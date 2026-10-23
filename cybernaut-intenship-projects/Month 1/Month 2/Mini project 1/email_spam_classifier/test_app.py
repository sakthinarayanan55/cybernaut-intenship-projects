from app import app

def test_endpoints():
    c = app.test_client()
    assert c.get("/").status_code == 200
    assert c.get("/health").status_code == 200
    r = c.post("/predict", json={"text": "WINNER!! Claim your free £900 prize now, call 09061701461"}).get_json()
    assert r["label"] == "spam"
    r = c.post("/predict", json={"text": "Are we still on for lunch tomorrow?"}).get_json()
    assert r["label"] == "ham"
    assert c.post("/predict", json={"text": ""}).status_code == 400
    print("All tests passed")

if __name__ == "__main__":
    test_endpoints()
