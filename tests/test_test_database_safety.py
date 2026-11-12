def test_db_url_ignores_external_database_override(monkeypatch, request, tmp_path):
    """The destructive app fixture must always receive its own temporary SQLite DB."""
    monkeypatch.setenv("TEST_DATABASE_URL", "sqlite:////tmp/artha-demo-must-not-be-touched.sqlite3")
    url = request.getfixturevalue("db_url")
    assert url.startswith("sqlite:///")
    assert str(tmp_path) in url
    assert "artha-demo-must-not-be-touched.sqlite3" not in url
