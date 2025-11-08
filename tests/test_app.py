from pathlib import Path
import importlib.util


# Load the application module from src/app.py so tests work regardless of package layout
src_app_path = Path(__file__).resolve().parents[1] / "src" / "app.py"
spec = importlib.util.spec_from_file_location("mergington_app", str(src_app_path))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

from fastapi.testclient import TestClient

app = mod.app
client = TestClient(app)


def test_get_activities():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    # ensure a known activity exists
    assert "Chess Club" in data


def test_signup_success_and_cleanup():
    email = "teststudent@example.com"
    # sign up for Chess Club
    resp = client.post("/activities/Chess Club/signup", params={"email": email})
    assert resp.status_code == 200
    body = resp.json()
    assert "Signed up" in body.get("message", "")
    # verify participant added to in-memory data
    assert email in mod.activities["Chess Club"]["participants"]
    # cleanup to keep tests idempotent
    mod.activities["Chess Club"]["participants"].remove(email)


def test_signup_duplicate_fails():
    # use an existing participant from the seeded data
    existing = mod.activities["Chess Club"]["participants"][0]
    resp = client.post("/activities/Chess Club/signup", params={"email": existing})
    assert resp.status_code == 400
    data = resp.json()
    assert data.get("detail") == "Student is already signed up"


def test_signup_activity_not_found():
    resp = client.post("/activities/NoSuchActivity/signup", params={"email": "a@b.com"})
    assert resp.status_code == 404
