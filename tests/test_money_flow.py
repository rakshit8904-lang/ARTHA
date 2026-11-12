from bs4 import BeautifulSoup
from tests.conftest import csv_text


def test_money_flow_follows_approved_classification(alice, bob):
    hid = alice.household()
    account = alice.account(hid, "Salary account")
    path = f"/households/{hid}/money-flow"
    assert path.encode() in alice.client.get(f"/households/{hid}").data
    imp = alice.upload(account, csv_text([
        "2026-11-01,Recognized debit,5000,debit,,",
        "2026-11-02,Market,100,debit,purchase,Groceries",
        "2026-11-03,Private pending,900,debit,purchase,Travel",
        "2026-11-04,Salary,7000,credit,income,",
    ])).get_json()["import"]["id"]
    unknown, grocery, pending, salary = alice.rows(imp)
    assert b"Approve a transaction" in alice.client.get(path).data
    assert b"Money flow" in alice.client.get(path).data
    deferred = alice.post("/staged/approve", {"ids": [unknown["id"]], "review_later": True})
    txn = deferred.get_json()["results"][0]["transaction_id"]
    alice.post("/staged/approve", {"ids": [grocery["id"], salary["id"]]})

    def links():
        page = alice.client.get(path)
        assert page.status_code == 200 and page.cache_control.no_store
        return {a.strong.text: a for a in BeautifulSoup(page.data, "html.parser").select("a.flow-edge")}

    edges = links()
    assert set(edges) == {"Awaiting classification", "Groceries", "Income"}
    assert "←" in edges["Income"].text
    old = edges["Awaiting classification"]["href"]
    details = alice.client.get(old)
    assert "₹5,000.00 across 1 approved transaction." in details.get_data(as_text=True)
    assert b"Recognized debit" in details.data and b"Private pending" not in details.data
    assert bob.client.get(old).status_code == 404
    assert alice.patch(f"/transactions/{txn}", {"transaction_type": "purchase", "category": "Groceries"}).status_code == 200
    assert alice.client.get(old).status_code == 404
    groceries = links()["Groceries"]
    assert groceries.b.text == "₹5,100.00"
    assert b"Market" in alice.client.get(groceries["href"]).data
    assert alice.patch(f"/transactions/{txn}", {"transaction_type": "internal_transfer", "category": ""}).status_code == 200
    edges = links()
    assert edges["Groceries"].b.text == "₹100.00"
    assert edges["Internal transfer · destination unknown"].b.text == "₹5,000.00"
    assert "Awaiting classification" not in edges


def test_connection_keeps_account_totals_and_pages_separate(alice):
    hid = alice.household()
    path = f"/households/{hid}/money-flow"
    for name, count in (("A", 26), ("B", 1)):
        acc = alice.account(hid, name)
        data = csv_text([f"2026-11-01,{name} expense {i},1,debit,purchase,Groceries" for i in range(count)])
        imp = alice.upload(acc, data).get_json()["import"]["id"]
        alice.post("/staged/approve", {"ids": [r["id"] for r in alice.rows(imp)]})
    edges = BeautifulSoup(alice.client.get(path).data, "html.parser").select("a.flow-edge")
    assert [edge.b.text for edge in edges] == ["₹26.00", "₹1.00"]
    first = BeautifulSoup(alice.client.get(edges[0]["href"]).data, "html.parser").select_one("#connection")
    second = BeautifulSoup(alice.client.get(first.find("a", string="More transactions")["href"]).data,
                           "html.parser").select_one("#connection")
    entries = [a.text for section in (first, second) for a in section.select("li a")]
    assert len(entries) == 26 and set(entries) == {f"A expense {i}" for i in range(26)}
