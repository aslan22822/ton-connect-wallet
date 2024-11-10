from sqlalchemy import Column, Integer, String, MetaData, Table, select, update, insert, and_, delete, func, Float
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

metadata = MetaData()
engine = create_async_engine(f"sqlite+aiosqlite:///database.sqlite")
Session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
session = Session()

apis = Table('apis', metadata,
    Column('api', String(100), primary_key=True)
)

async def edit():
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
    await session.commit()

asyncio.run(edit())

async def reg_key(api):
    await session.execute(apis.insert().values(api=api))
    await session.commit()

async def get_key(api):
    if await session.scalar(select(apis.c.api).where(apis.c.api == api)) is None:
        return False
    else:
        return True