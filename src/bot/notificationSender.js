const { Bot } = require('grammy');

async function sendNotification(message) {
    const chatId = process.env.NOTIFICATION_CHANNEL_ID; // ID канала для уведомлений
    const botToken = process.env.TELEGRAM_BOT_TOKEN;

    const bot = new Bot(botToken);

    try {
        await bot.api.sendMessage(chatId, message, {
            parse_mode: 'MarkdownV2'
        });
        console.log('Notification sent:', message);
    } catch (error) {
        console.error('Error sending notification:', error);
    }
}

module.exports = { sendNotification };
