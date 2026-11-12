from io import BytesIO

import pytest
from openpyxl import Workbook

from tests.conftest import csv_text


@pytest.mark.parametrize("extension", ["csv", "xlsx"])
def test_model_suggestions_require_user_choice(alice, extension):
    account = alice.account(alice.household())
    records = ["2026-11-01,Zepto,100,debit,purchase,", "2026-11-02,Uber,60,debit,purchase,",
               "2026-11-03,Zepto,90,debit,purchase,", "2026-11-04,Zepto,100,debit,internal_transfer,",
               "2026-11-05,Uber,100,debit,purchase,Travel", "2026-11-06,qqzzqx,1,debit,purchase,"]
    data = csv_text(records)
    if extension == "xlsx":
        book = Workbook()
        for line in data.splitlines():
            book.active.append(line.split(","))
        stream = BytesIO()
        book.save(stream)
        data = stream.getvalue()
    imp = alice.upload(account, data, filename="fictional." + extension).get_json()["import"]["id"]
    accept, change, defer, transfer, supplied, unknown = alice.rows(imp)
    assert accept["category"] is None and accept["suggested_category"] == "Groceries"
    assert change["suggested_category"] == "Transportation & Gas"
    assert all(row["suggested_category"] is None for row in (transfer, supplied, unknown))
    assert supplied["category"] == "Travel"
    assert b"Suggested: Groceries" in alice.client.get(f"/imports/{imp}").data
    assert not alice.post("/staged/approve", {"ids": [accept["id"]]}).get_json()["results"][0]["ok"]
    for row, category in ((accept, "Groceries"), (change, "Travel")):
        path = f"/staged/{row['id']}/edit"
        assert alice.client.post(path, data={"category": category}).status_code == 302
        result, = alice.post("/staged/approve", {"ids": [row["id"]]}).get_json()["results"]
        saved = alice.get("/transactions/" + result["transaction_id"]).get_json()["transaction"]
        assert saved["category"] == category
    edited = alice.patch("/staged/" + defer["id"], {"description": "Uber"}).get_json()["row"]
    assert edited["category"] is None and edited["suggested_category"] == "Transportation & Gas"
    result, = alice.post("/staged/approve", {"ids": [defer["id"]], "review_later": True}).get_json()["results"]
    saved = alice.get("/transactions/" + result["transaction_id"]).get_json()["transaction"]
    assert saved["category"] is None and saved["transaction_type"] is None
