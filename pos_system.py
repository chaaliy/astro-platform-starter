"""
Point of Sale (POS) System with GUI and SQLite backend.

This script provides a complete POS application using tkinter for the GUI and
SQLite for persistent storage. It includes product management and sales
processing features. Written with an object-oriented design for clarity and
extensibility.
"""
from __future__ import annotations

import json
import os
import platform
import sqlite3
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk


DB_FILE = Path("pos_system.db")


PALETTE = {
    "bg": "#f3f4ff",
    "surface": "#ffffff",
    "surface_alt": "#ecf2ff",
    "primary": "#6366f1",
    "primary_dark": "#4f46e5",
    "accent": "#f97316",
    "text": "#1f2937",
    "muted": "#64748b",
    "hero_fg": "#eef2ff",
    "hero_muted": "#c7d2fe",
}

FONT_FAMILY = "Segoe UI"


@dataclass
class Product:
    """Represents a product record."""

    product_id: str
    name: str
    price: float
    stock: int


@dataclass
class SaleRecord:
    """Represents a recorded sale."""

    sale_id: int
    timestamp: datetime
    subtotal: float
    total: float
    items: List[Dict[str, Any]]


class DatabaseManager:
    """Handles all interactions with the SQLite database."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._ensure_database()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_database(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS products (
                    product_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    price REAL NOT NULL CHECK(price >= 0),
                    stock INTEGER NOT NULL CHECK(stock >= 0)
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS sales_log (
                    sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    subtotal REAL NOT NULL,
                    tax REAL NOT NULL,
                    total REAL NOT NULL,
                    items TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def add_product(self, product: Product) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO products (product_id, name, price, stock)
                VALUES (?, ?, ?, ?)
                """,
                (product.product_id, product.name, product.price, product.stock),
            )
            conn.commit()

    def update_product(self, product: Product) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE products
                SET name = ?, price = ?, stock = ?
                WHERE product_id = ?
                """,
                (product.name, product.price, product.stock, product.product_id),
            )
            if cursor.rowcount == 0:
                raise ValueError("Product not found for update")
            conn.commit()

    def get_product(self, product_id: str) -> Optional[Product]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT product_id, name, price, stock FROM products WHERE product_id = ?",
                (product_id,),
            )
            row = cursor.fetchone()
            if row:
                return Product(
                    product_id=row["product_id"],
                    name=row["name"],
                    price=float(row["price"]),
                    stock=int(row["stock"]),
                )
            return None

    def list_products(self) -> List[Product]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT product_id, name, price, stock FROM products ORDER BY product_id"
            )
            rows = cursor.fetchall()
            return [
                Product(
                    product_id=row["product_id"],
                    name=row["name"],
                    price=float(row["price"]),
                    stock=int(row["stock"]),
                )
                for row in rows
            ]

    def update_stock(self, product_id: str, new_stock: int) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE products SET stock = ? WHERE product_id = ?",
                (new_stock, product_id),
            )
            if cursor.rowcount == 0:
                raise ValueError("Product not found when updating stock")
            conn.commit()

    def log_sale(
        self,
        subtotal: float,
        tax: float,
        total: float,
        items: List[Dict[str, Any]],
    ) -> SaleRecord:
        timestamp = datetime.utcnow()
        items_payload = json.dumps(items)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO sales_log (timestamp, subtotal, tax, total, items)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    timestamp.isoformat(timespec="seconds"),
                    subtotal,
                    tax,
                    total,
                    items_payload,
                ),
            )
            conn.commit()
            sale_id = cursor.lastrowid

        return SaleRecord(
            sale_id=sale_id,
            timestamp=timestamp,
            subtotal=subtotal,
            total=total,
            items=items,
        )

    def list_sales(self, limit: Optional[int] = None) -> List[SaleRecord]:
        query = (
            "SELECT sale_id, timestamp, subtotal, total, items FROM sales_log "
            "ORDER BY datetime(timestamp) DESC"
        )
        params: tuple = ()
        if limit is not None:
            query += " LIMIT ?"
            params = (limit,)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

        sales: List[SaleRecord] = []
        for row in rows:
            timestamp_str: str = row["timestamp"]
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
            except ValueError:
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            items = json.loads(row["items"]) if row["items"] else []
            sales.append(
                SaleRecord(
                    sale_id=int(row["sale_id"]),
                    timestamp=timestamp,
                    subtotal=float(row["subtotal"]),
                    total=float(row["total"]),
                    items=items,
                )
            )

        return sales


class ProductManagerFrame(ttk.Frame):
    """GUI for managing product inventory."""

    def __init__(self, parent: tk.Widget, db: DatabaseManager, on_inventory_change) -> None:
        super().__init__(parent, padding=20, style="Background.TFrame")
        self.db = db
        self.on_inventory_change = on_inventory_change
        self.summary_var = tk.StringVar(value="No products in inventory yet.")
        self.product_id_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.price_var = tk.StringVar()
        self.stock_var = tk.StringVar()

        self.container = ttk.Frame(self, style="Background.TFrame")
        self.container.grid(row=0, column=0, sticky="nsew")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_columnconfigure(1, weight=1)
        self.container.grid_rowconfigure(1, weight=1)

        self._build_ui()
        self.refresh_products()

    def _build_ui(self) -> None:
        container = self.container

        hero = ttk.Frame(container, style="Hero.TFrame", padding=(24, 18))
        hero.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 24))
        hero.grid_columnconfigure(0, weight=1)

        ttk.Label(hero, text="Inventory Studio", style="HeroTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            hero,
            text="Add, update, and monitor your catalog with instant insights.",
            style="HeroSubtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))
        ttk.Label(hero, textvariable=self.summary_var, style="HeroStat.TLabel").grid(
            row=2, column=0, sticky="w", pady=(16, 0)
        )

        form_card = ttk.Frame(container, style="Card.TFrame", padding=24)
        form_card.grid(row=1, column=0, sticky="nsew", padx=(0, 16))
        form_card.grid_columnconfigure(1, weight=1)

        ttk.Label(form_card, text="New or Existing Product", style="SectionTitle.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk.Separator(form_card).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 16))

        ttk.Label(form_card, text="Product ID", style="FieldLabel.TLabel").grid(
            row=2, column=0, sticky="w"
        )
        ttk.Entry(form_card, textvariable=self.product_id_var).grid(
            row=2, column=1, sticky="ew", pady=(0, 12)
        )

        ttk.Label(form_card, text="Name", style="FieldLabel.TLabel").grid(
            row=3, column=0, sticky="w"
        )
        ttk.Entry(form_card, textvariable=self.name_var).grid(
            row=3, column=1, sticky="ew", pady=(0, 12)
        )

        ttk.Label(form_card, text="Price", style="FieldLabel.TLabel").grid(
            row=4, column=0, sticky="w"
        )
        ttk.Entry(form_card, textvariable=self.price_var).grid(
            row=4, column=1, sticky="ew", pady=(0, 12)
        )

        ttk.Label(form_card, text="Stock", style="FieldLabel.TLabel").grid(
            row=5, column=0, sticky="w"
        )
        ttk.Entry(form_card, textvariable=self.stock_var).grid(
            row=5, column=1, sticky="ew", pady=(0, 16)
        )

        actions = ttk.Frame(form_card, style="Card.TFrame")
        actions.grid(row=6, column=0, columnspan=2, sticky="ew")
        actions.grid_columnconfigure(0, weight=1)
        actions.grid_columnconfigure(1, weight=1)
        actions.grid_columnconfigure(2, weight=1)
        actions.grid_columnconfigure(3, weight=1)

        ttk.Button(
            actions,
            text="Add Product",
            command=self.add_product,
            style="Accent.TButton",
        ).grid(row=0, column=0, sticky="ew", padx=(0, 12))
        ttk.Button(
            actions,
            text="Update",
            command=self.update_product,
            style="Secondary.TButton",
        ).grid(row=0, column=1, sticky="ew", padx=(0, 12))
        ttk.Button(
            actions,
            text="Clear",
            command=self.clear_form,
            style="Secondary.TButton",
        ).grid(row=0, column=2, sticky="ew", padx=(0, 12))
        ttk.Button(
            actions,
            text="Refresh",
            command=self.refresh_products,
            style="Secondary.TButton",
        ).grid(row=0, column=3, sticky="ew")

        inventory_card = ttk.Frame(container, style="Card.TFrame", padding=24)
        inventory_card.grid(row=1, column=1, sticky="nsew")
        inventory_card.grid_rowconfigure(1, weight=1)
        inventory_card.grid_columnconfigure(0, weight=1)

        ttk.Label(inventory_card, text="Inventory", style="SectionTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Separator(inventory_card).grid(row=1, column=0, sticky="ew", pady=(8, 16))

        columns = ("product_id", "name", "price", "stock")
        self.tree = ttk.Treeview(
            inventory_card,
            columns=columns,
            show="headings",
            height=10,
        )
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            anchor = tk.CENTER if col != "name" else tk.W
            width = 120 if col != "name" else 220
            self.tree.column(col, width=width, anchor=anchor)
        self.tree.configure(selectmode="browse")
        self.tree.grid(row=2, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(inventory_card, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=2, column=1, sticky="ns")

        self.tree.tag_configure("evenrow", background=PALETTE["surface"])
        self.tree.tag_configure("oddrow", background=PALETTE["surface_alt"])

        self.tree.bind("<Double-1>", self._on_tree_select)

    def _on_tree_select(self, event) -> None:
        selected_item = self.tree.selection()
        if not selected_item:
            return
        item_values = self.tree.item(selected_item[0], "values")
        self.product_id_var.set(item_values[0])
        self.name_var.set(item_values[1])
        self.price_var.set(item_values[2])
        self.stock_var.set(item_values[3])

    def _parse_product_from_form(self) -> Product:
        product_id = self.product_id_var.get().strip()
        name = self.name_var.get().strip()

        try:
            price = float(self.price_var.get())
            stock = int(self.stock_var.get())
        except ValueError as exc:
            raise ValueError("Price must be a number and stock must be an integer") from exc

        if price < 0 or stock < 0:
            raise ValueError("Price and stock must be non-negative")

        if not product_id or not name:
            raise ValueError("Product ID and name are required")

        return Product(product_id=product_id, name=name, price=price, stock=stock)

    def add_product(self) -> None:
        try:
            product = self._parse_product_from_form()
            self.db.add_product(product)
            messagebox.showinfo("Success", "Product added successfully")
            self.refresh_products()
            self.clear_form()
            self.on_inventory_change()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Product ID already exists")
        except ValueError as exc:
            messagebox.showerror("Error", str(exc))

    def update_product(self) -> None:
        try:
            product = self._parse_product_from_form()
            self.db.update_product(product)
            messagebox.showinfo("Success", "Product updated successfully")
            self.refresh_products()
            self.clear_form()
            self.on_inventory_change()
        except ValueError as exc:
            messagebox.showerror("Error", str(exc))

    def clear_form(self) -> None:
        self.product_id_var.set("")
        self.name_var.set("")
        self.price_var.set("")
        self.stock_var.set("")

    def refresh_products(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        products = self.db.list_products()
        for index, product in enumerate(products):
            tag = "evenrow" if index % 2 == 0 else "oddrow"
            self.tree.insert(
                "",
                tk.END,
                values=(product.product_id, product.name, f"{product.price:.2f}", product.stock),
                tags=(tag,),
            )

        if products:
            total_stock = sum(product.stock for product in products)
            total_value = sum(product.stock * product.price for product in products)
            summary = (
                f"{len(products)} products • {total_stock} units available • "
                f"Inventory value ${total_value:.2f}"
            )
        else:
            summary = "No products in inventory yet. Add your first item to get started."
        self.summary_var.set(summary)


class SalesFrame(ttk.Frame):
    """GUI for handling the sales process."""

    def __init__(
        self,
        parent: tk.Widget,
        db: DatabaseManager,
        inventory_provider,
        on_sale_complete,
    ) -> None:
        super().__init__(parent, padding=20, style="Background.TFrame")
        self.db = db
        self.inventory_provider = inventory_provider
        self.on_sale_complete = on_sale_complete
        self.cart: Dict[str, Dict[str, float]] = {}
        self.last_sale: Optional[SaleRecord] = None
        self.cart_summary_var = tk.StringVar(value="Cart is empty.")
        self.status_var = tk.StringVar(value="Ready to build a cart.")

        self.product_id_var = tk.StringVar()
        self.quantity_var = tk.StringVar(value="1")
        self.subtotal_var = tk.StringVar(value="0.00")
        self.total_var = tk.StringVar(value="0.00")

        self.container = ttk.Frame(self, style="Background.TFrame")
        self.container.grid(row=0, column=0, sticky="nsew")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(1, weight=1)

        self._build_ui()
        self._refresh_inventory_cache()

    def _build_ui(self) -> None:
        container = self.container

        hero = ttk.Frame(container, style="Hero.TFrame", padding=(24, 18))
        hero.grid(row=0, column=0, sticky="ew", pady=(0, 24))
        hero.grid_columnconfigure(0, weight=1)

        ttk.Label(hero, text="Sales Checkout", style="HeroTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            hero,
            text="Scan items into the cart, monitor totals, and wrap receipts instantly.",
            style="HeroSubtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))
        ttk.Label(hero, textvariable=self.cart_summary_var, style="HeroStat.TLabel").grid(
            row=2, column=0, sticky="w", pady=(16, 0)
        )

        workflow = ttk.Frame(container, style="Background.TFrame")
        workflow.grid(row=1, column=0, sticky="nsew")
        workflow.grid_columnconfigure(0, weight=1)
        workflow.grid_columnconfigure(1, weight=1)
        workflow.grid_rowconfigure(1, weight=1)

        scanner_card = ttk.Frame(workflow, style="Card.TFrame", padding=24)
        scanner_card.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        scanner_card.grid_columnconfigure(1, weight=1)

        ttk.Label(scanner_card, text="Quick Add", style="SectionTitle.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk.Separator(scanner_card).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 16))

        ttk.Label(scanner_card, text="Product ID", style="FieldLabel.TLabel").grid(
            row=2, column=0, sticky="w"
        )
        ttk.Entry(scanner_card, textvariable=self.product_id_var).grid(
            row=2, column=1, sticky="ew", pady=(0, 12)
        )

        ttk.Label(scanner_card, text="Quantity", style="FieldLabel.TLabel").grid(
            row=3, column=0, sticky="w"
        )
        ttk.Entry(scanner_card, textvariable=self.quantity_var).grid(
            row=3, column=1, sticky="ew", pady=(0, 12)
        )

        ttk.Button(
            scanner_card,
            text="Add to Cart",
            command=self.add_to_cart,
            style="Accent.TButton",
        ).grid(row=4, column=0, columnspan=2, sticky="ew")

        secondary_actions = ttk.Frame(scanner_card, style="Background.TFrame")
        secondary_actions.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(16, 0))
        secondary_actions.grid_columnconfigure(0, weight=1)
        secondary_actions.grid_columnconfigure(1, weight=1)

        ttk.Button(
            secondary_actions,
            text="Remove Selected",
            command=self.remove_selected_item,
            style="Secondary.TButton",
        ).grid(row=0, column=0, sticky="ew", padx=(0, 12))
        ttk.Button(
            secondary_actions,
            text="Clear Cart",
            command=self.clear_cart,
            style="Secondary.TButton",
        ).grid(row=0, column=1, sticky="ew")

        totals_card = ttk.Frame(workflow, style="Card.TFrame", padding=24)
        totals_card.grid(row=0, column=1, sticky="nsew")
        totals_card.grid_columnconfigure(1, weight=1)

        ttk.Label(totals_card, text="Checkout Summary", style="SectionTitle.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk.Separator(totals_card).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 16))

        ttk.Label(totals_card, text="Subtotal", style="FieldLabel.TLabel").grid(
            row=2, column=0, sticky="w"
        )
        ttk.Label(totals_card, textvariable=self.subtotal_var, style="TotalsValue.TLabel").grid(
            row=2, column=1, sticky=tk.E
        )

        ttk.Label(totals_card, text="Balance Due", style="FieldLabel.TLabel").grid(
            row=3, column=0, sticky="w"
        )
        ttk.Label(totals_card, textvariable=self.total_var, style="TotalsValueAccent.TLabel").grid(
            row=3, column=1, sticky=tk.E
        )

        ttk.Button(
            totals_card,
            text="Finalize Sale",
            command=self.finalize_sale,
            style="Accent.TButton",
        ).grid(row=4, column=0, columnspan=2, sticky="ew", pady=(16, 8))

        self.print_button = ttk.Button(
            totals_card,
            text="Print Invoice",
            command=self.print_invoice,
            style="Secondary.TButton",
        )
        self.print_button.grid(row=5, column=0, columnspan=2, sticky="ew")
        self.print_button.state(["disabled"])

        cart_card = ttk.Frame(workflow, style="Card.TFrame", padding=24)
        cart_card.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(24, 0))
        cart_card.grid_rowconfigure(2, weight=1)
        cart_card.grid_columnconfigure(0, weight=1)

        ttk.Label(cart_card, text="Active Cart", style="SectionTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Separator(cart_card).grid(row=1, column=0, sticky="ew", pady=(8, 16))

        columns = ("product_id", "name", "price", "quantity", "line_total")
        self.tree = ttk.Treeview(cart_card, columns=columns, show="headings", height=10)
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            anchor = tk.CENTER if col != "name" else tk.W
            width = 110 if col not in {"name", "line_total"} else 150
            if col == "name":
                width = 240
            self.tree.column(col, anchor=anchor, width=width)
        self.tree.configure(selectmode="browse")
        self.tree.grid(row=2, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(cart_card, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=2, column=1, sticky="ns")

        self.tree.tag_configure("evenrow", background=PALETTE["surface"])
        self.tree.tag_configure("oddrow", background=PALETTE["surface_alt"])
        self.tree.bind("<Delete>", lambda _event: self.remove_selected_item())
        self.tree.bind("<Double-1>", lambda _event: self.remove_selected_item())

        self.status_label = ttk.Label(container, textvariable=self.status_var, style="Status.TLabel")
        self.status_label.grid(row=2, column=0, sticky="w", pady=(24, 0))

    def _refresh_inventory_cache(self) -> None:
        self.inventory_cache = {product.product_id: product for product in self.inventory_provider()}

    def _set_status(self, message: str, accent: bool = False) -> None:
        self.status_var.set(message)
        style = "StatusAccent.TLabel" if accent else "Status.TLabel"
        self.status_label.configure(style=style)

    def add_to_cart(self) -> None:
        product_id = self.product_id_var.get().strip()
        try:
            quantity = int(self.quantity_var.get())
            if quantity <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid quantity", "Quantity must be a positive integer")
            self._set_status("Quantity must be a positive integer.")
            return

        if product_id not in self.inventory_cache:
            messagebox.showerror("Not found", "Product ID not found in inventory")
            self._set_status("Product ID not found in inventory.")
            return

        product = self.inventory_cache[product_id]
        if quantity > product.stock:
            messagebox.showerror(
                "Insufficient stock",
                f"Only {product.stock} units available for {product.name}",
            )
            self._set_status(f"Only {product.stock} units of {product.name} available.")
            return

        if product_id in self.cart:
            new_qty = self.cart[product_id]["quantity"] + quantity
            if new_qty > product.stock:
                messagebox.showerror(
                    "Insufficient stock",
                    f"Adding exceeds available stock ({product.stock}) for {product.name}",
                )
                self._set_status(f"Stock limit reached for {product.name}.")
                return
            self.cart[product_id]["quantity"] = new_qty
            self.cart[product_id]["line_total"] = new_qty * product.price
        else:
            self.cart[product_id] = {
                "name": product.name,
                "price": product.price,
                "quantity": quantity,
                "line_total": quantity * product.price,
            }

        self._populate_cart_tree()
        self._update_totals()
        self._set_status(f"Added {quantity} × {product.name} to cart.", accent=True)
        self.product_id_var.set("")
        self.quantity_var.set("1")

    def _populate_cart_tree(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for index, (product_id, data) in enumerate(self.cart.items()):
            tag = "evenrow" if index % 2 == 0 else "oddrow"
            self.tree.insert(
                "",
                tk.END,
                values=(
                    product_id,
                    data["name"],
                    f"{data['price']:.2f}",
                    data["quantity"],
                    f"{data['line_total']:.2f}",
                ),
                tags=(tag,),
            )

    def _update_totals(self) -> None:
        subtotal = sum(item["line_total"] for item in self.cart.values())
        total = subtotal
        self.subtotal_var.set(f"{subtotal:.2f}")
        self.total_var.set(f"{total:.2f}")

        if self.cart:
            item_count = sum(item["quantity"] for item in self.cart.values())
            label = "item" if item_count == 1 else "items"
            self.cart_summary_var.set(f"{item_count} {label} • ${total:.2f}")
        else:
            self.cart_summary_var.set("Cart is empty.")

    def clear_cart(self, notify: bool = True) -> None:
        self.cart.clear()
        self._populate_cart_tree()
        self._update_totals()
        if notify:
            self._set_status("Cart cleared.")

    def remove_selected_item(self) -> None:
        selection = self.tree.selection()
        if not selection:
            self._set_status("Select an item to remove from the cart.")
            return
        product_id = self.tree.item(selection[0], "values")[0]
        if product_id in self.cart:
            removed_name = self.cart[product_id]["name"]
            del self.cart[product_id]
            self._populate_cart_tree()
            self._update_totals()
            self._set_status(f"Removed {removed_name} from the cart.")
        else:
            self._set_status("Selected item could not be found.")

    def finalize_sale(self) -> None:
        if not self.cart:
            messagebox.showwarning("Empty cart", "No items in cart to finalize")
            self._set_status("Add items to the cart before finalizing.")
            return

        # Refresh inventory to ensure latest stock counts
        self._refresh_inventory_cache()

        # Validate stock availability before committing
        for product_id, item in self.cart.items():
            product = self.inventory_cache.get(product_id)
            if product is None:
                messagebox.showerror("Error", f"Product {product_id} no longer exists")
                self._set_status(f"Product {product_id} no longer exists.")
                return
            if item["quantity"] > product.stock:
                messagebox.showerror(
                    "Insufficient stock",
                    f"Only {product.stock} units available for {product.name}",
                )
                self._set_status(f"Only {product.stock} units of {product.name} remaining.")
                return

        subtotal = sum(item["line_total"] for item in self.cart.values())
        total = subtotal
        finalized_at = datetime.utcnow()
        items_payload = [
            {
                "product_id": product_id,
                "name": item["name"],
                "quantity": item["quantity"],
                "price": item["price"],
                "line_total": item["line_total"],
            }
            for product_id, item in self.cart.items()
        ]

        # Update stock and log sale in a transaction
        try:
            with self.db._get_connection() as conn:  # using private method for transaction control
                cursor = conn.cursor()
                for product_id, item in self.cart.items():
                    product = self.inventory_cache[product_id]
                    new_stock = product.stock - item["quantity"]
                    cursor.execute(
                        "UPDATE products SET stock = ? WHERE product_id = ?",
                        (new_stock, product_id),
                    )
                cursor.execute(
                    """
                    INSERT INTO sales_log (timestamp, subtotal, tax, total, items)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        finalized_at.isoformat(timespec="seconds"),
                        subtotal,
                        0.0,
                        total,
                        json.dumps(items_payload),
                    ),
                )
                sale_id = cursor.lastrowid
                conn.commit()
        except sqlite3.DatabaseError as exc:
            messagebox.showerror("Database error", f"Failed to finalize sale: {exc}")
            self._set_status("Failed to finalize sale. Please try again.")
            return

        sale_record = SaleRecord(
            sale_id=sale_id,
            timestamp=finalized_at,
            subtotal=subtotal,
            total=total,
            items=items_payload,
        )

        self.last_sale = sale_record
        self.print_button.state(["!disabled"])

        messagebox.showinfo("Sale complete", f"Total charged: ${total:.2f}")
        self.clear_cart(notify=False)
        self._refresh_inventory_cache()
        self._set_status(
            f"Sale completed at {datetime.now().strftime('%I:%M:%S %p').lstrip('0')} • Invoice ready to print.",
            accent=True,
        )

        if self.on_sale_complete:
            try:
                self.on_sale_complete(sale_record)
            except Exception:  # pragma: no cover - guard callbacks
                pass

    def print_invoice(self) -> None:
        if not self.last_sale:
            messagebox.showinfo("No invoice", "Complete a sale to print an invoice.")
            return

        InvoicePreview(self, format_invoice(self.last_sale))


class PurchaseHistoryFrame(ttk.Frame):
    """GUI for reviewing and exporting past sales."""

    def __init__(self, parent: tk.Widget, db: DatabaseManager) -> None:
        super().__init__(parent, padding=20, style="Background.TFrame")
        self.db = db
        self.sales: List[SaleRecord] = []
        self.summary_var = tk.StringVar(value="No purchases recorded yet.")

        self.container = ttk.Frame(self, style="Background.TFrame")
        self.container.grid(row=0, column=0, sticky="nsew")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.container.grid_rowconfigure(1, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self._build_ui()
        self.refresh_history()

    def _build_ui(self) -> None:
        container = self.container

        hero = ttk.Frame(container, style="Hero.TFrame", padding=(24, 18))
        hero.grid(row=0, column=0, sticky="ew", pady=(0, 24))
        hero.grid_columnconfigure(0, weight=1)

        ttk.Label(hero, text="Purchase History", style="HeroTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            hero,
            text="Browse previous receipts, revisit totals, and reprint invoices on demand.",
            style="HeroSubtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))
        ttk.Label(hero, textvariable=self.summary_var, style="HeroStat.TLabel").grid(
            row=2, column=0, sticky="w", pady=(16, 0)
        )

        body = ttk.Frame(container, style="Background.TFrame")
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=2)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        history_card = ttk.Frame(body, style="Card.TFrame", padding=24)
        history_card.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        history_card.grid_rowconfigure(2, weight=1)
        history_card.grid_columnconfigure(0, weight=1)

        header = ttk.Frame(history_card, style="Background.TFrame")
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ttk.Label(header, text="Recent Sales", style="SectionTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Button(
            header,
            text="Refresh",
            command=self.refresh_history,
            style="Secondary.TButton",
        ).grid(row=0, column=1, sticky="e")

        ttk.Separator(history_card).grid(row=1, column=0, sticky="ew", pady=(8, 16))

        columns = ("sale_id", "timestamp", "items", "subtotal", "total")
        self.tree = ttk.Treeview(history_card, columns=columns, show="headings", height=12)
        headings = {
            "sale_id": "Sale #",
            "timestamp": "Completed",
            "items": "Items",
            "subtotal": "Subtotal",
            "total": "Total",
        }
        widths = {
            "sale_id": 80,
            "timestamp": 160,
            "items": 80,
            "subtotal": 100,
            "total": 100,
        }
        for column in columns:
            self.tree.heading(column, text=headings[column])
            anchor = tk.CENTER if column != "timestamp" else tk.W
            self.tree.column(column, width=widths[column], anchor=anchor)
        self.tree.grid(row=2, column=0, sticky="nsew")
        self.tree.configure(selectmode="browse")
        self.tree.tag_configure("evenrow", background=PALETTE["surface"])
        self.tree.tag_configure("oddrow", background=PALETTE["surface_alt"])
        self.tree.bind("<<TreeviewSelect>>", lambda _event: self._update_details())

        scroll = ttk.Scrollbar(history_card, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.grid(row=2, column=1, sticky="ns")

        details_card = ttk.Frame(body, style="Card.TFrame", padding=24)
        details_card.grid(row=0, column=1, sticky="nsew")
        details_card.grid_rowconfigure(2, weight=1)
        details_card.grid_columnconfigure(0, weight=1)

        ttk.Label(details_card, text="Sale Details", style="SectionTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Separator(details_card).grid(row=1, column=0, sticky="ew", pady=(8, 16))

        self.detail_text = tk.Text(
            details_card,
            height=14,
            wrap="word",
            background=PALETTE["surface"],
            foreground=PALETTE["text"],
            font=(FONT_FAMILY, 11),
            relief="flat",
            borderwidth=0,
        )
        self.detail_text.grid(row=2, column=0, sticky="nsew")
        self.detail_text.configure(state="disabled")

        detail_scroll = ttk.Scrollbar(details_card, orient=tk.VERTICAL, command=self.detail_text.yview)
        self.detail_text.configure(yscrollcommand=detail_scroll.set)
        detail_scroll.grid(row=2, column=1, sticky="ns")

        self.view_button = ttk.Button(
            details_card,
            text="Open Invoice",
            command=self.open_invoice,
            style="Secondary.TButton",
        )
        self.view_button.grid(row=3, column=0, sticky="ew", pady=(16, 0))
        self.view_button.state(["disabled"])

    def refresh_history(self) -> None:
        self.sales = self.db.list_sales()
        for item in self.tree.get_children():
            self.tree.delete(item)

        total_revenue = 0.0
        for index, sale in enumerate(self.sales):
            total_revenue += sale.total
            tag = "evenrow" if index % 2 == 0 else "oddrow"
            self.tree.insert(
                "",
                tk.END,
                values=(
                    sale.sale_id,
                    sale.timestamp.strftime("%Y-%m-%d %H:%M"),
                    sum(item["quantity"] for item in sale.items),
                    f"{sale.subtotal:.2f}",
                    f"{sale.total:.2f}",
                ),
                tags=(tag,),
            )

        if self.sales:
            summary = (
                f"{len(self.sales)} sales • ${total_revenue:.2f} revenue captured"
            )
        else:
            summary = "No purchases recorded yet. Completed sales will appear here."
        self.summary_var.set(summary)
        self._update_details()

    def _get_selected_sale(self) -> Optional[SaleRecord]:
        selection = self.tree.selection()
        if not selection:
            return None
        sale_id = int(self.tree.item(selection[0], "values")[0])
        for sale in self.sales:
            if sale.sale_id == sale_id:
                return sale
        return None

    def _update_details(self) -> None:
        sale = self._get_selected_sale()
        if sale is None:
            self.view_button.state(["disabled"])
            self.detail_text.configure(state="normal")
            self.detail_text.delete("1.0", tk.END)
            self.detail_text.insert(tk.END, "Select a sale to see its details.")
            self.detail_text.configure(state="disabled")
            return

        self.view_button.state(["!disabled"])
        details_lines = [
            f"Sale #{sale.sale_id}",
            sale.timestamp.strftime("%B %d, %Y • %I:%M %p").lstrip("0").replace(" 0", " "),
            "",
        ]
        for item in sale.items:
            details_lines.append(
                f"{item['quantity']} × {item['name']} (@ ${item['price']:.2f}) = ${item['line_total']:.2f}"
            )
        details_lines.append("")
        details_lines.append(f"Subtotal: ${sale.subtotal:.2f}")
        details_lines.append(f"Balance Due: ${sale.total:.2f}")

        self.detail_text.configure(state="normal")
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.insert(tk.END, "\n".join(details_lines))
        self.detail_text.configure(state="disabled")

    def open_invoice(self) -> None:
        sale = self._get_selected_sale()
        if sale is None:
            messagebox.showinfo("No sale selected", "Select a sale to open its invoice.")
            return

        InvoicePreview(self, format_invoice(sale))


def format_invoice(sale: SaleRecord) -> str:
    """Create a printable invoice string from a sale."""

    header_width = 72
    lines = [
        "POS System Invoice".center(header_width),
        "=" * header_width,
        f"Sale #: {sale.sale_id}",
        f"Completed: {sale.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * header_width,
        f"{'ID':<10}{'Product':<26}{'Qty':>5}{'Price':>16}{'Total':>15}",
        "-" * header_width,
    ]

    for item in sale.items or []:
        name = str(item.get("name", ""))
        display_name = (name[:23] + "...") if len(name) > 26 else name
        quantity = int(item.get("quantity", 0))
        price = float(item.get("price", 0.0))
        line_total = float(item.get("line_total", quantity * price))
        price_str = f"${price:.2f}"
        total_str = f"${line_total:.2f}"
        lines.append(
            f"{str(item.get('product_id', '')):<10}"
            f"{display_name:<26}"
            f"{quantity:>5}"
            f"{price_str:>16}"
            f"{total_str:>15}"
        )

    lines.append("-" * header_width)
    subtotal_str = f"${sale.subtotal:.2f}"
    total_str = f"${sale.total:.2f}"
    lines.append(f"{'Subtotal:':>56}{subtotal_str:>16}")
    lines.append(f"{'Balance Due:':>56}{total_str:>16}")
    lines.append("=" * header_width)
    lines.append("Thank you for shopping with us!")

    return "\n".join(lines)


class InvoicePreview(tk.Toplevel):
    """Preview window that supports saving or printing invoices."""

    def __init__(self, parent: tk.Widget, invoice_text: str) -> None:
        super().__init__(parent)
        self.title("Invoice Preview")
        self.configure(bg=PALETTE["bg"])
        self.invoice_text = invoice_text

        self.transient(parent.winfo_toplevel())
        self.grab_set()
        self.resizable(True, True)
        self.minsize(520, 500)

        container = ttk.Frame(self, padding=24, style="Background.TFrame")
        container.grid(row=0, column=0, sticky="nsew")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(1, weight=1)

        ttk.Label(container, text="Invoice Preview", style="SectionTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )

        text_frame = ttk.Frame(container, style="Card.TFrame", padding=0)
        text_frame.grid(row=1, column=0, sticky="nsew", pady=(16, 16))
        text_frame.grid_columnconfigure(0, weight=1)
        text_frame.grid_rowconfigure(0, weight=1)

        text_widget = tk.Text(
            text_frame,
            wrap="none",
            font=(FONT_FAMILY, 11),
            background=PALETTE["surface"],
            foreground=PALETTE["text"],
            relief="flat",
            borderwidth=0,
        )
        text_widget.insert("1.0", invoice_text)
        text_widget.configure(state="disabled")
        text_widget.grid(row=0, column=0, sticky="nsew")

        text_scroll = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=text_scroll.set)
        text_scroll.grid(row=0, column=1, sticky="ns")

        button_bar = ttk.Frame(container, style="Background.TFrame")
        button_bar.grid(row=2, column=0, sticky="ew")
        for index in range(3):
            button_bar.grid_columnconfigure(index, weight=1)

        ttk.Button(
            button_bar,
            text="Save As…",
            command=self._save_invoice,
            style="Secondary.TButton",
        ).grid(row=0, column=0, sticky="ew", padx=(0, 12))
        ttk.Button(
            button_bar,
            text="Print",
            command=self._send_to_printer,
            style="Accent.TButton",
        ).grid(row=0, column=1, sticky="ew", padx=(0, 12))
        ttk.Button(
            button_bar,
            text="Close",
            command=self.destroy,
            style="Secondary.TButton",
        ).grid(row=0, column=2, sticky="ew")

    def _save_invoice(self) -> None:
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*")),
            title="Save invoice",
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(self.invoice_text)
        except OSError as exc:
            messagebox.showerror("Save failed", f"Could not save invoice: {exc}")
            return

        messagebox.showinfo("Invoice saved", f"Invoice saved to {file_path}")

    def _send_to_printer(self) -> None:
        tmp_path: Optional[str] = None
        try:
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=".txt", mode="w", encoding="utf-8"
            ) as tmp:
                tmp.write(self.invoice_text)
                tmp_path = tmp.name

            system = platform.system().lower()
            if "windows" in system:
                if hasattr(os, "startfile"):
                    os.startfile(tmp_path, "print")  # type: ignore[attr-defined]
                else:
                    raise RuntimeError("Printing is not supported on this Windows configuration.")
            elif system in {"darwin", "linux"}:
                subprocess.run(["lp", tmp_path], check=True)
            else:
                raise RuntimeError("Printing is not supported on this platform.")

            messagebox.showinfo("Invoice sent", "Invoice sent to the default printer.")
        except FileNotFoundError:
            messagebox.showerror(
                "Print failed",
                "The system printing utility was not found. Save the invoice and print manually.",
            )
        except (OSError, subprocess.CalledProcessError, RuntimeError) as exc:
            messagebox.showerror("Print failed", f"Could not print invoice: {exc}")
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass


class POSApp(tk.Tk):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()
        self.title("POS System")
        self.geometry("1100x720")
        self.configure(bg=PALETTE["bg"])
        self.option_add("*Font", (FONT_FAMILY, 11))

        self.style = ttk.Style(self)
        self._configure_style()

        self.db = DatabaseManager(DB_FILE)
        self._build_ui()

    def _configure_style(self) -> None:
        style = self.style
        if "clam" in style.theme_names():
            style.theme_use("clam")

        style.configure("TFrame", background=PALETTE["bg"])
        style.configure("Background.TFrame", background=PALETTE["bg"])
        style.configure("Card.TFrame", background=PALETTE["surface"], relief="flat", borderwidth=0)
        style.configure("Hero.TFrame", background=PALETTE["primary"], relief="flat", borderwidth=0)

        style.configure("TLabel", background=PALETTE["surface"], foreground=PALETTE["text"], font=(FONT_FAMILY, 11))
        style.configure(
            "SectionTitle.TLabel",
            background=PALETTE["surface"],
            foreground=PALETTE["primary_dark"],
            font=(FONT_FAMILY, 15, "bold"),
        )
        style.configure(
            "FieldLabel.TLabel",
            background=PALETTE["surface"],
            foreground=PALETTE["muted"],
            font=(FONT_FAMILY, 11, "bold"),
        )
        style.configure(
            "HeroTitle.TLabel",
            background=PALETTE["primary"],
            foreground=PALETTE["hero_fg"],
            font=(FONT_FAMILY, 20, "bold"),
        )
        style.configure(
            "HeroSubtitle.TLabel",
            background=PALETTE["primary"],
            foreground=PALETTE["hero_muted"],
            font=(FONT_FAMILY, 12),
        )
        style.configure(
            "HeroStat.TLabel",
            background=PALETTE["primary"],
            foreground=PALETTE["hero_fg"],
            font=(FONT_FAMILY, 11),
        )
        style.configure(
            "TotalsValue.TLabel",
            background=PALETTE["surface"],
            foreground=PALETTE["primary_dark"],
            font=(FONT_FAMILY, 17, "bold"),
        )
        style.configure(
            "TotalsValueAccent.TLabel",
            background=PALETTE["surface"],
            foreground=PALETTE["accent"],
            font=(FONT_FAMILY, 24, "bold"),
        )
        style.configure(
            "Status.TLabel",
            background=PALETTE["bg"],
            foreground=PALETTE["muted"],
            font=(FONT_FAMILY, 10),
        )
        style.configure(
            "StatusAccent.TLabel",
            background=PALETTE["bg"],
            foreground=PALETTE["primary_dark"],
            font=(FONT_FAMILY, 10, "bold"),
        )

        style.configure("TButton", font=(FONT_FAMILY, 11), padding=(14, 8), borderwidth=0)
        style.configure(
            "Accent.TButton",
            background=PALETTE["primary"],
            foreground="#ffffff",
            padding=(16, 10),
        )
        style.map(
            "Accent.TButton",
            background=[("active", PALETTE["primary_dark"]), ("pressed", PALETTE["primary_dark"])],
        )
        style.configure(
            "Secondary.TButton",
            background=PALETTE["surface_alt"],
            foreground=PALETTE["primary_dark"],
            padding=(16, 10),
        )
        style.map(
            "Secondary.TButton",
            background=[("active", PALETTE["primary"]), ("pressed", PALETTE["primary_dark"])],
            foreground=[("active", "#ffffff"), ("pressed", "#ffffff")],
        )

        style.configure(
            "Treeview",
            background=PALETTE["surface"],
            fieldbackground=PALETTE["surface"],
            foreground=PALETTE["text"],
            bordercolor=PALETTE["surface_alt"],
            rowheight=30,
            borderwidth=1,
            font=(FONT_FAMILY, 11),
        )
        style.map(
            "Treeview",
            background=[("selected", PALETTE["primary"])],
            foreground=[("selected", "#ffffff")],
        )
        style.configure(
            "Treeview.Heading",
            background=PALETTE["primary_dark"],
            foreground="#ffffff",
            font=(FONT_FAMILY, 11, "bold"),
            relief="flat",
        )
        style.map("Treeview.Heading", background=[("active", PALETTE["primary"])])

        style.configure("TScrollbar", troughcolor=PALETTE["surface"], background=PALETTE["primary"])

        style.configure("TNotebook", background=PALETTE["bg"], borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=PALETTE["surface_alt"],
            foreground=PALETTE["muted"],
            padding=(16, 8),
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", PALETTE["surface"])],
            foreground=[("selected", PALETTE["primary_dark"])],
        )

    def _build_ui(self) -> None:
        container = ttk.Notebook(self)
        container.pack(fill=tk.BOTH, expand=True)

        self.product_manager = ProductManagerFrame(
            container,
            db=self.db,
            on_inventory_change=self._notify_inventory_change,
        )
        container.add(self.product_manager, text="Products")

        self.sales_frame = SalesFrame(
            container,
            db=self.db,
            inventory_provider=self.db.list_products,
            on_sale_complete=self._handle_sale_complete,
        )
        container.add(self.sales_frame, text="Sales")

        self.history_frame = PurchaseHistoryFrame(container, db=self.db)
        container.add(self.history_frame, text="History")

    def _notify_inventory_change(self) -> None:
        self.sales_frame._refresh_inventory_cache()

    def _handle_sale_complete(self, _sale: SaleRecord) -> None:
        self.history_frame.refresh_history()


def main() -> None:
    app = POSApp()
    app.mainloop()


if __name__ == "__main__":
    main()
