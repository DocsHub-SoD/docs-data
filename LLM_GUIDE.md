# AI Agent Guide: Shape of Dreams Modding API

You are acting as an expert assistant for creating mods for the game Shape of Dreams (Unity / C# / Harmony / BepInEx).

## Available Database Resources
This repository contains a compiled SQLite database `api.db` and a structured dependency graph `api-graph.json`.
NEVER attempt to read the entire documentation at once. Use targeted SQL queries against `api.db` to conserve context and instantly obtain exact method signatures.

### Database Schema (`api.db`):
1. `types` (`uid`, `name`, `kind`, `namespace`, `summary`, `syntax`) — Registry of all 897 types.
2. `hierarchy` (`child_uid`, `parent_uid`, `relation_type`) — Inheritance tree (`extends`, `implements`).
3. `members` (`id`, `type_uid`, `member_type`, `name`, `declaration`, `summary`, `returns`) — Methods, fields, and properties.
4. `parameters` (`id`, `member_id`, `name`, `param_type`, `param_type_uid`, `description`) — Method arguments and parameter types.

### Targeted Query Patterns:
- Search methods by keyword (e.g., `Cast`, `Spell`, `Damage`):
  ```sql
  SELECT t.name, m.name, m.declaration 
  FROM members m 
  JOIN types t ON m.type_uid = t.uid 
  WHERE m.name LIKE '%Cast%' LIMIT 10;
  ```
- Inspect parents and subclasses of a type:
  ```sql
  SELECT child_uid FROM hierarchy WHERE parent_uid = 'Global.Actor';
  ```
- Find methods accepting a specific parameter type:
  ```sql
  SELECT t.name, m.name, p.name 
  FROM parameters p 
  JOIN members m ON p.member_id = m.id 
  JOIN types t ON m.type_uid = t.uid 
  WHERE p.param_type_uid = 'Global.Entity';
  ```
