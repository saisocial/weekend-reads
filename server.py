#!/usr/bin/env python3
import argparse
import json
import sqlite3
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DATABASE = ROOT / "weekend-reads.db"


def connect_database():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with connect_database() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL DEFAULT '',
                url TEXT NOT NULL DEFAULT '',
                note TEXT NOT NULL DEFAULT '',
                added_day INTEGER NOT NULL,
                added_at TEXT NOT NULL,
                is_read INTEGER NOT NULL DEFAULT 0,
                read_at TEXT
            )
            """
        )


def read_items():
    with connect_database() as connection:
        rows = connection.execute(
            """
            SELECT id, title, url, note, added_day, added_at, is_read, read_at
            FROM items
            ORDER BY added_at DESC
            """
        ).fetchall()
    return [
        {
            "id": row["id"],
            "title": row["title"],
            "url": row["url"],
            "note": row["note"],
            "addedDay": row["added_day"],
            "addedAt": row["added_at"],
            "read": bool(row["is_read"]),
            "readAt": row["read_at"],
        }
        for row in rows
    ]


def replace_items(items):
    with connect_database() as connection:
        connection.execute("DELETE FROM items")
        connection.executemany(
            """
            INSERT INTO items
                (id, title, url, note, added_day, added_at, is_read, read_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    item["id"],
                    item.get("title", ""),
                    item.get("url", ""),
                    item.get("note", ""),
                    item["addedDay"],
                    item["addedAt"],
                    int(bool(item.get("read", False))),
                    item.get("readAt"),
                )
                for item in items
            ],
        )


class WeekendReadsHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def send_json(self, payload, status=HTTPStatus.OK):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if urlparse(self.path).path == "/api/items":
            self.send_json(read_items())
            return
        super().do_GET()

    def do_PUT(self):
        if urlparse(self.path).path != "/api/items":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            items = json.loads(self.rfile.read(content_length))
            if not isinstance(items, list):
                raise ValueError("items must be a list")
            replace_items(items)
        except (ValueError, json.JSONDecodeError, KeyError, TypeError, sqlite3.Error) as error:
            self.send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
            return
        self.send_json({"saved": len(items)})

    def log_message(self, format_string, *args):
        print(f"{self.address_string()} - {format_string % args}")


def main():
    parser = argparse.ArgumentParser(description="Run the local Weekend Reads app")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    initialize_database()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), WeekendReadsHandler)
    print(f"Weekend Reads is running at http://127.0.0.1:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Weekend Reads")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
