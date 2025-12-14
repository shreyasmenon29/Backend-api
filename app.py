from flask import Flask, request, jsonify
import sqlite3
import random

app = Flask(__name__)

DB = "game.db"

# ---------- DATABASE ----------
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS rooms (
        id INTEGER PRIMARY KEY AUTOINCREMENT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_id INTEGER,
        name TEXT,
        role TEXT,
        points INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------- ROUTES ----------
@app.route("/")
def home():
    return "Backend running (Python + SQLite)"

@app.route("/room/create", methods=["POST"])
def create_room():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO rooms DEFAULT VALUES")
    conn.commit()
    room_id = cur.lastrowid
    conn.close()
    return jsonify({"room_id": room_id})

@app.route("/room/join", methods=["POST"])
def join_room():
    data = request.json
    room_id = data["room_id"]
    name = data["player_name"]

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM players WHERE room_id=?", (room_id,))
    if cur.fetchone()[0] >= 4:
        return jsonify({"error": "Room full"}), 400

    cur.execute(
        "INSERT INTO players (room_id, name) VALUES (?, ?)",
        (room_id, name)
    )

    conn.commit()
    player_id = cur.lastrowid
    conn.close()

    return jsonify({"player_id": player_id})

@app.route("/room/assign/<int:room_id>", methods=["POST"])
def assign_roles(room_id):
    roles = ["Raja", "Mantri", "Chor", "Sipahi"]
    random.shuffle(roles)

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT id FROM players WHERE room_id=?", (room_id,))
    players = cur.fetchall()

    if len(players) != 4:
        return jsonify({"error": "Need exactly 4 players"}), 400

    for player, role in zip(players, roles):
        cur.execute(
            "UPDATE players SET role=? WHERE id=?",
            (role, player["id"])
        )

    conn.commit()
    conn.close()

    return jsonify({"message": "Roles assigned"})

@app.route("/guess/<int:room_id>", methods=["POST"])
def guess(room_id):
    guessed_id = request.json["guessed_player_id"]

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM players WHERE room_id=?", (room_id,))
    players = cur.fetchall()

    chor = next(p for p in players if p["role"] == "Chor")
    raja = next(p for p in players if p["role"] == "Raja")
    mantri = next(p for p in players if p["role"] == "Mantri")
    sipahi = next(p for p in players if p["role"] == "Sipahi")

    if guessed_id == chor["id"]:
        cur.execute("UPDATE players SET points=1000 WHERE id=?", (raja["id"],))
        cur.execute("UPDATE players SET points=800 WHERE id=?", (mantri["id"],))
        cur.execute("UPDATE players SET points=500 WHERE id=?", (sipahi["id"],))
    else:
        cur.execute("UPDATE players SET points=1300 WHERE id=?", (chor["id"],))
        cur.execute("UPDATE players SET points=1000 WHERE id=?", (raja["id"],))

    conn.commit()

    cur.execute("SELECT name, role, points FROM players WHERE room_id=?", (room_id,))
    result = [dict(row) for row in cur.fetchall()]
    conn.close()

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
