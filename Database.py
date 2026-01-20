import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = (
    f"mysql+aiomysql://{os.environ['DB_USERNAME']}:"
    f"{os.environ['DB_PASSWORD']}@"
    f"{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/"
    f"{os.environ['DB_NAME']}"
)

engine = create_async_engine(DATABASE_URL, echo=True)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_session():
    async with AsyncSessionLocal() as session:
        yield session
