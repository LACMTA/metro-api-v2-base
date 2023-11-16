# Using SQLAlchemy to connect to the Database

from sqlalchemy import create_engine,MetaData, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config import Config
# from .utils.log_helper import *

engine = create_engine(Config.API_DB_URI, echo=False,pool_size=20, max_overflow=0)

Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

session = Session()

Base = declarative_base(metadata=MetaData(schema=Config.TARGET_DB_SCHEMA))

def get_db():
    db = Session()
    try:
        # Execute a simple query to keep the connection alive
        db.execute(text("SELECT 1"))
        yield db
    finally:
        db.close()