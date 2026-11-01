const crypto = require('crypto');
const { promisify } = require('util');

const scrypt = promisify(crypto.scrypt);
const SALT_BYTES = 16;
const KEY_LENGTH = 64;
const RANDOM_PASSWORD_BYTES = 12;

async function hashPassword(plain) {
    const salt = crypto.randomBytes(SALT_BYTES).toString('hex');
    const hash = await scrypt(plain, salt, KEY_LENGTH);
    return `scrypt$${salt}$${hash.toString('hex')}`;
}

async function verifyPassword(plain, stored) {
    const [scheme, salt, hash] = String(stored).split('$');
    if (scheme !== 'scrypt' || !salt || !hash) return false;
    const candidate = await scrypt(plain, salt, KEY_LENGTH);
    const expected = Buffer.from(hash, 'hex');
    return expected.length === candidate.length && crypto.timingSafeEqual(candidate, expected);
}

function generateRandomPassword() {
    return crypto.randomBytes(RANDOM_PASSWORD_BYTES).toString('hex');
}

module.exports = { hashPassword, verifyPassword, generateRandomPassword };
