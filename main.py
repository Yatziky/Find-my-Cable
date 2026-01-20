from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database import engine, get_session
from models import Base
from schemas import ItemCreate, ItemRead
import crud

import logging

# --- Logging setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")
logger.info("FastAPI app defined (before startup)")

# --- FastAPI App ---
app = FastAPI()

@app.on_event("startup")
async def on_startup():
    logger.info("Running startup: creating database tables")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.post("/items/", response_model=ItemRead)
async def api_create_item(item: ItemCreate, db: AsyncSession = Depends(get_session)):
    return await crud.create_item(db, item)

# ... your other route handlers ...

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Uvicorn server")
    uvicorn.run("main:app", host="0.0.0.0", port=8080, log_level="info")
