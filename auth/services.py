from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from auth.responses import TokenResponse
from core.config import get_settings
from core.database import SessionLocal, get_db
from core.security import get_token_payload, verify_password, create_access_token, create_refresh_token
from users.models import UserModel
from datetime import timedelta, datetime
from sqlalchemy.orm import Session

settings = get_settings()

def get_token(data: OAuth2PasswordRequestForm = Depends(), db: SessionLocal = Depends(get_db)):
	user = db.query(UserModel).filter(UserModel.email == data.username).first()

	if not user:
		raise HTTPException(
			status=status.HTTP_400_BAD_REQUEST, 
			detail="User not found",
			headers={"WWW-Authenticate": "Bearer"}
			)
	
	if not verify_password(plain_password=data.password, hashed_password=user.hashed_password):
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Invalid login credentials",
			headers={"WWW-Authenticate": "Bearer"}
		)
	
	_verify_user_access(user=user)

	return _get_user_token(user=user)
	

def _verify_user_access(user: UserModel):
	if not user.is_active:
		raise HTTPException(
			status=status.HTTP_400_BAD_REQUEST, 
			detail="Your account is inactive. Please contact support.",
			headers={"WWW-Authenticate": "Bearer"}
			)
	
	# I want to let unverified accounts have some access
	# if not user.is_verified:
	# 	Trigger user account verification email
	# 	raise HTTPException(
	# 		status=status.HTTP_400_BAD_REQUEST, 
	# 		detail="Your account is not verified. We have resent the account verification email.",
	# 		headers={"WWW-Authenticate": "Bearer"}
	# 		)
	
	
def _get_user_token(user: UserModel, refresh_token: str = None):
	payload = {"id": user.id }

	access_token_expiry = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

	access_token = create_access_token(data=payload, expiry=access_token_expiry)
	if not refresh_token:
		refresh_token = create_refresh_token(data=payload)

	return TokenResponse(
		access_token=access_token,
		refresh_token=refresh_token,
		expires_in=access_token_expiry.seconds
	)


def get_refresh_token(token: str, db: Session = Depends(get_db)):
	payload = get_token_payload(token=token)
	user_id = payload.get("id", None)
	if not user_id:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Invalid refresh token",
			headers={"WWW-Authenticate": "Bearer"}
		)
	
	user = db.query(UserModel).filter(UserModel.id == user_id).first()
	if not user:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Invalid refresh token",
			headers={"WWW-Authenticate": "Bearer"}
		)
	return _get_user_token(user=user, refresh_token=token)


	
	