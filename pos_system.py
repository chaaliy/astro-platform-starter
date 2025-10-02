"""
Point of Sale (POS) System with GUI and SQLite backend.

This script provides a complete POS application using tkinter for the GUI and
SQLite for persistent storage. It includes product management and sales
processing features. Written with an object-oriented design for clarity and
extensibility.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import tkinter as tk
from tkinter import messagebox
from tkinter import ttk


DB_FILE = Path("pos_system.db")
TAX_RATE = 0.15


@dataclass
class Product:
    """Represents a product record."""

    product_id: str
    name: str
    price: float
    stock: int


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
        items: List[Dict[str, str]],
    ) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO sales_log (timestamp, subtotal, tax, total, items)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    datetime.utcnow().isoformat(timespec="seconds"),
                    subtotal,
                    tax,
                    total,
                    json.dumps(items),
                ),
            )
            conn.commit()


class ProductManagerFrame(ttk.Frame):
    """GUI for managing product inventory."""

    def __init__(self, parent: tk.Widget, db: DatabaseManager, on_inventory_change) -> None:
        super().__init__(parent, padding=10)
        self.db = db
        self.on_inventory_change = on_inventory_change
        self._build_ui()
        self.refresh_products()

    def _build_ui(self) -> None:
        title = ttk.Label(self, text="Product Management", font=("Arial", 14, "bold"))
        title.grid(row=0, column=0, columnspan=4, pady=(0, 10))

        ttk.Label(self, text="Product ID:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Label(self, text="Name:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Label(self, text="Price:").grid(row=3, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Label(self, text="Stock:").grid(row=4, column=0, sticky=tk.W, padx=(0, 5))

        self.product_id_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.price_var = tk.StringVar()
        self.stock_var = tk.StringVar()

        ttk.Entry(self, textvariable=self.product_id_var).grid(row=1, column=1, sticky="ew", pady=2)
        ttk.Entry(self, textvariable=self.name_var).grid(row=2, column=1, sticky="ew", pady=2)
        ttk.Entry(self, textvariable=self.price_var).grid(row=3, column=1, sticky="ew", pady=2)
        ttk.Entry(self, textvariable=self.stock_var).grid(row=4, column=1, sticky="ew", pady=2)

        add_button = ttk.Button(self, text="Add Product", command=self.add_product)
        add_button.grid(row=5, column=0, pady=(10, 0), sticky="ew")

        update_button = ttk.Button(self, text="Update Product", command=self.update_product)
        update_button.grid(row=5, column=1, pady=(10, 0), sticky="ew")

        clear_button = ttk.Button(self, text="Clear", command=self.clear_form)
        clear_button.grid(row=5, column=2, pady=(10, 0), sticky="ew")

        refresh_button = ttk.Button(self, text="Refresh", command=self.refresh_products)
        refresh_button.grid(row=5, column=3, pady=(10, 0), sticky="ew")

        columns = ("product_id", "name", "price", "stock")
        self.tree = ttk.Treeview(
            self,
            columns=columns,
            show="headings",
            height=8,
        )
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=120, anchor=tk.CENTER)
        self.tree.grid(row=6, column=0, columnspan=4, sticky="nsew", pady=(10, 0))

        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=6, column=4, sticky="ns")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(6, weight=1)

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
        for product in self.db.list_products():
            self.tree.insert(
                "",
                tk.END,
                values=(product.product_id, product.name, f"{product.price:.2f}", product.stock),
            )


class SalesFrame(ttk.Frame):
    """GUI for handling the sales process."""

    def __init__(self, parent: tk.Widget, db: DatabaseManager, inventory_provider) -> None:
        super().__init__(parent, padding=10)
        self.db = db
        self.inventory_provider = inventory_provider
        self.cart: Dict[str, Dict[str, float]] = {}
        self._build_ui()
        self._refresh_inventory_cache()

    def _build_ui(self) -> None:
        title = ttk.Label(self, text="Sales", font=("Arial", 14, "bold"))
        title.grid(row=0, column=0, columnspan=4, pady=(0, 10))

        ttk.Label(self, text="Product ID:").grid(row=1, column=0, sticky=tk.W)
        ttk.Label(self, text="Quantity:").grid(row=2, column=0, sticky=tk.W)

        self.product_id_var = tk.StringVar()
        self.quantity_var = tk.StringVar(value="1")

        ttk.Entry(self, textvariable=self.product_id_var).grid(row=1, column=1, pady=2, sticky="ew")
        ttk.Entry(self, textvariable=self.quantity_var).grid(row=2, column=1, pady=2, sticky="ew")

        add_button = ttk.Button(self, text="Add to Cart", command=self.add_to_cart)
        add_button.grid(row=1, column=2, rowspan=2, padx=(10, 0), sticky="nsew")

        columns = ("product_id", "name", "price", "quantity", "line_total")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=10)
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            anchor = tk.CENTER if col != "name" else tk.W
            width = 100 if col != "name" else 180
            self.tree.column(col, anchor=anchor, width=width)
        self.tree.grid(row=3, column=0, columnspan=4, sticky="nsew", pady=(10, 0))

        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=3, column=4, sticky="ns")

        totals_frame = ttk.Frame(self, padding=(0, 10, 0, 0))
        totals_frame.grid(row=4, column=0, columnspan=4, sticky="ew")
        totals_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(totals_frame, text="Subtotal:").grid(row=0, column=0, sticky=tk.E)
        ttk.Label(totals_frame, text="Tax (15%):").grid(row=1, column=0, sticky=tk.E)
        ttk.Label(totals_frame, text="Total:").grid(row=2, column=0, sticky=tk.E)

        self.subtotal_var = tk.StringVar(value="0.00")
        self.tax_var = tk.StringVar(value="0.00")
        self.total_var = tk.StringVar(value="0.00")

        ttk.Label(totals_frame, textvariable=self.subtotal_var).grid(row=0, column=1, sticky=tk.W)
        ttk.Label(totals_frame, textvariable=self.tax_var).grid(row=1, column=1, sticky=tk.W)
        ttk.Label(totals_frame, textvariable=self.total_var).grid(row=2, column=1, sticky=tk.W)

        finalize_button = ttk.Button(self, text="Finalize Sale", command=self.finalize_sale)
        finalize_button.grid(row=5, column=0, columnspan=2, pady=(10, 0), sticky="ew")

        clear_button = ttk.Button(self, text="Clear Cart", command=self.clear_cart)
        clear_button.grid(row=5, column=2, columnspan=2, pady=(10, 0), sticky="ew")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(3, weight=1)

    def _refresh_inventory_cache(self) -> None:
        self.inventory_cache = {product.product_id: product for product in self.inventory_provider()}

    def add_to_cart(self) -> None:
        product_id = self.product_id_var.get().strip()
        try:
            quantity = int(self.quantity_var.get())
            if quantity <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid quantity", "Quantity must be a positive integer")
            return

        if product_id not in self.inventory_cache:
            messagebox.showerror("Not found", "Product ID not found in inventory")
            return

        product = self.inventory_cache[product_id]
        if quantity > product.stock:
            messagebox.showerror(
                "Insufficient stock",
                f"Only {product.stock} units available for {product.name}",
            )
            return

        if product_id in self.cart:
            new_qty = self.cart[product_id]["quantity"] + quantity
            if new_qty > product.stock:
                messagebox.showerror(
                    "Insufficient stock",
                    f"Adding exceeds available stock ({product.stock}) for {product.name}",
                )
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
        self.product_id_var.set("")
        self.quantity_var.set("1")

    def _populate_cart_tree(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for product_id, data in self.cart.items():
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
            )

    def _update_totals(self) -> None:
        subtotal = sum(item["line_total"] for item in self.cart.values())
        tax = subtotal * TAX_RATE
        total = subtotal + tax
        self.subtotal_var.set(f"{subtotal:.2f}")
        self.tax_var.set(f"{tax:.2f}")
        self.total_var.set(f"{total:.2f}")

    def clear_cart(self) -> None:
        self.cart.clear()
        self._populate_cart_tree()
        self._update_totals()

    def finalize_sale(self) -> None:
        if not self.cart:
            messagebox.showwarning("Empty cart", "No items in cart to finalize")
            return

        # Refresh inventory to ensure latest stock counts
        self._refresh_inventory_cache()

        # Validate stock availability before committing
        for product_id, item in self.cart.items():
            product = self.inventory_cache.get(product_id)
            if product is None:
                messagebox.showerror("Error", f"Product {product_id} no longer exists")
                return
            if item["quantity"] > product.stock:
                messagebox.showerror(
                    "Insufficient stock",
                    f"Only {product.stock} units available for {product.name}",
                )
                return

        subtotal = sum(item["line_total"] for item in self.cart.values())
        tax = subtotal * TAX_RATE
        total = subtotal + tax

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
                        datetime.utcnow().isoformat(timespec="seconds"),
                        subtotal,
                        tax,
                        total,
                        json.dumps(
                            [
                                {
                                    "product_id": product_id,
                                    "name": item["name"],
                                    "quantity": item["quantity"],
                                    "price": item["price"],
                                    "line_total": item["line_total"],
                                }
                                for product_id, item in self.cart.items()
                            ]
                        ),
                    ),
                )
                conn.commit()
        except sqlite3.DatabaseError as exc:
            messagebox.showerror("Database error", f"Failed to finalize sale: {exc}")
            return

        messagebox.showinfo("Sale complete", f"Total charged: ${total:.2f}")
        self.clear_cart()
        self._refresh_inventory_cache()


class POSApp(tk.Tk):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()
        self.title("POS System")
        self.geometry("950x600")
        self.db = DatabaseManager(DB_FILE)
        self._build_ui()

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
        )
        container.add(self.sales_frame, text="Sales")

    def _notify_inventory_change(self) -> None:
        self.sales_frame._refresh_inventory_cache()


def main() -> None:
    app = POSApp()
    app.mainloop()


if __name__ == "__main__":
    main()
