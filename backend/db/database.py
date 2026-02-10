from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import User, Email, Attachment, Followup, Base
from config import settings

DATABASE_URL = settings.DB_URL

engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)

# Function that connects to the db
def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()