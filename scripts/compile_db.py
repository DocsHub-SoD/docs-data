"""
Compiles the normalized JSON API data and extracted Cecil metadata into:
1. SQLite Database (api.db) with categories, tags, assemblies, attributes, enum values, and dependencies.
2. Lightweight JSON Knowledge Graph (api-graph.json) for fast zero-overhead traversal.
"""

import sqlite3
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
API_JSON_DIR = REPO_ROOT / "api"
CATALOG_PATH = REPO_ROOT / "api-catalog.json"
TAXONOMY_PATH = REPO_ROOT / "api-taxonomy.json"
ENUMS_PATH = REPO_ROOT / "enums.json"
METADATA_PATH = REPO_ROOT / "enriched_metadata.json"
DEPS_PATH = REPO_ROOT / "dependencies.json"

DB_PATH = REPO_ROOT / "api.db"
GRAPH_PATH = REPO_ROOT / "api-graph.json"


def build_databases():
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE types (
        uid TEXT PRIMARY KEY,
        name TEXT,
        kind TEXT,
        category TEXT,
        tag TEXT,
        assembly TEXT,
        attributes TEXT,
        namespace TEXT,
        summary TEXT,
        syntax TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE hierarchy (
        child_uid TEXT,
        parent_uid TEXT,
        relation_type TEXT,
        PRIMARY KEY (child_uid, parent_uid, relation_type)
    )
    """)

    cur.execute("""
    CREATE TABLE members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type_uid TEXT,
        member_type TEXT,
        name TEXT,
        attributes TEXT,
        declaration TEXT,
        summary TEXT,
        returns TEXT,
        FOREIGN KEY(type_uid) REFERENCES types(uid)
    )
    """)

    cur.execute("""
    CREATE TABLE parameters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER,
        name TEXT,
        param_type TEXT,
        param_type_uid TEXT,
        description TEXT,
        FOREIGN KEY(member_id) REFERENCES members(id)
    )
    """)

    cur.execute("""
    CREATE TABLE enum_values (
        type_uid TEXT NOT NULL,
        name TEXT NOT NULL,
        value INTEGER NOT NULL,
        hex_value TEXT,
        PRIMARY KEY (type_uid, name)
    )
    """)

    cur.execute("""
    CREATE TABLE dependencies (
        from_uid TEXT NOT NULL,
        to_uid TEXT NOT NULL,
        relation TEXT NOT NULL,
        PRIMARY KEY (from_uid, to_uid, relation)
    )
    """)

    cur.execute("CREATE INDEX idx_members_name ON members(name)")
    cur.execute("CREATE INDEX idx_members_type ON members(type_uid)")
    cur.execute("CREATE INDEX idx_hierarchy_child ON hierarchy(child_uid)")
    cur.execute("CREATE INDEX idx_hierarchy_parent ON hierarchy(parent_uid)")
    cur.execute("CREATE INDEX idx_params_type_uid ON parameters(param_type_uid)")
    cur.execute("CREATE INDEX idx_types_category ON types(category)")
    cur.execute("CREATE INDEX idx_enum_values_uid ON enum_values(type_uid)")
    cur.execute("CREATE INDEX idx_dep_from ON dependencies(from_uid)")
    cur.execute("CREATE INDEX idx_dep_to ON dependencies(to_uid)")

    graph = {
        "nodes": {},
        "edges": []
    }

    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    taxonomy = json.loads(TAXONOMY_PATH.read_text(encoding="utf-8")) if TAXONOMY_PATH.exists() else {}
    enums_data = json.loads(ENUMS_PATH.read_text(encoding="utf-8")) if ENUMS_PATH.exists() else {}
    enriched_meta = json.loads(METADATA_PATH.read_text(encoding="utf-8")) if METADATA_PATH.exists() else {}
    deps_data = json.loads(DEPS_PATH.read_text(encoding="utf-8")) if DEPS_PATH.exists() else {}

    # 1. Populate Enum Values
    for uid, enum_info in enums_data.items():
        for m in enum_info.get("members", []):
            cur.execute("""
            INSERT OR IGNORE INTO enum_values (type_uid, name, value, hex_value)
            VALUES (?, ?, ?, ?)
            """, (uid, m["name"], m["value"], m["hexValue"]))

    # 2. Populate Types & Members
    for item in catalog:
        uid = item["uid"]
        json_file = API_JSON_DIR / f"{uid}.json"
        if not json_file.exists():
            continue

        data = json.loads(json_file.read_text(encoding="utf-8"))
        tax = taxonomy.get(uid, {"category": "Miscellaneous & Utility", "tag": "misc"})
        meta = enriched_meta.get(uid, {})

        asm = meta.get("assembly") or data.get("assembly", "Dew.Core.dll")
        type_attrs = " ".join(meta.get("attributes", []))

        cur.execute("""
        INSERT INTO types (uid, name, kind, category, tag, assembly, attributes, namespace, summary, syntax)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("uid"),
            data.get("name"),
            data.get("kind"),
            tax.get("category"),
            tax.get("tag"),
            asm,
            type_attrs,
            data.get("namespace"),
            data.get("summary"),
            data.get("syntax")
        ))

        graph["nodes"][uid] = {
            "name": data.get("name"),
            "kind": data.get("kind"),
            "category": tax.get("category"),
            "assembly": asm,
            "summary": data.get("summary"),
            "methods": [m.get("name") for m in data.get("methods", [])],
            "extends": [i.get("uid") for i in data.get("inheritance", [])],
            "implements": [i.get("uid") for i in data.get("implements", [])]
        }

        for inh in data.get("inheritance", []):
            p_uid = inh.get("uid")
            if p_uid:
                cur.execute("INSERT OR IGNORE INTO hierarchy VALUES (?, ?, 'extends')", (uid, p_uid))
                cur.execute("INSERT OR IGNORE INTO dependencies VALUES (?, ?, 'extends')", (uid, p_uid))
                graph["edges"].append({"source": uid, "target": p_uid, "type": "extends"})

        for imp in data.get("implements", []):
            i_uid = imp.get("uid")
            if i_uid:
                cur.execute("INSERT OR IGNORE INTO hierarchy VALUES (?, ?, 'implements')", (uid, i_uid))
                cur.execute("INSERT OR IGNORE INTO dependencies VALUES (?, ?, 'implements')", (uid, i_uid))
                graph["edges"].append({"source": uid, "target": i_uid, "type": "implements"})

        # Map methods with Cecil attributes
        meta_methods = {m["name"]: m for m in meta.get("methods", [])}
        for m in data.get("methods", []):
            m_name = m.get("name")
            m_meta = meta_methods.get(m_name, {})
            m_attrs = " ".join(m_meta.get("attributes", []))

            cur.execute("""
            INSERT INTO members (type_uid, member_type, name, attributes, declaration, summary, returns)
            VALUES (?, 'method', ?, ?, ?, ?, ?)
            """, (uid, m_name, m_attrs, m.get("declaration"), m.get("summary"), m.get("returns")))
            m_id = cur.lastrowid

            for p in m.get("parameters", []):
                cur.execute("""
                INSERT INTO parameters (member_id, name, param_type, param_type_uid, description)
                VALUES (?, ?, ?, ?, ?)
                """, (m_id, p.get("name"), p.get("type"), p.get("type_uid"), p.get("description")))

        # Map fields with Cecil attributes
        meta_fields = {f["name"]: f for f in meta.get("fields", [])}
        for f in data.get("fields", []):
            f_name = f.get("name")
            f_meta = meta_fields.get(f_name, {})
            f_attrs = " ".join(f_meta.get("attributes", []))

            cur.execute("""
            INSERT INTO members (type_uid, member_type, name, attributes, declaration, summary, returns)
            VALUES (?, 'field', ?, ?, ?, ?, ?)
            """, (uid, f_name, f_attrs, f.get("declaration"), f.get("summary"), None))

        # Map properties with Cecil attributes
        meta_props = {p["name"]: p for p in meta.get("properties", [])}
        for p in data.get("properties", []):
            p_name = p.get("name")
            p_meta = meta_props.get(p_name, {})
            p_attrs = " ".join(p_meta.get("attributes", []))

            cur.execute("""
            INSERT INTO members (type_uid, member_type, name, attributes, declaration, summary, returns)
            VALUES (?, 'property', ?, ?, ?, ?, ?)
            """, (uid, p_name, p_attrs, p.get("declaration"), p.get("summary"), None))

    # 3. Populate Dependencies from Cecil Call & Type Graph
    for from_uid, dep_info in deps_data.items():
        for to_uid in dep_info.get("uses", []):
            cur.execute("""
            INSERT OR IGNORE INTO dependencies (from_uid, to_uid, relation)
            VALUES (?, ?, 'uses')
            """, (from_uid, to_uid))

    conn.commit()
    conn.close()

    GRAPH_PATH.write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Built SQLite Database: {DB_PATH} ({DB_PATH.stat().st_size / 1024:.1f} KB)")
    print(f"Built JSON Knowledge Graph: {GRAPH_PATH} ({GRAPH_PATH.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    build_databases()
