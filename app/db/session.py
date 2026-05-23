from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from app.config import settings

engine = create_async_engine(
    settings.db_dns,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(engine)

async def get_db_session():
    async with AsyncSessionLocal() as session:
        yield session