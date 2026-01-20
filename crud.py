from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Item
from schemas import ItemCreate

async def create_item(db: AsyncSession, item: ItemCreate):
    db_item = Item(name=item.name, description=item.description)
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item

async def get_item(db: AsyncSession, item_id: int):
    result = await db.execute(select(Item).filter(Item.id == item_id))
    return result.scalars().first()

async def get_items(db: AsyncSession):
    result = await db.execute(select(Item))
    return result.scalars().all()

async def update_item(db: AsyncSession, item_id: int, item: ItemCreate):
    db_item = await get_item(db, item_id)
    if db_item:
        db_item.name = item.name
        db_item.description = item.description
        await db.commit()
        await db.refresh(db_item)
    return db_item

async def delete_item(db: AsyncSession, item_id: int):
    db_item = await get_item(db, item_id)
    if db_item:
        await db.delete(db_item)
        await db.commit()
    return db_item
