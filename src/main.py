from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database import engine, get_session
from models import Base
from schemas import ItemCreate, ItemRead
import crud

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.post("/items/", response_model=ItemRead)
async def api_create_item(item: ItemCreate, db: AsyncSession = Depends(get_session)):
    return await crud.create_item(db, item)

@app.get("/items/", response_model=list[ItemRead])
async def api_get_items(db: AsyncSession = Depends(get_session)):
    return await crud.get_items(db)

@app.get("/items/{item_id}", response_model=ItemRead)
async def api_get_item(item_id: int, db: AsyncSession = Depends(get_session)):
    db_item = await crud.get_item(db, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

@app.put("/items/{item_id}", response_model=ItemRead)
async def api_update_item(item_id: int, item: ItemCreate, db: AsyncSession = Depends(get_session)):
    db_item = await crud.update_item(db, item_id, item)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

@app.delete("/items/{item_id}", response_model=ItemRead)
async def api_delete_item(item_id: int, db: AsyncSession = Depends(get_session)):
    db_item = await crud.delete_item(db, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item
