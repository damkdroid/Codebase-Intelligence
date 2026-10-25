
from sample_project.auth import hash_password, verify_password, generate_jwt_token, verify_jwt_token


def test_password_hashing_and_verification():
    plain = "SuperSecurePassword123!"
    hashed = hash_password(plain)
    assert "$" in hashed
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_token_generation_and_validation():
    token = generate_jwt_token(user_id=42, username="testuser", role="admin")
    assert token is not None
    info = verify_jwt_token(token)
    assert info is not None
    assert info["user_id"] == 42
    assert info["username"] == "testuser"
    assert info["role"] == "admin"
