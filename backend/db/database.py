from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import User, Email, Attachment, Followup, Base
import os

DATABASE_URL = os.getenv('DB_URL')

engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)

# Create all tables
Base.metadata.create_all(bind=engine)

# Function that connects to the db
def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()