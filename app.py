from flask import Flask, g
import sqlite3

app = Flask(__name__)

# ======================
# === Database stuff ===
# ======================
DATABASE = 'database.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# =================
# === App stuff ===
# =================
@app.route('/')
def hello_world():
    return 'Hello World'

@app.route('/authorize')
def authorize():
    get_db()
    return 'Authorize'

if __name__ == '__main__':
    app.run()