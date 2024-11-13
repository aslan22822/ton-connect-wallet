require('dotenv').config();
const express = require('express');
const { setupBot } = require('./bot/bot');
const { setupWebServer } = require('./web/server');

const app = express();
const port = process.env.PORT || 3000;

// Настройка Telegram бота
setupBot();

// Настройка веб-сервера
setupWebServer(app);

// Запуск сервера
app.listen(port, () => {
    console.log(`Server is running on port ${port}`);
});
