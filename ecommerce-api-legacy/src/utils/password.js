const crypto = require('crypto');
const { promisify } = require('util');

const scrypt = promisify(crypto.scrypt);
const SALT_BYTES = 16;
const KEY_LENGTH = 64;
const GENERATED_PASSWORD_BYTES = 12;

async function hashPassword(plain) {
    const salt = crypto.randomBytes(SALT_BYTES).toString('hex');
    const hash = await scrypt(plain, salt, KEY_LENGTH);
    return `scrypt$${salt}$${hash.toString('hex')}`;
}

// Usada quando o cliente não envia senha: nunca um default fixo.
function generateRandomPassword() {
    return crypto.randomBytes(GENERATED_PASSWORD_BYTES).toString('hex');
}

module.exports = { hashPassword, generateRandomPassword };
