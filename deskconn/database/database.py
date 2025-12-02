import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from deskconn.models import Base

load_dotenv()

DATABASE_PATH = os.getenv("DESKCONN_DBPATH", None)
if DATABASE_PATH is None or DATABASE_PATH == "":
    raise ValueError("'DESKCONN_DBPATH' missing in environment variables.")

DATABASE_URL = f"sqlite+aiosqlite:///{DATABASE_PATH}"

engine = create_async_engine(DATABASE_URL, echo=True)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, autoflush=False, autocommit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
