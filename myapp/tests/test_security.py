import pytest
from jose import jwt

from myapp import security



def test_access_token_expire_minutes():
    assert security.access_token_expire_minutes() == 30


def test_confirm_token_expire_minutes():
    assert security.confirm_token_expire_minutes() == 30


def test_create_access_token():
    token = security.create_access_token("123")
    payload = jwt.decode(
        token,
        key=security.SECRET_KEY,
        algorithms=[security.ALGORITHM],
    )
    assert payload["sub"] == "123"
    assert payload["type"] == "access"


def test_create_confirmation_token():
    token = security.create_confirmation_token("123")
    payload = jwt.decode(
        token,
        key=security.SECRET_KEY,
        algorithms=[security.ALGORITHM],
    )
    assert payload["sub"] == "123"
    assert payload["type"] == "confirmation"


def test_password_hashes():
    password = "password"
    hashed = security.get_password_hash(password)
    assert security.verify_password(password, hashed)



def test_get_subject_for_token_type_valid_confirmation():
    email = "test@example.com"
    token = security.create_confirmation_token(email)

    assert (
        security.get_subject_for_token_type(token, "confirmation")
        == email
    )


def test_get_subject_for_token_type_valid_access():
    email = "test@example.com"
    token = security.create_access_token(email)

    assert (
        security.get_subject_for_token_type(token, "access")
        == email
    )


def test_get_subject_for_token_type_expired(mocker):
    mocker.patch(
        "myapp.security.access_token_expire_minutes",
        return_value=-1,
    )

    token = security.create_access_token("test@example.com")

    with pytest.raises(security.HTTPException) as exc_info:
        security.get_subject_for_token_type(token, "access")

    assert exc_info.value.detail == "Token has expired"


def test_get_subject_for_token_type_invalid_token():
    with pytest.raises(security.HTTPException) as exc_info:
        security.get_subject_for_token_type("invalid token", "access")

    assert exc_info.value.detail == "Invalid token"


def test_get_subject_for_token_type_missing_sub():
    token = security.create_access_token("test@example.com")

    payload = jwt.decode(
        token,
        key=security.SECRET_KEY,
        algorithms=[security.ALGORITHM],
    )
    payload.pop("sub")

    token = jwt.encode(
        payload,
        key=security.SECRET_KEY,
        algorithm=security.ALGORITHM,
    )

    with pytest.raises(security.HTTPException) as exc_info:
        security.get_subject_for_token_type(token, "access")

    assert exc_info.value.detail == "Token is missing 'sub' field"


def test_get_subject_for_token_type_wrong_type():
    token = security.create_confirmation_token("test@example.com")

    with pytest.raises(security.HTTPException) as exc_info:
        security.get_subject_for_token_type(token, "access")

    assert (
        exc_info.value.detail
        == "Token has incorrect type, expected 'access'"
    )



@pytest.mark.asyncio
async def test_get_user(registered_user: dict):
    user = await security.get_user(registered_user["email"])

    assert user is not None
    assert user.email == registered_user["email"]


@pytest.mark.asyncio
async def test_get_user_not_found():
    user = await security.get_user("missing@example.com")
    assert user is None


@pytest.mark.asyncio
async def test_authenticate_user(confirmed_user: dict):
    user = await security.authenticate_user(
        confirmed_user["email"],
        confirmed_user["password"],
    )

    assert user.email == confirmed_user["email"]


@pytest.mark.asyncio
async def test_authenticate_user_not_found():
    with pytest.raises(security.HTTPException):
        await security.authenticate_user("missing@example.com", "1234")


@pytest.mark.asyncio
async def test_authenticate_user_wrong_password(registered_user: dict):
    with pytest.raises(security.HTTPException):
        await security.authenticate_user(
            registered_user["email"],
            "wrong-password",
        )


@pytest.mark.asyncio
async def test_get_current_user(registered_user: dict):
    token = security.create_access_token(registered_user["email"])
    user = await security.get_current_user(token)

    assert user.email == registered_user["email"]


@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    with pytest.raises(security.HTTPException):
        await security.get_current_user("invalid token")


@pytest.mark.asyncio
async def test_get_current_user_wrong_token_type(registered_user: dict):
    token = security.create_confirmation_token(
        registered_user["email"]
    )

    with pytest.raises(security.HTTPException):
        await security.get_current_user(token)
