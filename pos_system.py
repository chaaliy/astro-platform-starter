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


PALETTE = {
    "bg": "#eef2ff",
    "surface": "#ffffff",
    "surface_alt": "#f4f6ff",
    "primary": "#4c6ef5",
    "primary_dark": "#364fc7",
    "accent": "#f76707",
    "text": "#243b53",
    "muted": "#829ab1",
}

FONT_FAMILY = "Segoe UI"


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
        super().__init__(parent, padding=20, style="Background.TFrame")
        self.db = db
        self.on_inventory_change = on_inventory_change
        self.summary_var = tk.StringVar(value="No products in inventory yet.")

        self.container = ttk.Frame(self, style="Card.TFrame", padding=20)
        self.container.grid(row=0, column=0, sticky="nsew")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(1, weight=1)
        self.container.grid_columnconfigure(3, weight=1)
        self.container.grid_rowconfigure(9, weight=1)

        self._build_ui()
        self.refresh_products()

    def _build_ui(self) -> None:
        container = self.container

        title = ttk.Label(container, text="Product Management", style="Title.TLabel")
        title.grid(row=0, column=0, columnspan=4, sticky="w")

        subtitle = ttk.Label(
            container,
            text="Maintain your catalog, adjust pricing, and monitor stock in real time.",
            style="Subtitle.TLabel",
        )
        subtitle.grid(row=1, column=0, columnspan=4, sticky="w", pady=(2, 12))

        summary = ttk.Label(container, textvariable=self.summary_var, style="Summary.TLabel")
        summary.grid(row=2, column=0, columnspan=4, sticky="w")

        ttk.Separator(container).grid(row=3, column=0, columnspan=5, sticky="ew", pady=(12, 18))

        ttk.Label(container, text="Product ID:", style="Highlight.TLabel").grid(
            row=4, column=0, sticky=tk.W, padx=(0, 8)
        )
        ttk.Label(container, text="Name:", style="Highlight.TLabel").grid(
            row=5, column=0, sticky=tk.W, padx=(0, 8)
        )
        ttk.Label(container, text="Price:", style="Highlight.TLabel").grid(
            row=6, column=0, sticky=tk.W, padx=(0, 8)
        )
        ttk.Label(container, text="Stock:", style="Highlight.TLabel").grid(
            row=7, column=0, sticky=tk.W, padx=(0, 8)
        )

        self.product_id_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.price_var = tk.StringVar()
        self.stock_var = tk.StringVar()

        ttk.Entry(container, textvariable=self.product_id_var).grid(
            row=4, column=1, sticky="ew", pady=2
        )
        ttk.Entry(container, textvariable=self.name_var).grid(
            row=5, column=1, sticky="ew", pady=2
        )
        ttk.Entry(container, textvariable=self.price_var).grid(
            row=6, column=1, sticky="ew", pady=2
        )
        ttk.Entry(container, textvariable=self.stock_var).grid(
            row=7, column=1, sticky="ew", pady=2
        )

        add_button = ttk.Button(
            container,
            text="Add Product",
            command=self.add_product,
            style="Accent.TButton",
        )
        add_button.grid(row=8, column=0, pady=(12, 0), sticky="ew")

        update_button = ttk.Button(
            container,
            text="Update Product",
            command=self.update_product,
            style="Secondary.TButton",
        )
        update_button.grid(row=8, column=1, pady=(12, 0), sticky="ew", padx=(10, 0))

        clear_button = ttk.Button(
            container, text="Clear", command=self.clear_form, style="Secondary.TButton"
        )
        clear_button.grid(row=8, column=2, pady=(12, 0), sticky="ew", padx=(10, 0))

        refresh_button = ttk.Button(
            container, text="Refresh", command=self.refresh_products, style="Secondary.TButton"
        )
        refresh_button.grid(row=8, column=3, pady=(12, 0), sticky="ew", padx=(10, 0))

        columns = ("product_id", "name", "price", "stock")
        self.tree = ttk.Treeview(
            container,
            columns=columns,
            show="headings",
            height=8,
        )
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            anchor = tk.CENTER if col != "name" else tk.W
            width = 120 if col != "name" else 220
            self.tree.column(col, width=width, anchor=anchor)
        self.tree.configure(selectmode="browse")
        self.tree.grid(row=9, column=0, columnspan=4, sticky="nsew", pady=(16, 0))

        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=9, column=4, sticky="ns")

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

    def __init__(self, parent: tk.Widget, db: DatabaseManager, inventory_provider) -> None:
        super().__init__(parent, padding=20, style="Background.TFrame")
        self.db = db
        self.inventory_provider = inventory_provider
        self.cart: Dict[str, Dict[str, float]] = {}
        self.status_var = tk.StringVar(value="Ready to build a cart.")

        self.container = ttk.Frame(self, style="Card.TFrame", padding=20)
        self.container.grid(row=0, column=0, sticky="nsew")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(1, weight=1)
        self.container.grid_rowconfigure(5, weight=1)

        self._build_ui()
        self._refresh_inventory_cache()

    def _build_ui(self) -> None:
        container = self.container

        title = ttk.Label(container, text="Sales", style="Title.TLabel")
        title.grid(row=0, column=0, columnspan=4, sticky="w")

        subtitle = ttk.Label(
            container,
            text="Scan items into the cart, review totals, and complete customer sales.",
            style="Subtitle.TLabel",
        )
        subtitle.grid(row=1, column=0, columnspan=4, sticky="w", pady=(2, 12))

        ttk.Separator(container).grid(row=2, column=0, columnspan=5, sticky="ew", pady=(12, 18))

        ttk.Label(container, text="Product ID:", style="Highlight.TLabel").grid(
            row=3, column=0, sticky=tk.W
        )
        ttk.Label(container, text="Quantity:", style="Highlight.TLabel").grid(
            row=4, column=0, sticky=tk.W
        )

        self.product_id_var = tk.StringVar()
        self.quantity_var = tk.StringVar(value="1")

        ttk.Entry(container, textvariable=self.product_id_var).grid(
            row=3, column=1, pady=2, sticky="ew"
        )
        ttk.Entry(container, textvariable=self.quantity_var).grid(
            row=4, column=1, pady=2, sticky="ew"
        )

        add_button = ttk.Button(
            container,
            text="Add to Cart",
            command=self.add_to_cart,
            style="Accent.TButton",
        )
        add_button.grid(row=3, column=2, rowspan=2, padx=(12, 0), sticky="nsew")

        columns = ("product_id", "name", "price", "quantity", "line_total")
        self.tree = ttk.Treeview(container, columns=columns, show="headings", height=10)
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            anchor = tk.CENTER if col != "name" else tk.W
            width = 110 if col not in {"name", "line_total"} else 140
            if col == "name":
                width = 220
            self.tree.column(col, anchor=anchor, width=width)
        self.tree.configure(selectmode="browse")
        self.tree.grid(row=5, column=0, columnspan=4, sticky="nsew", pady=(16, 0))

        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=5, column=4, sticky="ns")

        self.tree.tag_configure("evenrow", background=PALETTE["surface"])
        self.tree.tag_configure("oddrow", background=PALETTE["surface_alt"])
        self.tree.bind("<Delete>", lambda _event: self.remove_selected_item())
        self.tree.bind("<Double-1>", lambda _event: self.remove_selected_item())

        totals_frame = ttk.Frame(container, style="Card.TFrame", padding=(16, 12))
        totals_frame.grid(row=6, column=0, columnspan=4, sticky="ew", pady=(20, 0))
        totals_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(totals_frame, text="Subtotal", style="TotalsCaption.TLabel").grid(
            row=0, column=0, sticky=tk.W
        )
        ttk.Label(totals_frame, text="Tax (15%)", style="TotalsCaption.TLabel").grid(
            row=1, column=0, sticky=tk.W
        )
        ttk.Label(totals_frame, text="Grand Total", style="TotalsCaption.TLabel").grid(
            row=2, column=0, sticky=tk.W
        )

        self.subtotal_var = tk.StringVar(value="0.00")
        self.tax_var = tk.StringVar(value="0.00")
        self.total_var = tk.StringVar(value="0.00")

        ttk.Label(totals_frame, textvariable=self.subtotal_var, style="TotalsValue.TLabel").grid(
            row=0, column=1, sticky=tk.E
        )
        ttk.Label(totals_frame, textvariable=self.tax_var, style="TotalsValue.TLabel").grid(
            row=1, column=1, sticky=tk.E
        )
        ttk.Label(totals_frame, textvariable=self.total_var, style="TotalsValue.TLabel").grid(
            row=2, column=1, sticky=tk.E
        )

        finalize_button = ttk.Button(
            container,
            text="Finalize Sale",
            command=self.finalize_sale,
            style="Accent.TButton",
        )
        finalize_button.grid(row=7, column=0, pady=(16, 0), sticky="ew")

        remove_button = ttk.Button(
            container,
            text="Remove Item",
            command=self.remove_selected_item,
            style="Secondary.TButton",
        )
        remove_button.grid(row=7, column=1, pady=(16, 0), sticky="ew", padx=(12, 0))

        clear_button = ttk.Button(
            container,
            text="Clear Cart",
            command=self.clear_cart,
            style="Secondary.TButton",
        )
        clear_button.grid(row=7, column=2, pady=(16, 0), sticky="ew", padx=(12, 0))

        self.status_label = ttk.Label(container, textvariable=self.status_var, style="Status.TLabel")
        self.status_label.grid(row=8, column=0, columnspan=4, sticky="w", pady=(18, 0))

        container.grid_columnconfigure(3, weight=1)

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
        tax = subtotal * TAX_RATE
        total = subtotal + tax
        self.subtotal_var.set(f"{subtotal:.2f}")
        self.tax_var.set(f"{tax:.2f}")
        self.total_var.set(f"{total:.2f}")

    def clear_cart(self) -> None:
        self.cart.clear()
        self._populate_cart_tree()
        self._update_totals()
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
            self._set_status("Failed to finalize sale. Please try again.")
            return

        messagebox.showinfo("Sale complete", f"Total charged: ${total:.2f}")
        self.clear_cart()
        self._refresh_inventory_cache()
        self._set_status(
            f"Sale completed at {datetime.now().strftime('%I:%M:%S %p').lstrip('0')}.",
            accent=True,
        )


class POSApp(tk.Tk):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()
        self.title("POS System")
        self.geometry("950x600")
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
        style.configure("Card.TFrame", background=PALETTE["surface"], borderwidth=0, relief="flat")

        style.configure("TLabel", background=PALETTE["surface"], foreground=PALETTE["text"], font=(FONT_FAMILY, 11))
        style.configure(
            "Title.TLabel",
            background=PALETTE["surface"],
            foreground=PALETTE["primary_dark"],
            font=(FONT_FAMILY, 18, "bold"),
        )
        style.configure(
            "Subtitle.TLabel",
            background=PALETTE["surface"],
            foreground=PALETTE["muted"],
            font=(FONT_FAMILY, 11),
        )
        style.configure(
            "Summary.TLabel",
            background=PALETTE["surface"],
            foreground=PALETTE["muted"],
            font=(FONT_FAMILY, 10),
        )
        style.configure(
            "Highlight.TLabel",
            background=PALETTE["surface"],
            foreground=PALETTE["text"],
            font=(FONT_FAMILY, 11, "bold"),
        )
        style.configure(
            "TotalsCaption.TLabel",
            background=PALETTE["surface"],
            foreground=PALETTE["muted"],
            font=(FONT_FAMILY, 12),
        )
        style.configure(
            "TotalsValue.TLabel",
            background=PALETTE["surface"],
            foreground=PALETTE["accent"],
            font=(FONT_FAMILY, 16, "bold"),
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

        style.configure("TButton", font=(FONT_FAMILY, 11), padding=(12, 8))
        style.configure(
            "Accent.TButton",
            background=PALETTE["primary"],
            foreground="#ffffff",
            padding=(16, 10),
            borderwidth=0,
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
            borderwidth=0,
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
            rowheight=28,
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
        )
        container.add(self.sales_frame, text="Sales")

    def _notify_inventory_change(self) -> None:
        self.sales_frame._refresh_inventory_cache()


def main() -> None:
    app = POSApp()
    app.mainloop()


if __name__ == "__main__":
    main()
