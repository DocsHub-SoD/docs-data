import sqlite3
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TAXONOMY_PATH = REPO_ROOT / "api-taxonomy.json"
DB_PATH = REPO_ROOT / "api.db"

def update_db():
    taxonomy = json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cols = [c[1] for c in cur.execute("PRAGMA table_info(types)").fetchall()]
    if "category" not in cols:
        cur.execute("ALTER TABLE types ADD COLUMN category TEXT")
    if "tag" not in cols:
        cur.execute("ALTER TABLE types ADD COLUMN tag TEXT")

    for uid, data in taxonomy.items():
        cur.execute("UPDATE types SET category = ?, tag = ? WHERE uid = ?", (data["category"], data["tag"], uid))

    conn.commit()
    sample = cur.execute("SELECT name, category, tag FROM types WHERE name = 'AbilityTrigger'").fetchone()
    print("Database enriched! Sample:", sample)
    conn.close()

if __name__ == "__main__":
    update_db()
