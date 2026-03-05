from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str
    role: Optional[str] = "user"

class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None

class UserResponse(UserBase):
    id: int
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class LoginRequest(BaseModel):
    username: str
    password: str

class AdvertisementBase(BaseModel):
    title: str
    description: str
    price: float

class AdvertisementCreate(AdvertisementBase):
    pass

class AdvertisementUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None

class AdvertisementResponse(AdvertisementBase):
    id: int
    owner_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
