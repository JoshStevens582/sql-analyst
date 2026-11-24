"""Synthetic retail warehouse schema and seed data. No live ledger rows."""

from __future__ import annotations

import sqlite3
from pathlib import Path

DDL = """
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    sku TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    category_id INTEGER NOT NULL REFERENCES categories(id),
    unit_price_cents INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY,
    customer_label TEXT NOT NULL,
    status TEXT NOT NULL,
    placed_on TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS order_lines (
    id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL,
    line_total_cents INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS stock_movements (
    id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity_delta INTEGER NOT NULL,
    note TEXT,
    moved_on TEXT NOT NULL
);
"""

SCHEMA_CONTEXT = """
Tables (SQLite, synthetic demo data only):

categories(id, name)
products(id, sku, name, category_id, unit_price_cents)
orders(id, customer_label, status, placed_on)  -- status: draft|paid|fulfilled|cancelled
order_lines(id, order_id, product_id, quantity, line_total_cents)
stock_movements(id, product_id, quantity_delta, note, moved_on)

Shelf quantity for a product = SUM(stock_movements.quantity_delta) for that product_id.
Prices are integer cents. Dates are ISO strings (YYYY-MM-DD).
""".strip()


def ensure_demo_database(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.executescript(DDL)
        count = conn.execute("SELECT COUNT(*) FROM products").fetchone()
        if count is not None and count[0] > 0:
            return
        _seed(conn)
        conn.commit()


def _seed(conn: sqlite3.Connection) -> None:
    categories = [("Fasteners",), ("Packaging",), ("Tools",)]
    conn.executemany("INSERT INTO categories(name) VALUES (?)", categories)

    products = [
        ("SKU-100", "M8 Bolt Pack", 1, 4500),
        ("SKU-200", "Packing Tape Roll", 2, 1200),
        ("SKU-300", "Box Cutter", 3, 8900),
        ("SKU-400", "Bubble Wrap Bundle", 2, 5600),
    ]
    conn.executemany(
        "INSERT INTO products(sku, name, category_id, unit_price_cents) VALUES (?,?,?,?)",
        products,
    )

    orders = [
        ("Demo buyer A", "paid", "2026-11-01"),
        ("Demo buyer B", "fulfilled", "2026-11-05"),
        ("Demo buyer C", "cancelled", "2026-11-08"),
    ]
    conn.executemany(
        "INSERT INTO orders(customer_label, status, placed_on) VALUES (?,?,?)",
        orders,
    )

    lines = [
        (1, 1, 4, 18000),
        (1, 2, 6, 7200),
        (2, 3, 2, 17800),
        (2, 4, 1, 5600),
    ]
    conn.executemany(
        "INSERT INTO order_lines(order_id, product_id, quantity, line_total_cents) "
        "VALUES (?,?,?,?)",
        lines,
    )

    movements = [
        (1, 120, "Opening stock", "2026-10-01"),
        (1, -8, "Pick for order 1", "2026-11-02"),
        (2, 80, "Restock", "2026-10-15"),
        (2, -6, "Pick for order 1", "2026-11-02"),
        (3, 40, "Opening stock", "2026-10-01"),
        (3, -2, "Pick for order 2", "2026-11-06"),
        (4, 25, "Restock", "2026-10-20"),
        (4, -1, "Pick for order 2", "2026-11-06"),
    ]
    conn.executemany(
        "INSERT INTO stock_movements(product_id, quantity_delta, note, moved_on) VALUES (?,?,?,?)",
        movements,
    )