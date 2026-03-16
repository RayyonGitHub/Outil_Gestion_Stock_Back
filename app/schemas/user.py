from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    identifiant: str
    role: str
    actif: bool


class UserResponse(UserBase):
    id_utilisateur: int
    date_creation: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    role: Optional[str] = None
    actif: Optional[bool] = None