from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional

class UserStatus(BaseModel):
    """
    Schema for authentication state and sync metadata
    """
    authenticated: bool
    user_id: int
    last_synced: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class EmailRead(BaseModel):
    """
    Schema for the email list view
    """
    id: int
    thread_id: str
    sender: Optional[str] = None
    subject: Optional[str] = None
    received_at: Optional[datetime] = None
    category: Optional[str] = None
    summary: Optional[str] = None
    urgency: Optional[str] = None
    is_processed: bool
    inference_time: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class AttachmentRead(BaseModel):
    """
    Schema for individual attachments in the UI
    """
    id: int
    filename: str
    filetype: Optional[str] = None
    url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class EmailBodyResponse(BaseModel):
    """
    Schema for the detailed email view including decrypted body
    """
    body: str
    attachments: List[AttachmentRead]