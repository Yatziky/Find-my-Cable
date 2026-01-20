import os
import logging
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from sqlalchemy.ext.declarative import declarative_base

# -----------------------
# Logging
# -----------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")

# -----------------------
# Database setup
# -----------------------
DB_HOST = os.environ.get("DB_HOST", "")
DB_PORT = os.environ.get("DB_PORT", "3306")
DB_NAME = os.environ.get("DB_NAME", "")
DB_USERNAME = os.environ.get("DB_USERNAME", "")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")

if not all([DB_HOST, DB_NAME, DB_USERNAME, DB_PASSWORD]):
    logger.warning("Database environment variables are not fully set!")

DATABASE_URL = f"mysql+aiomysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
logger.info(f"Connecting to DB: {DB_HOST}:{DB_PORT}/{DB_NAME}")

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def get_session():
    try:
        async with AsyncSessionLocal() as session:
            yield session
    except Exception as e:
        logger.error(f"DB session creation failed: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Database unavailable")

Base = declarative_base()

# -----------------------
# Example model
# -----------------------
from sqlalchemy import Column, Integer, String

class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(250), nullable=True)

# -----------------------
# FastAPI app
# -----------------------
app = FastAPI(title="Find-my-Cable API")

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

# -----------------------
# Pydantic schemas
# -----------------------
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

# -----------------------
# Routes
# -----------------------
@app.post("/items/", response_model=ItemRead)
async def create_item(item: ItemCreate, db: AsyncSession = Depends(get_session)):
    try:
        db_item = Item(name=item.name, description=item.description)
        db.add(db_item)
        await db.commit()
        await db.refresh(db_item)
        return db_item
    except Exception as e:
        logger.error(f"Failed to create item: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Database operation failed")

@app.get("/items/{item_id}", response_model=ItemRead)
async def read_item(item_id: int, db: AsyncSession = Depends(get_session)):
    try:
        result = await db.execute(text("SELECT * FROM items WHERE id = :id"), {"id": item_id})
        row = result.first()
        if not row:
            raise HTTPException(status_code=404, detail="Item not found")
        return ItemRead(id=row.id, name=row.name, description=row.description)
    except Exception as e:
        logger.error(f"Failed to read item: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Database operation failed")

# -----------------------
# Run Uvicorn
# -----------------------
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Uvicorn server...")
    uvicorn.run("main:app", host="0.0.0.0", port=8080, log_level="info")
