import io
import pytest

from app import create_app
from app.extensions import db
from app.integrations import finance
from app.security.rate_limiter import limiter


@pytest.fixture()
def db_url(tmp_path):
    """Return a per-test temporary database; never honor an external DB override.

    The app fixture drops and recreates every table. Allowing TEST_DATABASE_URL
    here could therefore erase a developer's demo or otherwise valuable database.
    Tests that need another backend must use a separately managed disposable
    database fixture with an explicit safety check, not this shared fixture.
    """
    return "sqlite:///" + str(tmp_path / "test.sqlite3")


@pytest.fixture()
def app(db_url):
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": db_url,
                              "CSRF_ENABLED": False, "SECRET_KEY": "test-secret"})
    with application.app_context():
        db.drop_all()
        db.create_all()
    finance.clear_service()
    limiter.clear()
    yield application
    with application.app_context():
        db.session.remove()
        db.drop_all()
    finance.clear_service()


@pytest.fixture()
def client(app):
    return app.test_client()


def make_client(app):
    return app.test_client()


class Api:
    """Small helper around the JSON API for one signed-in user."""

    def __init__(self, app, email="a@example.com", name="Alice"):
        self.app = app
        self.client = app.test_client()
        r = self.client.post("/api/v1/auth/register",
                             json={"email": email, "display_name": name, "password": "correct-horse-1"})
        assert r.status_code == 201, r.get_json()
        self.user = r.get_json()["user"]

    def get(self, url, **kw):
        return self.client.get("/api/v1" + url, **kw)

    def post(self, url, json=None, **kw):
        return self.client.post("/api/v1" + url, json=json, **kw)

    def patch(self, url, json=None):
        return self.client.patch("/api/v1" + url, json=json)

    def household(self, name="Home"):
        r = self.post("/households", {"name": name})
        assert r.status_code == 201, r.get_json()
        return r.get_json()["household"]["id"]

    def account(self, household_id, name="Savings", kind="savings"):
        r = self.post("/households/%s/accounts" % household_id,
                      {"account_name": name, "account_type": kind, "institution_name": "Test Bank"})
        assert r.status_code == 201, r.get_json()
        return r.get_json()["account"]["id"]

    def upload(self, account_id, text, filename="stmt.csv", layout="signed_amount"):
        data = text if isinstance(text, bytes) else text.encode("utf-8")
        return self.post("/accounts/%s/imports" % account_id,
                         data={"file": (io.BytesIO(data), filename), "layout": layout},
                         content_type="multipart/form-data")

    def rows(self, import_id, status=None):
        url = "/imports/%s/rows" % import_id + ("?status=" + status if status else "")
        return self.get(url).get_json()["rows"]


def csv_text(rows, header="date,description,amount,direction,type,category"):
    return header + "\n" + "\n".join(rows) + "\n"


@pytest.fixture()
def alice(app):
    return Api(app, "alice@example.com", "Alice")


@pytest.fixture()
def bob(app):
    return Api(app, "bob@example.com", "Bob")
