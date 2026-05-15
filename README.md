# SchemaSnap

Automatically diffs and versions database schema changes across migrations for PostgreSQL and MySQL.

---

## Installation

```bash
pip install schemasnap
```

---

## Usage

Point SchemaSnap at your database and let it capture a snapshot of your current schema:

```bash
schemasnap capture --db postgresql://user:password@localhost/mydb
```

Run it again after a migration to automatically diff and version the changes:

```bash
schemasnap diff --db postgresql://user:password@localhost/mydb
```

Example output:

```
[+] Table added: user_sessions
[~] Table modified: orders
    [+] Column added: discount_code (VARCHAR 50)
    [-] Column removed: legacy_ref
[-] Table removed: temp_imports
```

Snapshots are stored locally in a `.schemasnap/` directory and can be committed alongside your codebase to track schema history over time.

### MySQL Support

```bash
schemasnap capture --db mysql://user:password@localhost/mydb
```

### Python API

```python
from schemasnap import SchemaSnap

snap = SchemaSnap(dsn="postgresql://user:password@localhost/mydb")
snap.capture()
diff = snap.diff()
print(diff.summary())
```

---

## Configuration

Create a `schemasnap.toml` in your project root to set defaults:

```toml
[database]
dsn = "postgresql://user:password@localhost/mydb"

[snapshots]
directory = ".schemasnap"
```

---

## License

MIT © SchemaSnap Contributors