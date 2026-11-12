from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import pytest

from app.errors import Conflict
from app.ledger.transfers import decide_transfer
from app.models import TransferDecision
from tests.conftest import csv_text


@pytest.mark.parametrize("choice", ["confirmed", "dismissed", "unsure"])
def test_owner_decides_single_transfer_without_double_counting(alice, bob, choice):
    hid = alice.household()
    source, destination = alice.account(hid, "Salary"), alice.account(hid, "Savings")
    path = f"/households/{hid}/money-flow"

    def approve(account, lines):
        imp = alice.upload(account, csv_text(lines)).get_json()["import"]["id"]
        result = alice.post("/staged/approve", {"ids": [r["id"] for r in alice.rows(imp)]})
        return [r["transaction_id"] for r in result.get_json()["results"]]

    debit, = approve(source, ["2026-11-01,Outgoing entry,5000,debit,purchase,Groceries"])
    credit, other, _, _ = approve(destination, [
        "2026-11-01,Incoming entry,5000,credit,income,",
        "2026-11-01,Second possible credit,5000,credit,income,",
        "2026-11-02,Wrong date,5000,credit,income,",
        "2026-11-01,Wrong amount,400,credit,income,"])
    params = dict(debit_id=debit, credit_id=credit, choice=choice)
    def page():
        return BeautifulSoup(alice.client.get(path).data, "html.parser")
    def proposals():
        return [x["value"] for x in page().select("input[name=credit_id]")]
    assert set(proposals()) == {credit, other}
    assert bob.client.post(path + "/transfer", data=params).status_code == 404
    assert alice.client.post(path + "/transfer", data=params).status_code == 302
    assert alice.client.post(path + "/transfer", data=params).status_code == 302
    def record(tid):
        return alice.get("/transactions/"+tid).get_json()["transaction"]["transaction_type"]
    if choice == "confirmed":
        assert not proposals()
        detail, = page().select("details")
        assert "Salary → Savings" in detail.summary.text and "₹5,000.00" in detail.summary.text
        assert {a["href"] for a in detail.select("a")} == {"/transactions/"+debit, "/transactions/"+credit}
        assert record(debit) == record(credit) == "internal_transfer"
        assert alice.client.post(path + "/transfer", data=dict(params, credit_id=other)).status_code == 409
        assert "₹0.00" in alice.client.get(f"/households/{hid}/spend").get_data(as_text=True)
        alice.patch("/transactions/"+debit, {"transaction_type":"purchase", "category":"Groceries"})
        assert not page().select("details") and credit not in proposals()
    else:
        assert record(debit) == "purchase" and record(credit) == "income"
        assert (credit in proposals()) == (choice == "unsure")
        assert "₹5,000.00" in alice.client.get(f"/households/{hid}/spend").get_data(as_text=True)


def test_two_simultaneous_confirmations_share_only_one_debit(app, alice):
    hid = alice.household()
    txns = []
    for name, signed, kind in (("A", "debit", "purchase"), ("B", "credit", "income"), ("C", "credit", "income")):
        account = alice.account(hid, name)
        category = "Groceries" if signed == "debit" else ""
        data = csv_text([f"2026-11-01,Transfer candidate,5000,{signed},{kind},{category}"])
        imp = alice.upload(account, data).get_json()["import"]["id"]
        result = alice.post("/staged/approve", {"ids": [alice.rows(imp)[0]["id"]]})
        txns.append(result.get_json()["results"][0]["transaction_id"])
    barrier = Barrier(2)
    def confirm(credit):
        with app.app_context():
            barrier.wait(timeout=10)
            try:
                decide_transfer(alice.user["id"], hid, txns[0], credit, "confirmed")
                return True
            except Conflict:
                return False
    with ThreadPoolExecutor(max_workers=2) as workers:
        assert sorted(workers.map(confirm, txns[1:])) == [False, True]
    with app.app_context():
        assert TransferDecision.query.filter_by(decision="confirmed").count() == 1
