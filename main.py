import os
import asyncio
import logging

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from sqlalchemy.ext.declarative import declarative_base

# --- Logging setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")

# --- Database setup ---
DATABASE_URL = (
    f"mysql+aiomysql://{os.environ.get('DB_USERNAME','root')}:"
    f"{os.environ.get('DB_PASSWORD','password')}@"
    f"{os.environ.get('DB_HOST','127.0.0.1')}:{os.environ.get('DB_PORT','3306')}/"
    f"{os.environ.get('DB_NAME','testdb')}"
)

logger.info(f"Using database URL: {DATABASE_URL}")

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def get_session():
    async with AsyncSessionLocal() as session:
        yield session

Base = declarative_base()

# --- Example model ---
from sqlalchemy import Column, Integer, String

class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(250), nullable=True)

# --- FastAPI app ---
app = FastAPI()

# --- Startup: test DB first ---
@app.on_event("startup")
async def on_startup():
    logger.info("Starting FastAPI startup...")
    try:
        # Test DB connection
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            logger.info(f"DB test query result: {result.scalar()}")

        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Tables created successfully!")

    except Exception as e:
        logger.error(f"Database connection or table creation failed: {e}")
        # Optional: stop FastAPI if DB is not reachable
        import sys
        sys.exit(1)

# --- Example route ---
from pydantic import BaseModel

class ItemCreate(BaseModel):
    name: str
    description: str | None = None

class ItemRead(BaseModel):
    id: int
    name: str
    description: str | None = None

    class Config:
        orm_mode = True

@app.post("/items/", response_model=ItemRead)
async def create_item(item: ItemCreate, db: AsyncSession = Depends(get_session)):
    from sqlalchemy.future import select
    db_item = Item(name=item.name, description=item.description)
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item

# --- Run Uvicorn ---
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Uvicorn server...")
    uvicorn.run("main:app", host="0.0.0.0", port=8080, log_level="info")
