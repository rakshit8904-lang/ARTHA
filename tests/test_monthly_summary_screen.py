from bs4 import BeautifulSoup
from app.integrations import finance
from app.integrations.ledger_finance import monthly_summary
from tests.test_ledger_aggregation import _import, _approve
from tests.test_authorization import add_member


def test_summary_details_follow_ledger_semantics_and_permissions(app,alice,bob):
    finance.register_service(monthly_summary)
    hid=alice.household();acc=alice.account(hid)
    imp,rows=_import(alice,acc,['2026-10-01,Original purchase,100,debit,purchase,Groceries'])
    _approve(alice,imp,list(rows.values()))
    original=alice.get(f'/households/{hid}/transactions').get_json()['transactions'][0]['id']
    imp,rows=_import(alice,acc,[
        '2026-11-01,Salary,1000,credit,income,',
        '2026-11-02,Refund,30,credit,refund,',
        '2026-11-03,Unmatched refund,7,credit,refund,',
        '2026-11-04,Transfer out,200,debit,internal_transfer,',
        '2026-11-04,Transfer in,200,credit,internal_transfer,',
        '2026-11-05,EMI,100,debit,loan_payment,'])
    alice.patch('/staged/'+rows['Refund'],{'matched_transaction_id':original})
    _approve(alice,imp,list(rows.values()))
    imp,rows=_import(alice,acc,['2026-11-06,Unknown debit,9,debit,,','2026-11-07,Unknown credit,3,credit,,'])
    _approve(alice,imp,list(rows.values()),review_later=True)
    _import(alice,acc,['2026-11-08,Pending shop,999,debit,purchase,Shopping & Clothing'])
    path=f'/households/{hid}/summary?month=2026-11'
    response=alice.client.get(path);assert response.status_code==200
    html=BeautifulSoup(response.data,'html.parser')
    assert '-₹30.00' in html.select_one('#summary-categories').get_text()
    assert '₹1,030.00' in html.select_one('#summary-overview').get_text()
    assert '₹9.00' in html.select_one('#summary-unresolved').get_text()
    assert '₹3.00' in html.select_one('#summary-unresolved').get_text()
    excluded=html.select_one('#summary-excluded').get_text()
    assert '₹400.00' in excluded and '₹7.00' in excluded and '₹100.00' in excluded
    assert '₹999.00' not in html.get_text()
    api=alice.get(path).get_json()
    assert api['excluded_movements']['unmatched_refunds_minor']==700
    assert api['expense_minor']==-3000 and api['transaction_count']==8
    assert bob.client.get(path).status_code==404
    add_member(app,hid,bob.user['id'],'viewer')
    assert bob.client.get(path).status_code==200
    for link in html.select('#summary-overview a, #summary-unresolved a, #summary-excluded a'):
        assert alice.client.get(link['href']).status_code==200


def test_summary_empty_and_invalid_month_do_not_invent_totals(alice):
    finance.register_service(monthly_summary)
    path=f'/households/{alice.household()}/summary'
    html=BeautifulSoup(alice.client.get(path+'?month=2026-11').data,'html.parser')
    assert 'Income, spending and surplus are unknown' in html.select_one('#summary-overview').get_text()
    assert not html.select_one('#summary-categories')
    assert '₹0.00' not in html.get_text()
    assert alice.client.get(path).status_code==200
    bad=alice.client.get(path+'?month=2026-13')
    assert b'Choose a month' in bad.data or b'Month must' in bad.data
