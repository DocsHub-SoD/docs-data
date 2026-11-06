# AI Agent Guide: Shape of Dreams Modding API & Database

You are acting as an expert autonomous AI coding assistant creating and debugging mods for the Unity action-roguelike **Shape of Dreams** (C# / Harmony / BepInEx / DewMod).

---

## 1. Database Architecture (`api.db`)

The SQLite database `api.db` contains complete, bytecode-extracted metadata from the official game assemblies (`Dew.Core.dll`, `Dew.Contents.dll`, `Dew.UI.dll`, `Assembly-CSharp.dll`).

> [!IMPORTANT]
> **Context Conservation**: NEVER attempt to read the entire database or dump full tables. Use specific, targeted SQL queries with `LIMIT` clauses to fetch exact declarations, assemblies, attributes, and enum constants.

### Database Tables & Schema

1. **`types`** — Canonical catalog of all game types:
   * `uid` (`TEXT PRIMARY KEY`) — Full unique identifier (e.g. `Global.Hero`, `Global.HeroSkillLocation`).
   * `name` (`TEXT`) — Type name (e.g. `Hero`, `AbilityLockHandle`).
   * `kind` (`TEXT`) — `Class`, `Struct`, `Enum`, `Interface`, or `Delegate`.
   * `assembly` (`TEXT`) — Exact game assembly DLL (e.g. `Dew.Core.dll`, `Dew.UI.dll`).
   * `attributes` (`TEXT`) — JSON/CSV list of attributes (e.g. `[RequireComponent]`, `[Flags]`).
   * `category` (`TEXT`) — Architectural domain (e.g. `Combat & Abilities`, `Actors & Entities`).
   * `namespace` (`TEXT`) — Namespace (`Global` for root game namespace).
   * `summary` (`TEXT`) — Docstring/description (if available).
   * `syntax` (`TEXT`) — C# declaration syntax.

2. **`enum_values`** — Exact integer and hexadecimal constants for all 118 enums:
   * `type_uid` (`TEXT`) — Full enum UID (e.g. `Global.HeroSkillLocation`).
   * `name` (`TEXT`) — Member name (e.g. `Q`, `W`, `E`, `R`, `Identity`, `Movement`).
   * `value` (`INTEGER`) — Integer value (e.g. `0`, `1`, `2`, `3`, `4`, `5`).
   * `hex_value` (`TEXT`) — Hexadecimal value (e.g. `0x0`, `0x1`, `0x4`).

3. **`dependencies`** — Call Graph and Type Usage links (XRefs):
   * `from_uid` (`TEXT`) — Source type (caller or dependent).
   * `to_uid` (`TEXT`) — Target type (callee or dependency).
   * `relation` (`TEXT`) — `uses` or `implements` or `extends`.

4. **`hierarchy`** — OOP inheritance tree:
   * `child_uid` (`TEXT`), `parent_uid` (`TEXT`), `relation_type` (`extends` or `implements`).

5. **`members`** — Methods, properties, and fields:
   * `id` (`INTEGER PRIMARY KEY`), `type_uid` (`TEXT`), `member_type` (`Method`, `Property`, `Field`), `name` (`TEXT`), `declaration` (`TEXT`), `summary` (`TEXT`), `returns` (`TEXT`).

6. **`parameters`** — Method arguments:
   * `id` (`INTEGER PRIMARY KEY`), `member_id` (`INTEGER`), `name` (`TEXT`), `param_type` (`TEXT`), `param_type_uid` (`TEXT`), `description` (`TEXT`).

---

## 2. Essential SQL Recipes for Modding

### A. Looking up Enum Constants (Crucial for skill slots, states, damage types)
```sql
SELECT name, value, hex_value 
FROM enum_values 
WHERE type_uid = 'Global.HeroSkillLocation';
-- Returns: Q=0, W=1, E=2, R=3, Identity=4, Movement=5
```

### B. Finding Callers & Dependencies (Who calls or uses a method/type?)
```sql
-- Find which systems depend on or invoke AbilityLockHandle
SELECT from_uid, relation 
FROM dependencies 
WHERE to_uid = 'Global.AbilityLockHandle';

-- Find all types used by ControlManager
SELECT to_uid 
FROM dependencies 
WHERE from_uid = 'Global.ControlManager' LIMIT 15;
```

### C. Finding Assembly and Methods for Harmony Patches
```sql
-- Find where a type lives and inspect its methods
SELECT t.name, t.assembly, m.name, m.declaration
FROM types t
JOIN members m ON t.uid = m.type_uid
WHERE t.name = 'Hero' AND m.name LIKE '%Cast%' LIMIT 10;
```

### D. Checking Network Authority (`[Server]`, `[ClientRpc]`, `[SyncVar]`)
* Methods with `[Server]` in their declaration must ONLY be executed on the host/server. In multiplayer or client sessions, calling them directly triggers a network desync or `NullReferenceException`.
* Inspect method signatures for network attributes:
```sql
SELECT t.name, m.name, m.declaration 
FROM members m
JOIN types t ON m.type_uid = t.uid
WHERE m.declaration LIKE '%[Server]%' AND t.name = 'Hero';
```

---

## 3. Shape of Dreams Native Mod Framework (`DewMod`) Rules

When creating or fixing a mod:
1. **Mod Location**: Mods reside in `Shape of Dreams\Mods\<ModFolderName>\`.
2. **Manifest (`about/metadata.json`)**: Every mod must contain `about/metadata.json`. The game engine reads `ModMetadata` which strictly checks the following fields:
   * **`modVer`** (string) — **NOT** `version`!
   * **`assemblies`** (string array) — **NOT** `entryDll`!
   * `id` (string), `name` (string), `author` (string).
   ```json
   {
     "id": "com.author.modname",
     "name": "My Mod Name",
     "modVer": "1.0.0",
     "author": "AuthorName",
     "assemblies": [
       "MyMod.dll"
     ]
   }
   ```
   *(Warning: Using `version` or `entryDll` causes the loader to ignore the assembly, preventing the mod from starting).*

3. **Activation Key**: New mods are **NOT** enabled automatically. To activate a mod, its `id` must be listed in:
   `%USERPROFILE%\AppData\LocalLow\Lizard Smoothie\Shape of Dreams\QuickSave\r_platform.json` under `"activeMods": [ "com.author.modname", ... ]`.

4. **Main Entry Class (`ModBehaviour`)**:
   * The entry class inherits from `ModBehaviour` (`Dew.Core.dll`, namespace `Dew`), which derives directly from `UnityEngine.MonoBehaviour`.
   * **There is NO `OnLoaded()` method.** Modders and agents must use standard Unity lifecycle methods: `Awake()`, `Start()`, `Update()`, `OnDestroy()`, plus the virtual method `OnConfigChanged()`.
   * Useful built-in methods provided by `ModBehaviour`:
     * `CallOnManager<T>(Action<T> action)`
     * `CallOnNetworkedManager<T>(Action<T> action)`
     * `RegisterConsoleCommand(...)`

   ```csharp
   using UnityEngine;
   using Dew;

   namespace MyCoolMod
   {
       public class ModEntry : ModBehaviour
       {
           private void Awake()
           {
               // Initialize patches, Harmony, hooks
           }

           private void Start()
           {
               // Post-initialization
           }

           public override void OnConfigChanged()
           {
               // Called when mod settings or config values update
           }

           private void OnDestroy()
           {
               // Cleanup
           }
       }
   }
   ```
