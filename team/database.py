from sqlalchemy import Column, Integer, String, MetaData, Table, select, update, insert, and_, delete, func, Float
import secrets
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

metadata = MetaData()
engine = create_async_engine(f"sqlite+aiosqlite:///database.sqlite")
Session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
session = Session()

users = Table('users', metadata,
    Column('id', Integer, primary_key=True),
    Column('address', String(100)),
    Column('profit', Float)
)

async def edit():
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
    await session.commit()

asyncio.run(edit())

async def get_all_id():
    result = await session.execute(select(users.c.id))
    return result.scalars().all()

async def get_info(id, colum):
    return await session.scalar(select(users.c[colum]).where(users.c.id == id))

async def check_reg(id):
    if await session.scalar(select(users.c.id).where(users.c.id == id)) is None:
        return False
    else:
        return True

async def add_balance(id, summ):
    bal = await get_info(id, 'profit')
    await session.execute(users.update().where(users.c.id == id).values(profit=bal + summ))
    await session.commit()

async def del_balance(id, summ):
    bal = await get_info(id, 'profit')
    await session.execute(users.update().where(users.c.id == id).values(profit=bal - summ))
    await session.commit()

async def change_address(id, address):
    await session.execute(users.update().where(users.c.id == id).values(address=address))
    await session.commit()

async def reg(id):
    await session.execute(users.insert().values(id=id, address='Не указан', profit=0.0))
    await session.commit()

