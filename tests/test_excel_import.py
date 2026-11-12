from datetime import date, timedelta
from io import BytesIO

from openpyxl import Workbook

from app.extensions import db
from app.imports.expiry import purge_due_reviews
from app.models import Import, StagedTransaction, Transaction, utcnow


def workbook(names=("Expenses",), *, formula=False):
    book = Workbook()
    for index, name in enumerate(names):
        sheet = book.active if index == 0 else book.create_sheet()
        sheet.title = name
        sheet.append(["date", "description", "amount", "type", "category", "private note"])
        sheet.append([date(2026, 11, 1), "Milk", -12.34, "purchase", "Groceries", "discard me"])
        if formula:
            sheet.append([date(2026, 11, 2), "Total", "=SUM(C2:C2)"])
    stream = BytesIO()
    book.save(stream)
    return stream.getvalue()


def test_single_sheet_review_and_privacy(app, alice, tmp_path):
    app.config["STORAGE_PATH"] = str(tmp_path / "uploads")
    account = alice.account(alice.household())
    data = workbook()
    imp = alice.upload(account, data, filename="daily.xlsx").get_json()["import"]
    assert imp["parser_version"] == "xlsx-v1"
    row, = alice.rows(imp["id"])
    assert row["amount_minor"] == 1234 and row["direction"] == "debit"
    with app.app_context():
        assert StagedTransaction.query.one().raw_row == {}
        assert Transaction.query.count() == 0
    assert not any(tmp_path.joinpath("uploads").rglob("*"))
    assert alice.get(f"/imports/{imp['id']}/file").status_code == 404
    assert alice.post("/staged/approve", {"ids": [row["id"]]}).get_json()["results"][0]["ok"]
    assert alice.upload(account, data, filename="daily.xlsx").get_json()["already_imported"]


def test_web_sheet_choice_and_cleanup(app, alice):
    account = alice.account(alice.household())
    path = f"/accounts/{account}/imports"
    data = workbook(("November", "December"))
    def submit(name=None):
        fields = {"file": (BytesIO(data), "expenses.xlsx")}
        if name:
            fields["sheet"] = name
        return alice.client.post(path, data=fields, headers={"Accept": "application/json"})

    assert submit().get_json()["sheets"] == ["November", "December"]
    assert submit("Unknown").status_code == 400
    with app.app_context():
        assert Import.query.count() == 0
    first = submit("November").get_json()["review"]
    second = submit("December").get_json()["review"]
    assert first != second and first == submit("November").get_json()["review"]
    assert b"Milk" in alice.client.get(second).data
    alice.client.post(first + "/cancel")
    with app.app_context():
        active = Import.query.one()
        active.review_expires_at = utcnow() - timedelta(seconds=1)
        db.session.commit()
        purge_due_reviews()
        assert StagedTransaction.query.count() == Import.query.count() == Transaction.query.count() == 0


def test_invalid_workbook_stages_nothing(app, alice):
    account = alice.account(alice.household())
    for data in (b"broken zip", workbook(formula=True)):
        assert alice.upload(account, data, filename="invalid.xlsx").status_code == 400
    with app.app_context():
        assert StagedTransaction.query.count() == Transaction.query.count() == 0


def test_excel_debit_credit_layout_with_blank_trailing_cell(alice):
    account = alice.account(alice.household())
    book = Workbook()
    book.active.append(["date", "description", "debit", "credit"])
    book.active.append([date(2026, 11, 2), "Milk", 30])
    stream = BytesIO()
    book.save(stream)
    response = alice.upload(account, stream.getvalue(), filename="monthly.XLSX", layout="debit_credit")
    assert response.status_code == 201
    row, = alice.rows(response.get_json()["import"]["id"])
    assert row["amount_minor"] == 3000 and row["direction"] == "debit"
