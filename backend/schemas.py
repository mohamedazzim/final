from pydantic import BaseModel, EmailStr
from datetime import date, time, datetime
from typing import Optional, List
from models import UserRole, ScraperStatus


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserPublicResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserAdminResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdateRole(BaseModel):
    role: UserRole


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class CauseBase(BaseModel):
    sr_no: Optional[str] = None
    court_no: Optional[str] = None
    case_no: Optional[str] = None
    petitioner: Optional[str] = None
    respondent: Optional[str] = None
    advocate: Optional[str] = None
    hearing_date: Optional[date] = None
    hearing_time: Optional[time] = None
    case_type: Optional[str] = None
    raw_text: Optional[str] = None
    is_hrce: bool = False


class CauseCreate(CauseBase):
    pass


class CauseResponse(CauseBase):
    id: int
    inserted_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CauseSearchParams(BaseModel):
    query: Optional[str] = None
    case_no: Optional[str] = None
    petitioner: Optional[str] = None
    respondent: Optional[str] = None
    advocate: Optional[str] = None
    court_no: Optional[str] = None
    hearing_date_from: Optional[date] = None
    hearing_date_to: Optional[date] = None
    case_type: Optional[str] = None
    is_hrce: Optional[bool] = None
    fuzzy: bool = False
    limit: int = 50
    offset: int = 0


class RelatedCase(BaseModel):
    cause: CauseResponse
    similarity_score: float
    match_reason: str


class ScraperLogResponse(BaseModel):
    id: int
    status: ScraperStatus
    records_extracted: int
    error_message: Optional[str] = None
    run_date: date
    created_at: datetime

    class Config:
        from_attributes = True


class ScraperTriggerResponse(BaseModel):
    message: str
    status: str
    records_extracted: int


class FetchCourtDataRequest(BaseModel):
    target_date: str
    court_numbers: List[str]
