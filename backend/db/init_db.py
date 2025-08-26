from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import User, Email, Attachment, Followup, Base

DATABASE_URL = "postgresql+psycopg2://myuser:mypassword@db:5432/mydatabase"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

# Create all tables
Base.metadata.create_all(bind=engine)