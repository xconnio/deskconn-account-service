import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

load_dotenv()

DATABASE_URL = os.getenv("DESKCONN_DATABASE_URL", None)

if DATABASE_URL is None or DATABASE_URL == "":
    raise ValueError("'DESKCONN_DATABASE_URL' missing in environment variables.")

engine = create_async_engine(DATABASE_URL, echo=True)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, autoflush=False, autocommit=False)


async def get_database() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
