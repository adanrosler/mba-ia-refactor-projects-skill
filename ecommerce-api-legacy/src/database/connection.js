const sqlite3 = require('sqlite3');

function openDatabase(filename) {
    return new Promise((resolve, reject) => {
        const raw = new sqlite3.Database(filename, (err) => (err ? reject(err) : resolve(raw)));
    });
}

async function createConnection(filename) {
    const raw = await openDatabase(filename);

    const run = (sql, params = []) => new Promise((resolve, reject) => {
        raw.run(sql, params, function onRun(err) {
            if (err) return reject(err);
            return resolve({ lastID: this.lastID, changes: this.changes });
        });
    });
    const get = (sql, params = []) => new Promise((resolve, reject) => {
        raw.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
    });
    const all = (sql, params = []) => new Promise((resolve, reject) => {
        raw.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
    });
    const close = () => new Promise((resolve, reject) => {
        raw.close((err) => (err ? reject(err) : resolve()));
    });

    // Uma única conexão: transações são enfileiradas para não se sobreporem.
    let queue = Promise.resolve();
    const withTransaction = (work) => {
        const execute = async () => {
            await run('BEGIN IMMEDIATE');
            try {
                const result = await work();
                await run('COMMIT');
                return result;
            } catch (err) {
                await run('ROLLBACK');
                throw err;
            }
        };
        const result = queue.then(execute);
        queue = result.catch(() => {});
        return result;
    };

    return { run, get, all, close, withTransaction };
}

module.exports = { createConnection };
