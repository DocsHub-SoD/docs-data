# docs-data

Structured API data, SQLite database, and dependency graph for the game **Shape of Dreams**.

This repository serves as the central data source for the documentation site ([sod-docs.shshx-one.xyz](https://sod-docs.shshx-one.xyz/)) and provides tools to query game types directly without opening hundreds of files.

---

## What is in this repository?

- **`api/`**: 897 JSON files, one per type (classes, structs, interfaces, enums). Each file contains member declarations, return types, parameters, inheritance links, and available XML summaries.
- **`api.db`**: SQLite database generated from the JSON files. Includes indexes and foreign keys for quick querying.
- **`api-graph.json`**: Graph containing inheritance links (`extends`, `implements`) and member lists for traversal.
- **`LLM_GUIDE.md`**: Schema definition and query examples for AI coding assistants.
- **`scripts/compile_db.py`**: Python script that builds `api.db` and `api-graph.json` from the `api/` directory.

---

## How to use this data

### 1. Reading raw JSON files
You can inspect individual classes directly in the `api/` folder (e.g., `api/Global.AbilityInstance.json`). 

### 2. Using the SQLite database (`api.db`)
Instead of reading through many files or grepping folders, you can query `api.db` with standard SQLite tools (or have an LLM assistant query it).

Examples:

Find methods related to casting abilities:
```sql
SELECT t.name, m.name, m.declaration 
FROM members m 
JOIN types t ON m.type_uid = t.uid 
WHERE m.name LIKE '%Cast%' LIMIT 10;
```

Find classes that inherit from `Actor`:
```sql
SELECT child_uid FROM hierarchy WHERE parent_uid = 'Global.Actor';
```

Find methods that take `Entity` as a parameter:
```sql
SELECT t.name, m.name, p.name 
FROM parameters p 
JOIN members m ON p.member_id = m.id 
JOIN types t ON m.type_uid = t.uid 
WHERE p.param_type_uid = 'Global.Entity';
```

### 3. Using with AI assistants (Cursor, Copilot, Cline, etc.)
If you use an LLM assistant while modding, give it `LLM_GUIDE.md` and `api.db`. Tell it to run SQL queries against `api.db` to check method signatures and types before writing patches. This keeps the assistant from making up non-existent methods and saves context space.

---

## Contributing

Most classes currently only have raw C# signatures without descriptions because the game's official docs lacked them.

If you know what a specific class, method, or parameter does, feel free to fill in the `summary` fields in `api/<TypeName>.json` and submit a Pull Request.

When a PR is merged into `main`, a GitHub Actions workflow automatically runs `compile_db.py` to rebuild `api.db` and `api-graph.json`.

---

## Related Repositories

- [docs-site](https://github.com/DocsHub-SoD/docs-site) — The frontend website.
- [sod-docs-resources](https://github.com/DocsHub-SoD/sod-docs-resources) — Scraper and generator scripts used to extract and compile this data.

## License

MIT
