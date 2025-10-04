from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from typing import List
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime, timedelta
from typing import Optional
import jwt
import httpx
from passlib.context import CryptContext
import os
from dotenv import load_dotenv
import random

# Load .env from parent directory (main folder)
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=env_path)

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./satellite_booking.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    google_id = Column(String, unique=True, nullable=True)
    profile_picture = Column(String, nullable=True)
    mobile_no = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_profile_complete = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Satellite(Base):
    __tablename__ = "satellites"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    designation = Column(String, nullable=False)
    orbit_altitude = Column(Float, nullable=False)  # in km
    resolution = Column(Float, nullable=False)  # in m/px
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    satellite_id = Column(Integer, ForeignKey("satellites.id"), nullable=False)
    object_name = Column(String, nullable=False)
    object_type = Column(String, nullable=False)
    booking_type = Column(String, nullable=False)  # photograph or track
    status = Column(String, default="pending")  # pending, completed, failed
    scheduled_time = Column(DateTime, nullable=True)
    duration = Column(Integer, nullable=True)  # in minutes
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    satellite = relationship("Satellite")

Base.metadata.create_all(bind=engine)

# Pydantic Models
class GoogleAuthRequest(BaseModel):
    token: str

class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    mobile_no: Optional[str] = None
    
    @validator('mobile_no')
    def validate_mobile(cls, v):
        if v and not v.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise ValueError('Invalid mobile number format')
        return v

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    mobile_no: Optional[str]
    profile_picture: Optional[str]
    is_profile_complete: bool
    
    model_config = {"from_attributes": True}

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class SatelliteResponse(BaseModel):
    id: int
    name: str
    designation: str
    orbit_altitude: float
    resolution: float
    is_active: bool
    
    model_config = {"from_attributes": True}

class BookingCreate(BaseModel):
    object_name: str
    object_type: str
    booking_type: str  # photograph or track
    satellite_id: int
    scheduled_time: Optional[datetime] = None
    duration: Optional[int] = None
    notes: Optional[str] = None
    
    @validator('booking_type')
    def validate_booking_type(cls, v):
        if v not in ['photograph', 'track']:
            raise ValueError('Booking type must be either "photograph" or "track"')
        return v

class BookingResponse(BaseModel):
    id: int
    object_name: str
    object_type: str
    booking_type: str
    status: str
    scheduled_time: Optional[datetime]
    duration: Optional[int]
    notes: Optional[str]
    created_at: datetime
    satellite: SatelliteResponse
    
    model_config = {"from_attributes": True}
# FastAPI app
app = FastAPI(title="Satellite Booking API")

# CORS configuration for Electron
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Electron app's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# JWT token functions
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(db: Session = Depends(get_db), token_data: dict = Depends(verify_token)):
    user = db.query(User).filter(User.id == token_data.get("user_id")).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def seed_satellites(db: Session):
    """Seed initial satellites if none exist"""
    if db.query(Satellite).count() == 0:
        satellites = [
            Satellite(name="AstroVision-1", designation="AV-001", orbit_altitude=550.0, resolution=0.5, is_active=True),
            Satellite(name="SkyWatch-2", designation="SW-002", orbit_altitude=620.0, resolution=0.4, is_active=True),
            Satellite(name="OrbitEye-3", designation="OE-003", orbit_altitude=680.0, resolution=0.3, is_active=True),
            Satellite(name="SpaceScan-4", designation="SS-004", orbit_altitude=590.0, resolution=0.45, is_active=True),
            Satellite(name="StarMapper-5", designation="SM-005", orbit_altitude=700.0, resolution=0.35, is_active=True),
            Satellite(name="CosmicLens-6", designation="CL-006", orbit_altitude=640.0, resolution=0.38, is_active=True),
            Satellite(name="NebulaSight-7", designation="NS-007", orbit_altitude=710.0, resolution=0.32, is_active=True),
            Satellite(name="GalaxyTrack-8", designation="GT-008", orbit_altitude=600.0, resolution=0.42, is_active=True),
            Satellite(name="PlanetScope-9", designation="PS-009", orbit_altitude=580.0, resolution=0.48, is_active=True),
            Satellite(name="DeepSpace-10", designation="DS-010", orbit_altitude=750.0, resolution=0.28, is_active=True),
            Satellite(name="CelestialEye-11", designation="CE-011", orbit_altitude=630.0, resolution=0.39, is_active=True),
            Satellite(name="StarSeeker-12", designation="SS-012", orbit_altitude=670.0, resolution=0.36, is_active=True),
            Satellite(name="AstroGuard-13", designation="AG-013", orbit_altitude=610.0, resolution=0.41, is_active=True),
            Satellite(name="CosmicWatch-14", designation="CW-014", orbit_altitude=690.0, resolution=0.34, is_active=True),
            Satellite(name="OrbitTracer-15", designation="OT-015", orbit_altitude=650.0, resolution=0.37, is_active=True),
            Satellite(name="SkyScanner-16", designation="SS-016", orbit_altitude=720.0, resolution=0.31, is_active=True),
            Satellite(name="SpaceVision-17", designation="SV-017", orbit_altitude=570.0, resolution=0.46, is_active=True),
            Satellite(name="AstroProbe-18", designation="AP-018", orbit_altitude=730.0, resolution=0.30, is_active=True),
            Satellite(name="StarGazer-19", designation="SG-019", orbit_altitude=660.0, resolution=0.33, is_active=True),
            Satellite(name="NebulaWatch-20", designation="NW-020", orbit_altitude=595.0, resolution=0.44, is_active=True),
            Satellite(name="GalaxyEye-21", designation="GE-021", orbit_altitude=740.0, resolution=0.29, is_active=True),
            Satellite(name="PlanetWatch-22", designation="PW-022", orbit_altitude=615.0, resolution=0.40, is_active=True),
            Satellite(name="CosmicScan-23", designation="CS-023", orbit_altitude=705.0, resolution=0.33, is_active=True),
            Satellite(name="OrbitVision-24", designation="OV-024", orbit_altitude=625.0, resolution=0.39, is_active=True),
            Satellite(name="SkyTracker-25", designation="ST-025", orbit_altitude=695.0, resolution=0.34, is_active=True),
            Satellite(name="SpaceLens-26", designation="SL-026", orbit_altitude=585.0, resolution=0.47, is_active=True),
            Satellite(name="AstroSight-27", designation="AS-027", orbit_altitude=715.0, resolution=0.31, is_active=True),
            Satellite(name="StarWatch-28", designation="SW-028", orbit_altitude=635.0, resolution=0.38, is_active=True),
            Satellite(name="NebulaScope-29", designation="NS-029", orbit_altitude=675.0, resolution=0.36, is_active=True),
            Satellite(name="GalaxyScope-30", designation="GS-030", orbit_altitude=605.0, resolution=0.43, is_active=True),
            Satellite(name="CelestialScan-31", designation="CS-031", orbit_altitude=725.0, resolution=0.30, is_active=True),
            Satellite(name="DeepWatch-32", designation="DW-032", orbit_altitude=645.0, resolution=0.37, is_active=True),
        ]
        db.add_all(satellites)
        db.commit()

# Routes
@app.get("/")
async def root():
    return {"message": "Satellite Booking API", "status": "running"}

@app.post("/auth/google", response_model=TokenResponse)
async def google_auth(auth_request: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Authenticate user with Google OAuth token"""
    try:
        # Verify Google token
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://www.googleapis.com/oauth2/v3/tokeninfo?access_token={auth_request.token}"
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid Google token")
            
            google_data = response.json()
            
            # Get user info
            user_info_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {auth_request.token}"}
            )
            user_info = user_info_response.json()
        
        email = user_info.get("email")
        google_id = user_info.get("id")
        
        # Check if user exists
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            # Create new user
            user = User(
                email=email,
                google_id=google_id,
                full_name=user_info.get("name"),
                profile_picture=user_info.get("picture"),
                is_profile_complete=False
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Create access token
        access_token = create_access_token({"user_id": user.id, "email": user.email})
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.model_validate(user)
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse.model_validate(current_user)

@app.put("/user/profile", response_model=UserResponse)
async def update_profile(
    profile_data: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    if profile_data.full_name:
        current_user.full_name = profile_data.full_name
    if profile_data.mobile_no:
        current_user.mobile_no = profile_data.mobile_no
    
    # Check if profile is complete
    if current_user.full_name and current_user.mobile_no:
        current_user.is_profile_complete = True
    
    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    
    return UserResponse.model_validate(current_user)


@app.get("/satellites/nearest", response_model=List[SatelliteResponse])
async def get_nearest_satellites(
    limit: int = 3,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get random available satellites"""
    # Seed satellites if database is empty
    seed_satellites(db)
    
    # Get all active satellites
    all_satellites = db.query(Satellite).filter(
        Satellite.is_active == True
    ).all()
    
    # Randomly select satellites
    selected_satellites = random.sample(all_satellites, min(limit, len(all_satellites)))
    
    return [SatelliteResponse.model_validate(sat) for sat in selected_satellites]

@app.post("/bookings", response_model=BookingResponse)
async def create_booking(
    booking_data: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new booking"""
    # Verify satellite exists and is active
    satellite = db.query(Satellite).filter(
        Satellite.id == booking_data.satellite_id,
        Satellite.is_active == True
    ).first()
    
    if not satellite:
        raise HTTPException(status_code=404, detail="Satellite not found or not active")
    
    # Create booking
    booking = Booking(
        user_id=current_user.id,
        satellite_id=booking_data.satellite_id,
        object_name=booking_data.object_name,
        object_type=booking_data.object_type,
        booking_type=booking_data.booking_type,
        scheduled_time=booking_data.scheduled_time,
        duration=booking_data.duration,
        notes=booking_data.notes,
        status="pending"
    )
    
    db.add(booking)
    db.commit()
    db.refresh(booking)
    
    return BookingResponse.model_validate(booking)

@app.get("/bookings", response_model=List[BookingResponse])
async def get_user_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all bookings for the current user"""
    bookings = db.query(Booking).filter(
        Booking.user_id == current_user.id
    ).order_by(Booking.created_at.desc()).all()
    
    return [BookingResponse.model_validate(booking) for booking in bookings]

@app.get("/bookings/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific booking"""
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.user_id == current_user.id
    ).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    return BookingResponse.model_validate(booking)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)