const sqlite3 = require('sqlite3');

function createDatabase(filename) {
    const raw = new sqlite3.Database(filename);

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
    const exec = (sql) => new Promise((resolve, reject) => {
        raw.exec(sql, (err) => (err ? reject(err) : resolve()));
    });
    const close = () => new Promise((resolve, reject) => {
        raw.close((err) => (err ? reject(err) : resolve()));
    });

    // Uma única conexão compartilhada: as transações são enfileiradas para que
    // BEGIN/COMMIT de requisições concorrentes nunca se intercalem.
    let queue = Promise.resolve();
    function transaction(work) {
        const result = queue.then(async () => {
            await run('BEGIN IMMEDIATE');
            try {
                const value = await work();
                await run('COMMIT');
                return value;
            } catch (err) {
                await run('ROLLBACK').catch(() => {});
                throw err;
            }
        });
        queue = result.catch(() => {});
        return result;
    }

    return { run, get, all, exec, close, transaction };
}

module.exports = { createDatabase };
