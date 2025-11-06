from pydantic import BaseModel
from datetime import datetime

class UserInfo(BaseModel):
    email: str
    full_name: str | None
    created_at: datetime | None

class UserEncrypt(BaseModel):
    google_sub: bytes
    encrypted_access_token : bytes
    encrypted_refresh_token  : bytes | None

class Email(BaseModel):
    user_id : int
    email_id : str
    sender : str | None
    subject : str | None
    received_at : datetime | None
    category : str | None
    urgency : str | None
    is_deleted : bool

class Attachment(BaseModel):
    email_id : int | None
    filename : str | None
    filetype : str | None
    url : str | None

class Followup(BaseModel):
    email_id : str
    remind_at : datetime