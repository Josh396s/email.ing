from db import engine, Base
from models import User, Email, Attachment, Followup

# Create all tables
Base.metadata.create_all(bind=engine)
print(Base.metadata.tables.keys())
