from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    emails = relationship("Email", back_populates="users", cascade="all, delete-orphan")

class Email(Base):
    __tablename__ = 'emails'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id  = Column(Integer, ForeignKey('users.id'), nullable=False)
    email_id  = Column(String, nullable=False)
    sender  = Column(String)
    subject = Column(String)
    received_at = Column(DateTime)
    category = Column(String)
    urgency = Column(String)
    is_deleted = Column(Boolean, default=False)

    users = relationship("User", back_populates="emails")
    attachments = relationship("Attachment", back_populates="emails", cascade="all, delete-orphan")
    followups = relationship("Followup", back_populates="emails", cascade="all, delete-orphan")

class Attachment(Base):
    __tablename__ = 'attachments'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email_id = Column(Integer, ForeignKey('emails.id'), nullable=False)
    filename  = Column(String)
    filetype = Column(String)
    url = Column(String)

    emails = relationship("Email", back_populates="attachments")

class Followup(Base):
    __tablename__ = 'followups'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email_id = Column(Integer, ForeignKey('emails.id'), nullable=False)
    remind_at = Column(DateTime)

    emails = relationship("Email", back_populates="followups")