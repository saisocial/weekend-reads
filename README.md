# Weekend Reads

A small reading list that stores data in a local SQLite database when run locally.

## Run locally

From this folder:

```bash
python3 server.py
```

Open http://127.0.0.1:8000 in a browser. The database is created as `weekend-reads.db` in this folder and is excluded from Git.

To use another port:

```bash
python3 server.py --port 8080
```

The GitHub Pages version remains available at https://saisocial.github.io/weekend-reads/ and falls back to browser storage because GitHub Pages cannot run the local Python API.
