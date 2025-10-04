from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
import google.auth.transport.requests
import google.oauth2.id_token
from jose import JWTError, jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import get_db, User
from database import Base, engine

Base.metadata.create_all(bind=engine)

auth_router = APIRouter()

GOOGLE_CLIENT_ID = "137294851791-v9vt65kusi2j5l8punsss214smbs0it7.apps.googleusercontent.com"

# Secret key for JWT encoding/decoding.  Ideally, this should be read from an environment variable.
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """
    Creates a JWT access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@auth_router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Login endpoint (Google Authentication).
    """
    try:
        # Verify the Google token
        idinfo = google.oauth2.id_token.verify_oauth2_token(
            form_data.username,  # The token is passed as the username
            google.auth.transport.requests.Request(),
            GOOGLE_CLIENT_ID
        )

        # Check if the token is valid for your client ID
        if idinfo['aud'] != GOOGLE_CLIENT_ID:
            raise HTTPException(status_code=400, detail="Invalid audience")

        # Get the user ID from the token
        user_id = idinfo['sub']
        email = idinfo['email']
        name = idinfo['name']
        picture = idinfo['picture']

        # Check if the user exists in your database
        user = db.query(User).filter(User.google_id == user_id).first()

        if user is None:
            # If the user doesn't exist, create a new user
            new_user = User(google_id=user_id, email=email, name=name, profile_picture=picture)
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            user = new_user

        # Create access token
        access_token_data = {"sub": user_id}
        access_token = create_access_token(access_token_data)
        return {"access_token": access_token, "token_type": "bearer"}

    except ValueError:
        # Invalid token
        raise HTTPException(status_code=400, detail="Invalid Google token")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@auth_router.post("/signup")
async def signup(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Signup endpoint (Google Authentication).
    """
    try:
        # Verify the Google token
        idinfo = google.oauth2.id_token.verify_oauth2_token(
            form_data.username,  # The token is passed as the username
            google.auth.transport.requests.Request(),
            GOOGLE_CLIENT_ID
        )

        # Check if the token is valid for your client ID
        if idinfo['aud'] != GOOGLE_CLIENT_ID:
            raise HTTPException(status_code=400, detail="Invalid audience")

        # Get the user ID from the token
        user_id = idinfo['sub']
        email = idinfo['email']
        name = idinfo['name']
        picture = idinfo['picture']

        # Check if the user exists in your database
        user = db.query(User).filter(User.google_id == user_id).first()
        if user:
             raise HTTPException(status_code=400, detail="User already registered")

        # Create a new user in the database
        new_user = User(google_id=user_id, email=email, name=name, profile_picture=picture)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Create access token
        access_token_data = {"sub": user_id}
        access_token = create_access_token(access_token_data)
        return {"access_token": access_token, "token_type": "bearer"}

    except ValueError:
        # Invalid token
        raise HTTPException(status_code=400, detail="Invalid Google token")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
