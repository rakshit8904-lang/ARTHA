from bs4 import BeautifulSoup
from app.extensions import db
from app.models import PortfolioHolding, Transaction
from tests.test_authorization import add_member


def form(**changes):
    return dict(asset_name='Example fund',asset_type='mutual_fund',quantity='12.5',
        invested_minor='1000',current_value_minor='1100',as_of_date='2026-11-09',notes='Manual valuation') | changes


def test_portfolio_save_edit_stale_and_ledger_isolation(app,alice):
    hid=alice.household(); path=f'/households/{hid}/portfolio'
    assert alice.client.post(path,data=form()).status_code==302
    with app.app_context():
        item=PortfolioHolding.query.one(); ident=item.id
        assert item.invested_minor==100000 and item.current_value_minor==110000
    detail=path+'/'+ident
    html=BeautifulSoup(alice.client.get(detail).data,'html.parser')
    version=html.select_one('[name=version]')['value']
    assert alice.client.post(detail,data=form(version=version,current_value_minor='900')).status_code==302
    assert alice.client.post(detail,data=form(version=version,current_value_minor='2000')).status_code==409
    page=alice.client.get(path).get_data(as_text=True)
    assert '-₹100.00' in page and '-10.00%' in page
    alice.post('/auth/logout');alice.post('/auth/login',{'email':'alice@example.com','password':'correct-horse-1'})
    assert 'Example fund' in alice.client.get(path).get_data(as_text=True)
    with app.app_context():
        assert PortfolioHolding.query.one().current_value_minor==90000
        assert Transaction.query.count()==0


def test_portfolio_permissions_and_csrf(app,alice,bob):
    hid=alice.household();path=f'/households/{hid}/portfolio'
    alice.client.post(path,data=form())
    with app.app_context():ident=PortfolioHolding.query.one().id
    detail=path+'/'+ident
    assert bob.client.get(path).status_code==404
    assert bob.client.post(detail,data=form()).status_code==404
    other=bob.household()
    assert bob.client.get(detail.replace(hid,other)).status_code==404
    add_member(app,hid,bob.user['id'],'viewer')
    page=bob.client.get(path)
    assert page.status_code==200 and b'id="portfolio-form"' not in page.data
    assert bob.client.post(path,data=form()).status_code==403
    assert bob.client.post(detail,data=form()).status_code==403
    app.config['CSRF_ENABLED']=True
    assert alice.client.post(path,data=form()).status_code==400


def test_portfolio_validation_zero_investment_and_escaping(app,alice):
    path=f'/households/{alice.household()}/portfolio'
    for data in [form(quantity='0'),form(quantity='0.000000001'),form(invested_minor='-1'),
                 form(current_value_minor='1.001'),form(as_of_date='bad'),form(asset_type='unsupported')]:
        assert alice.client.post(path,data=data).status_code==400
    with app.app_context():assert PortfolioHolding.query.count()==0
    assert alice.client.post(path,data=form(asset_name='<script>alert(1)</script>',notes='<b>Text</b>',invested_minor='0')).status_code==302
    page=alice.client.get(path).get_data(as_text=True)
    assert 'not defined with zero invested amount' in page
    assert '&lt;script&gt;' in page and '<script>alert(1)</script>' not in page
