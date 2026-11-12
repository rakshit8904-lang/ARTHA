from bs4 import BeautifulSoup

from app.cities.affordability import search_cities
from app.extensions import db
from app.models import MonthlyPlan, RelocationScenario, Transaction
from tests.test_authorization import add_member
from tests.test_planning_tools import _plan


def fields(**changes):
    return dict(city=search_cities('pune')[0]['city_key'], name='Pune move', revision='0',
                monthly_income_minor='30000', rent_minor='10000', utilities_minor='2000',
                food_minor='5000', transport_minor='1000', other_minor='2000', deposit_months='2',
                moving_cost_minor='1500', setup_cost_minor='500', action='save') | changes


def test_save_reopen_edit_and_stale_revision(app, alice):
    hid = alice.household()
    path = f'/households/{hid}/relocation'
    created = alice.client.post(path, data=fields())
    assert created.status_code == 302
    detail = created.headers['Location']
    page = alice.client.get(detail)
    assert page.status_code == 200
    html = page.get_data(as_text=True)
    assert '₹20,000.00' in html and '₹22,000.00' in html and '₹10,000.00' in html
    alice.post('/auth/logout')
    alice.post('/auth/login', {'email':'alice@example.com','password':'correct-horse-1'})
    assert 'Pune move' in alice.client.get(detail).get_data(as_text=True)
    assert alice.client.post(detail, data=fields(revision='1', name='Updated move')).status_code == 302
    assert alice.client.post(detail, data=fields(revision='1', name='Stale move')).status_code == 409
    with app.app_context():
        row = RelocationScenario.query.one()
        assert row.name == 'Updated move' and row.revision == 2
        assert row.inputs['rent_minor'] == 1000000


def test_city_prefill_reset_and_calculate_never_change_budget_or_saved_scenario(app, alice):
    hid = alice.household()
    _plan(alice, hid)
    city = search_cities('pune')[0]
    path = f'/households/{hid}/relocation'
    with app.app_context():
        plan = db.session.get(MonthlyPlan, (hid,'2026-11'))
        before = (plan.revision,dict(plan.limits),plan.income,Transaction.query.count())
    initial = BeautifulSoup(alice.client.get(path+'?city='+city['city_key']).data,'html.parser')
    expected = f"{city['rent_paise']//100}.{city['rent_paise']%100:02d}"
    assert initial.select_one('#rent_minor')['value'] == expected
    assert initial.select_one('#monthly_income_minor')['value'] == ''
    detail = alice.client.post(path,data=fields()).headers['Location']
    reset = BeautifulSoup(alice.client.get(detail+'?reset=1').data,'html.parser')
    assert reset.select_one('#rent_minor')['value'] == expected
    assert reset.select_one('#deposit_months')['value'] == ''
    assert not reset.select_one('#relocation-results')
    assert alice.client.post(detail,data=fields(action='calculate',rent_minor='40000')).status_code == 200
    with app.app_context():
        assert RelocationScenario.query.one().inputs['rent_minor'] == 1000000
        plan = db.session.get(MonthlyPlan,(hid,'2026-11'))
        assert (plan.revision,dict(plan.limits),plan.income,Transaction.query.count()) == before


def test_relocation_household_isolation_viewer_and_csrf(app, alice, bob):
    hid = alice.household()
    other = bob.household()
    path = f'/households/{hid}/relocation'
    detail = alice.client.post(path,data=fields()).headers['Location']
    assert bob.client.get(detail).status_code == 404
    assert bob.client.post(path,data=fields()).status_code == 404
    assert bob.client.get(detail.replace(hid,other)).status_code == 404
    add_member(app,hid,bob.user['id'],'viewer')
    assert bob.client.get(detail).status_code == 200
    assert bob.client.post(detail,data=fields(action='calculate')).status_code == 200
    assert bob.client.post(detail,data=fields(revision='1')).status_code == 403
    app.config['CSRF_ENABLED'] = True
    rejected = alice.client.post(detail,data=fields(revision='1'))
    assert rejected.status_code == 400 and b"CSRF" in rejected.data


def test_relocation_rejects_missing_invalid_and_unknown_city_inputs(app, alice):
    path = f'/households/{alice.household()}/relocation'
    for changes in [dict(city='unknown'),dict(name=''),dict(food_minor=''),dict(food_minor='-1'),
                    dict(food_minor='1.001'),dict(deposit_months='1.5'),dict(deposit_months='25'),
                    dict(action='delete'),dict(monthly_income_minor='NaN')]:
        assert alice.client.post(path,data=fields(**changes)).status_code == 400, changes
    with app.app_context():
        assert RelocationScenario.query.count() == 0


def test_relocation_zero_income_and_break_even_are_explained(alice):
    path = f'/households/{alice.household()}/relocation'
    page = alice.client.post(path,data=fields(action='calculate',monthly_income_minor='0'))
    assert page.status_code == 200
    assert 'Monthly shortfall' in page.get_data(as_text=True)
    assert 'not defined with zero income' in page.get_data(as_text=True)
    page = alice.client.post(path,data=fields(action='calculate',monthly_income_minor='20000'))
    assert 'no remaining buffer' in page.get_data(as_text=True)
