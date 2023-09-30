from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def get_password_hash(password: str):
	return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
	return pwd_context.verify(plain_password, hashed_password)