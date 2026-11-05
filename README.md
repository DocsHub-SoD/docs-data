# Shape of Dreams Modding API Dataset & Knowledge Base

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Database](https://img.shields.io/badge/SQLite-api.db-blue.svg)](#sqlite-database-for-modders--ai-agents)
[![Web Portal](https://img.shields.io/badge/Web-Live%20Docs-green.svg)](https://sod-docs.shshx-one.xyz/)
[![Graph View](https://img.shields.io/badge/Graph-Interactive%20View-orange.svg)](https://sod-docs.shshx-one.xyz/graph)

The canonical data layer and relational knowledge base for the **Shape of Dreams** modding ecosystem. 

This repository serves as the single source of truth for all 897 classes, structs, enums, interfaces, and methods in the game. It is designed to be consumed either via human-readable JSON files, an interactive Graph View, or directly by **AI Coding Agents** via a high-performance SQLite database.

🌐 **Live Web Portal:** [https://sod-docs.shshx-one.xyz/](https://sod-docs.shshx-one.xyz/)  
🕸️ **Interactive Graph View:** [https://sod-docs.shshx-one.xyz/graph](https://sod-docs.shshx-one.xyz/graph)

---

## What is Inside?

- **`api/*.json`**: 897 strongly-typed JSON models documenting full class signatures, fields, properties, methods, parameter types, summaries, and inheritance trees.
- **`api.db`**: An indexed SQLite database (~2.0 MB) enriched with domain categories (`category`, `tag`), foreign keys, and fast indexes.
- **`api-graph.json`**: A lightweight knowledge graph (~544 KB) mapping all class dependencies, base classes, and interfaces.
- **`api-taxonomy.json`**: Verified domain categorization across 9 architectural domains.
- **`LLM_GUIDE.md`**: Dedicated system prompt and SQL cheat sheet for AI agents to query the database without blowing their context window.
- **`scripts/compile_db.py`**: Automated compilation engine that builds `api.db` and `api-graph.json` upon PR merge.

---

## Domain Taxonomy & Categorization

The entire game assembly has been organized into 9 domains:
- 🔴 **Combat & Abilities** (146 types): Spells, ability instances, triggers, cooldowns, projectiles.
- 🟢 **Actors & Entities** (143 types): Monsters, heroes, boss logic, AI behaviors, actors.
- 🔵 **Managers & Systems** (131 types): Singletons, audio, console, zones, cameras.
- 🟠 **Data & Core Math** (140 types): Stats, enums, grid math, serialization.
- 🟣 **Buffs & Statuses** (50 types): Debuffs, curses, stat modifiers, telegraphs.
- 🟡 **Items & Economy** (49 types): Artifacts, shrines, drops, accessories.
- 🌸 **User Interface** (69 types): Windows, buttons, HUD, cursor, gamepad hints.
- 🔷 **Networking** (29 types): RPCs, Mirror syncing, lobbies, rooms.
- 🔘 **Miscellaneous & Utility** (140 types): Engine helpers, reflection, caches.

---

## How to Query the SQLite Database (`api.db`)

Filter directly by category or keyword:
```sql
-- Find all Combat classes
SELECT name, summary FROM types WHERE category = 'Combat & Abilities' AND kind = 'Class';

-- Find methods dealing with Cast/Spells
SELECT t.name, m.name, m.declaration 
FROM members m 
JOIN types t ON m.type_uid = t.uid 
WHERE m.name LIKE '%Cast%' LIMIT 10;
```

---

## License
MIT License. Free for all community members, tool developers, and modders.
