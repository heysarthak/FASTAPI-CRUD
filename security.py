import logging
import bcrypt
import datetime
from database import user_table, database
from fastapi import HTTPException, status
from jose import jwt, JWTError, ExpiredSignatureError
from typing import Literal
import hashlib

logger = logging.getLogger(__name__)



SECRET_KEY = "9b73f2a1bdd7ae163444473d29a6885ffa22ab26117068f72a5a56a74d12d1fc"
ALGORITHM = "HS256"

def create_credentials_exception(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )

def get_password_hash(password: str) -> str:
    # 1. Pre-hash with SHA-256 (gives a 64-character hex string)
    # We encode it to bytes because bcrypt operates on bytes
    password_pre_hash = hashlib.sha256(password.encode("utf-8")).hexdigest().encode("utf-8")
    
    # 2. Generate a salt and hash
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_pre_hash, salt)
    
    # 3. Return as a string to store in the DB
    return hashed_password.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # 1. Pre-hash the incoming password exactly the same way
    password_pre_hash = hashlib.sha256(plain_password.encode("utf-8")).hexdigest().encode("utf-8")
    
    # 2. Check the password against the stored hash
    # .encode("utf-8") converts the stored string back to bytes for comparison
    return bcrypt.checkpw(password_pre_hash, hashed_password.encode("utf-8"))

def access_toekn_expire_minutes() -> int:
    return 30

def confirm_toekn_expire_minutes() -> int:
    return 30

def create_access_token(email) -> str:
    logger.debug("Creating access token", extra={"email":email})
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=access_toekn_expire_minutes())
    jwt_data = {"sub": email , "exp":expire, "type":"access"}
    encoded_jwt= jwt.encode(jwt_data, key=SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_confirmation_token(email) -> str:
    logger.debug("Creating access token", extra={"email":email})
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=confirm_toekn_expire_minutes())
    jwt_data = {"sub": email , "exp":expire, "type":"confirmation"}
    encoded_jwt= jwt.encode(jwt_data, key=SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_user(email: str):
    logger.debug("Fetching user email from database", extra={"email": email})
    query = user_table.select().where(user_table.c.email == email)
    result = await database.fetch_one(query)
    if result:
        return result

async def authenticate_user(email: str, password: str):
    user = await get_user(email)
    if not user or not verify_password(password, user.password):
        raise create_credentials_exception("Invalid email or password")
    if not user.confirmed:
        raise create_credentials_exception("User has not confirmed email")
    return user


def get_subject_for_token_type(
    token: str, type: Literal["access", "confirmation"]
) -> str:
    try:
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError as e:
        raise create_credentials_exception("Token has expired") from e
    except JWTError as e:
        raise create_credentials_exception("Invalid token") from e

    email = payload.get("sub")
    if email is None:
        raise create_credentials_exception("Token is missing 'sub' field")

    token_type = payload.get("type")
    if token_type is None or token_type != type:
        raise create_credentials_exception(
            f"Token has incorrect type, expected '{type}'"
        )

    return email