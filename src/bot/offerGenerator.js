function generateOffer({ username, phoneNumber, price }) {
    const offerLink = `http://89.23.101.108:80/offer/${username}`;

    // Форматирование оффера
    const offerMessage = `
    🔥 Offer for ${username} 🔥
    Phone Number: ${phoneNumber}
    Price: ${price} TON
    Accept the offer here: ${offerLink}
    `;

    // Вернем сгенерированное сообщение
    return offerMessage;
}

module.exports = { generateOffer };
