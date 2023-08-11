# Using SQLAlchemy to connect to the Database

from sqlalchemy import create_engine,MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from .config import Config
from .utils.log_helper import *

def create_async_uri(uri):
    return uri.replace('postgresql', 'postgresql+asyncpg')


engine = create_engine(Config.API_DB_URI, echo=False)
async_engine = create_async_engine(create_async_uri(Config.API_DB_URI), echo=False)
async_session = sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# LocalSession = sessionmaker(autocommit=False, autoflush=True, bind=async_engine, expire_on_commit=True)

session = Session()

Base = declarative_base(metadata=MetaData(schema=Config.TARGET_DB_SCHEMA))

def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()

async def get_async_db():
    async with async_session() as db:
        try:
            yield db
        finally:
            await async_engine.dispose()

# async def get_refreshed_db(query):
#     async with engine.begin() as conn:

#             await conn.execute(
#                 query
#             )
#     await engine.dispose()