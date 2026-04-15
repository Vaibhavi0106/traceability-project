def login(username, password):
    return username == "admin" and password == "1234"


def get_profile(user):
    return {"name": "Vaishnavi", "email": "vai@example.com"}


def reset_password(email):
    return "@" in email


# TRACE: US-001
def test_login_success():
    assert login("admin", "1234") is True


# TRACE: US-002
def test_view_profile():
    profile = get_profile("admin")
    assert profile["name"] == "Vaishnavi"


# TRACE: US-003
def test_reset_password():
    assert reset_password("wrongemail") is True