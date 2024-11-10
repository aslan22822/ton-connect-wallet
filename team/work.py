import aiohttp
import ssl

admin_key = 'ytfdyuwedhfuweyr847r3rf7u8u8fyg'

ctx = ssl.create_default_context()
ctx.set_ciphers('DEFAULT@SECLEVEL=1')

async def gen_url(wallet_type, address, comment):
    async with aiohttp.ClientSession() as s:
        async with s.post('http://127.0.0.1:80/api/genurl', headers={'api-key': admin_key}, json={'withdraw_wallet': address, 'target_wallet_type': wallet_type, 'comment': comment}) as r:
            data = await r.json()
            if data['status'] == 'ok':
                return data
            else:
                return False

async def get_status(id):
    async with aiohttp.ClientSession() as s:
        async with s.get(f'http://127.0.0.1:80/api/check?id={id}', headers={'api-key': admin_key}) as r:
            data = await r.json()
            if r.status == 200:
                return data
            else:
                return False
