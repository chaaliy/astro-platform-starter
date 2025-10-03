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
from tkinter import font as tkfont
from tkinter import ttk


DB_FILE = Path("pos_system.db")


PALETTE = {
    "bg": "#161b2c",
    "surface": "#1f2538",
    "surface_alt": "#252c41",
    "primary": "#ff5b60",
    "primary_dark": "#e2484d",
    "accent": "#5b8dff",
    "text": "#f8fafc",
    "muted": "#94a3b8",
    "hero_fg": "#ffffff",
    "hero_muted": "#cbd5f5",
    "panel": "#20273a",
    "card_border": "#2f364e",
}

FONT_FAMILY = "Segoe UI"


DEFAULT_LANGUAGE = "en"
DEFAULT_CURRENCY = "USD"


SUPPORTED_LANGUAGES: Dict[str, Dict[str, Any]] = {
    "en": {"name": "English"},
    "es": {"name": "Español"},
    "fr": {"name": "Français"},
    "ar": {"name": "العربية"},
}


SUPPORTED_CURRENCIES: Dict[str, Dict[str, Any]] = {
    "USD": {"name": "US Dollar", "symbol": "$", "pattern": "{symbol}{value:,.2f}"},
    "EUR": {"name": "Euro", "symbol": "€", "pattern": "{value:,.2f} {symbol}"},
    "MXN": {"name": "Peso mexicano", "symbol": "$", "pattern": "{symbol}{value:,.2f} MXN"},
    "MDH": {
        "name": "Moroccan Dirham",
        "symbol": "د.م.",
        "pattern": "{value:,.2f} {symbol}",
    },
}


TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "app.title": {
        "en": "POS System",
        "es": "Sistema POS",
        "fr": "Système de point de vente",
        "ar": "نظام نقاط البيع",
    },
    "tab.products": {"en": "Products", "es": "Productos", "fr": "Produits", "ar": "المنتجات"},
    "tab.sales": {"en": "Sales", "es": "Ventas", "fr": "Ventes", "ar": "المبيعات"},
    "tab.history": {"en": "History", "es": "Historial", "fr": "Historique", "ar": "السجل"},
    "tab.settings": {"en": "Settings", "es": "Configuración", "fr": "Paramètres", "ar": "الإعدادات"},
    "menu.navigate": {
        "en": "Navigate",
        "es": "Navegar",
        "fr": "Naviguer",
        "ar": "التنقل",
    },
    "inventory.hero.title": {
        "en": "Inventory Studio",
        "es": "Estudio de Inventario",
        "fr": "Studio d'inventaire",
        "ar": "استوديو المخزون",
    },
    "inventory.hero.subtitle": {
        "en": "Add, update, and monitor your catalog with instant insights.",
        "es": "Agrega, actualiza y supervisa tu catálogo con información al instante.",
        "fr": "Ajoutez, mettez à jour et surveillez votre catalogue avec des informations instantanées.",
        "ar": "أضف وحدث وراقب قائمتك مع رؤى فورية.",
    },
    "inventory.hero.empty": {
        "en": "No products in inventory yet.",
        "es": "Aún no hay productos en el inventario.",
        "fr": "Aucun produit en stock pour le moment.",
        "ar": "لا توجد منتجات في المخزون بعد.",
    },
    "inventory.hero.summary": {
        "en": "{count} products • {value} inventory value",
        "es": "{count} productos • {value} valor de inventario",
        "fr": "{count} produits • {value} valeur de stock",
        "ar": "{count} منتج • قيمة مخزون {value}",
    },
    "inventory.card.form.title": {
        "en": "New or Existing Product",
        "es": "Producto nuevo o existente",
        "fr": "Produit nouveau ou existant",
        "ar": "منتج جديد أو حالي",
    },
    "field.product_id": {"en": "Product ID", "es": "ID del producto", "fr": "ID du produit", "ar": "معرّف المنتج"},
    "field.name": {"en": "Name", "es": "Nombre", "fr": "Nom", "ar": "الاسم"},
    "field.price": {"en": "Price", "es": "Precio", "fr": "Prix", "ar": "السعر"},
    "field.stock": {"en": "Stock", "es": "Existencias", "fr": "Stock", "ar": "المخزون"},
    "action.add_product": {
        "en": "Add Product",
        "es": "Agregar producto",
        "fr": "Ajouter un produit",
        "ar": "إضافة منتج",
    },
    "action.update_product": {"en": "Update", "es": "Actualizar", "fr": "Mettre à jour", "ar": "تحديث"},
    "action.clear": {"en": "Clear", "es": "Limpiar", "fr": "Effacer", "ar": "مسح"},
    "action.refresh": {"en": "Refresh", "es": "Actualizar", "fr": "Actualiser", "ar": "تحديث"},
    "inventory.card.list.title": {"en": "Inventory", "es": "Inventario", "fr": "Inventaire", "ar": "المخزون"},
    "inventory.table.product": {"en": "Product", "es": "Producto", "fr": "Produit", "ar": "المنتج"},
    "inventory.table.price": {"en": "Price", "es": "Precio", "fr": "Prix", "ar": "السعر"},
    "inventory.table.stock": {"en": "Stock", "es": "Existencias", "fr": "Stock", "ar": "المخزون"},
    "inventory.success.add": {
        "en": "Product added successfully",
        "es": "Producto agregado correctamente",
        "fr": "Produit ajouté avec succès",
        "ar": "تمت إضافة المنتج بنجاح",
    },
    "inventory.success.update": {
        "en": "Product updated successfully",
        "es": "Producto actualizado correctamente",
        "fr": "Produit mis à jour avec succès",
        "ar": "تم تحديث المنتج بنجاح",
    },
    "inventory.error.duplicate": {
        "en": "Product ID already exists",
        "es": "El ID del producto ya existe",
        "fr": "L'identifiant du produit existe déjà",
        "ar": "معرّف المنتج موجود بالفعل",
    },
    "inventory.error.database": {
        "en": "Database error: {error}",
        "es": "Error de base de datos: {error}",
        "fr": "Erreur de base de données : {error}",
        "ar": "خطأ في قاعدة البيانات: {error}",
    },
    "inventory.error.invalid": {
        "en": "Price must be a number and stock must be an integer",
        "es": "El precio debe ser un número y las existencias un entero",
        "fr": "Le prix doit être un nombre et le stock un entier",
        "ar": "يجب أن يكون السعر رقماً والمخزون عدداً صحيحاً",
    },
    "inventory.error.negative": {
        "en": "Price and stock must be non-negative",
        "es": "El precio y las existencias deben ser no negativos",
        "fr": "Le prix et le stock doivent être positifs",
        "ar": "يجب أن يكون السعر والمخزون غير سالبين",
    },
    "inventory.error.required": {
        "en": "Product ID and name are required",
        "es": "El ID y el nombre del producto son obligatorios",
        "fr": "L'identifiant du produit et le nom sont obligatoires",
        "ar": "معرّف المنتج والاسم مطلوبان",
    },
    "sales.hero.title": {
        "en": "Today's Menu",
        "es": "Menú de hoy",
        "fr": "Menu du jour",
        "ar": "قائمة اليوم",
    },
    "sales.hero.subtitle": {
        "en": "Tap a tile to add it to the current order.",
        "es": "Toca una tarjeta para agregarla al pedido.",
        "fr": "Appuyez sur une tuile pour l'ajouter à la commande.",
        "ar": "اضغط على العنصر لإضافته إلى الطلب الحالي.",
    },
    "sales.hero.empty": {"en": "Cart is empty.", "es": "El carrito está vacío.", "fr": "Le panier est vide.", "ar": "السلة فارغة."},
    "sales.hero.summary": {
        "en": "{count} {label} • {total}",
        "es": "{count} {label} • {total}",
        "fr": "{count} {label} • {total}",
        "ar": "{count} {label} • {total}",
    },
    "sales.hero.items": {"en": "items", "es": "artículos", "fr": "articles", "ar": "عناصر"},
    "sales.hero.item": {"en": "item", "es": "artículo", "fr": "article", "ar": "عنصر"},
    "sales.status.prompt": {
        "en": "Ready to build a cart.",
        "es": "Listo para armar un carrito.",
        "fr": "Prêt à créer un panier.",
        "ar": "جاهز لبناء السلة.",
    },
    "sales.categories.title": {
        "en": "Menu",
        "es": "Menú",
        "fr": "Menu",
        "ar": "القائمة",
    },
    "sales.categories.subtitle": {
        "en": "Filter items by section.",
        "es": "Filtra los artículos por sección.",
        "fr": "Filtrez les articles par section.",
        "ar": "قم بتصفية العناصر حسب القسم.",
    },
    "sales.categories.all": {
        "en": "All items",
        "es": "Todos los artículos",
        "fr": "Tous les articles",
        "ar": "جميع العناصر",
    },
    "sales.categories.uncategorized": {
        "en": "Other",
        "es": "Otros",
        "fr": "Autres",
        "ar": "أخرى",
    },
    "sales.products.empty": {
        "en": "No products are available yet.",
        "es": "Aún no hay productos disponibles.",
        "fr": "Aucun produit n'est disponible pour le moment.",
        "ar": "لا توجد منتجات متاحة بعد.",
    },
    "sales.products.empty_category": {
        "en": "No items in this category yet.",
        "es": "No hay artículos en esta categoría todavía.",
        "fr": "Aucun article dans cette catégorie pour le moment.",
        "ar": "لا توجد عناصر في هذه الفئة بعد.",
    },
    "sales.products.subtitle": {
        "en": "All changes update the cart instantly.",
        "es": "Los cambios se actualizan en el carrito al instante.",
        "fr": "Les modifications mettent immédiatement à jour le panier.",
        "ar": "يتم تحديث السلة فورًا مع أي تغييرات.",
    },
    "field.quantity": {"en": "Quantity", "es": "Cantidad", "fr": "Quantité", "ar": "الكمية"},
    "action.add_to_cart": {"en": "Add to Cart", "es": "Agregar al carrito", "fr": "Ajouter au panier", "ar": "إضافة إلى السلة"},
    "action.remove_selected": {
        "en": "Remove Selected",
        "es": "Eliminar seleccionado",
        "fr": "Supprimer la sélection",
        "ar": "إزالة المحدد",
    },
    "action.clear_cart": {"en": "Clear Cart", "es": "Vaciar carrito", "fr": "Vider le panier", "ar": "إفراغ السلة"},
    "sales.summary.title": {"en": "Checkout Summary", "es": "Resumen de pago", "fr": "Récapitulatif", "ar": "ملخص الدفع"},
    "sales.summary.subtitle": {
        "en": "Review order details before payment.",
        "es": "Revisa los detalles del pedido antes de pagar.",
        "fr": "Vérifiez les détails de la commande avant le paiement.",
        "ar": "راجع تفاصيل الطلب قبل الدفع.",
    },
    "label.subtotal": {"en": "Subtotal", "es": "Subtotal", "fr": "Sous-total", "ar": "الإجمالي الفرعي"},
    "label.balance_due": {"en": "Balance Due", "es": "Saldo a pagar", "fr": "Montant dû", "ar": "المبلغ المستحق"},
    "action.finalize_sale": {"en": "Finalize Sale", "es": "Finalizar venta", "fr": "Finaliser la vente", "ar": "إتمام البيع"},
    "action.print_invoice": {"en": "Print Invoice", "es": "Imprimir factura", "fr": "Imprimer la facture", "ar": "طباعة الفاتورة"},
    "sales.cart.title": {"en": "Active Cart", "es": "Carrito activo", "fr": "Panier actif", "ar": "السلة النشطة"},
    "sales.status.ready": {
        "en": "Sale completed at {timestamp} • Invoice ready to print.",
        "es": "Venta completada a las {timestamp} • Factura lista para imprimir.",
        "fr": "Vente terminée à {timestamp} • Facture prête à être imprimée.",
        "ar": "اكتمل البيع في {timestamp} • الفاتورة جاهزة للطباعة.",
    },
    "sales.warning.empty": {
        "en": "No items in cart to finalize",
        "es": "No hay artículos en el carrito para finalizar",
        "fr": "Aucun article dans le panier à finaliser",
        "ar": "لا توجد عناصر في السلة للإتمام",
    },
    "sales.warning.add_items": {
        "en": "Add items to the cart before finalizing.",
        "es": "Agrega artículos al carrito antes de finalizar.",
        "fr": "Ajoutez des articles au panier avant de finaliser.",
        "ar": "أضف عناصر إلى السلة قبل الإتمام.",
    },
    "sales.error.not_found": {
        "en": "Product {product_id} no longer exists",
        "es": "El producto {product_id} ya no existe",
        "fr": "Le produit {product_id} n'existe plus",
        "ar": "المنتج {product_id} لم يعد موجوداً",
    },
    "sales.error.insufficient_stock": {
        "en": "Only {stock} units available for {name}",
        "es": "Solo hay {stock} unidades disponibles de {name}",
        "fr": "Seulement {stock} unités disponibles pour {name}",
        "ar": "متوفر فقط {stock} وحدة من {name}",
    },
    "sales.error.generic": {
        "en": "Failed to finalize sale. Please try again.",
        "es": "No se pudo finalizar la venta. Inténtalo de nuevo.",
        "fr": "Échec de la finalisation de la vente. Veuillez réessayer.",
        "ar": "تعذر إتمام البيع. يرجى المحاولة مرة أخرى.",
    },
    "sales.success.total": {
        "en": "Total charged: {total}",
        "es": "Total cobrado: {total}",
        "fr": "Montant facturé : {total}",
        "ar": "المبلغ المحصل: {total}",
    },
    "sales.status.added": {
        "en": "Added {quantity} × {name} to the cart.",
        "es": "{quantity} × {name} agregado al carrito.",
        "fr": "Ajout de {quantity} × {name} au panier.",
        "ar": "تمت إضافة {quantity} × {name} إلى السلة.",
    },
    "sales.status.updated": {
        "en": "Updated {quantity} × {name} in the cart.",
        "es": "{quantity} × {name} actualizado en el carrito.",
        "fr": "Mise à jour de {quantity} × {name} dans le panier.",
        "ar": "تم تحديث {quantity} × {name} في السلة.",
    },
    "sales.status.removed": {
        "en": "Removed {name} from the cart.",
        "es": "{name} eliminado del carrito.",
        "fr": "{name} retiré du panier.",
        "ar": "تمت إزالة {name} من السلة.",
    },
    "sales.status.cleared": {
        "en": "Cart cleared.",
        "es": "Carrito vacío.",
        "fr": "Panier vidé.",
        "ar": "تم إفراغ السلة.",
    },
    "sales.status.invalid": {
        "en": "Enter a valid product ID and quantity.",
        "es": "Ingresa un ID de producto y cantidad válidos.",
        "fr": "Saisissez un identifiant produit et une quantité valides.",
        "ar": "أدخل معرف منتج وكماً صالحين.",
    },
    "sales.error.quantity": {
        "en": "Quantity must be a positive integer.",
        "es": "La cantidad debe ser un entero positivo.",
        "fr": "La quantité doit être un entier positif.",
        "ar": "يجب أن تكون الكمية عدداً صحيحاً موجباً.",
    },
    "sales.status.stock": {
        "en": "Only {stock} left for {name}.",
        "es": "Solo quedan {stock} de {name}.",
        "fr": "Il ne reste que {stock} pour {name}.",
        "ar": "تبقى فقط {stock} من {name}.",
    },
    "sales.status.not_found": {
        "en": "Product ID not found in inventory.",
        "es": "ID de producto no encontrado en el inventario.",
        "fr": "Identifiant produit introuvable dans l'inventaire.",
        "ar": "معرّف المنتج غير موجود في المخزون.",
    },
    "sales.status.select_item": {
        "en": "Select an item to remove from the cart.",
        "es": "Selecciona un artículo para quitar del carrito.",
        "fr": "Sélectionnez un article à retirer du panier.",
        "ar": "اختر عنصراً لإزالته من السلة.",
    },
    "sales.status.no_longer_exists": {
        "en": "Product {product_id} no longer exists.",
        "es": "El producto {product_id} ya no existe.",
        "fr": "Le produit {product_id} n'existe plus.",
        "ar": "المنتج {product_id} لم يعد موجوداً.",
    },
    "sales.dialog.invalid_quantity": {
        "en": "Invalid quantity",
        "es": "Cantidad inválida",
        "fr": "Quantité invalide",
        "ar": "كمية غير صالحة",
    },
    "sales.cart.heading.product_id": {
        "en": "Product Id",
        "es": "ID",
        "fr": "ID produit",
        "ar": "معرّف المنتج",
    },
    "sales.cart.heading.name": {"en": "Name", "es": "Nombre", "fr": "Nom", "ar": "الاسم"},
    "sales.cart.heading.price": {"en": "Price", "es": "Precio", "fr": "Prix", "ar": "السعر"},
    "sales.cart.heading.quantity": {"en": "Qty", "es": "Cant.", "fr": "Qté", "ar": "العدد"},
    "sales.cart.heading.total": {"en": "Total", "es": "Total", "fr": "Total", "ar": "الإجمالي"},
    "history.hero.title": {"en": "Purchase History", "es": "Historial de compras", "fr": "Historique des achats", "ar": "سجل المشتريات"},
    "history.hero.subtitle": {
        "en": "Browse previous receipts, revisit totals, and reprint invoices on demand.",
        "es": "Explora recibos anteriores, revisa totales y reimprime facturas al instante.",
        "fr": "Consultez les reçus précédents, révisez les totaux et réimprimez les factures à la demande.",
        "ar": "تصفح الإيصالات السابقة، وراجع الإجماليات، وأعد طباعة الفواتير عند الطلب.",
    },
    "history.hero.empty": {
        "en": "No purchases recorded yet.",
        "es": "Aún no se registran compras.",
        "fr": "Aucun achat enregistré pour le moment.",
        "ar": "لا توجد عمليات شراء مسجلة بعد.",
    },
    "history.hero.summary": {
        "en": "{count} sales • {revenue} revenue captured",
        "es": "{count} ventas • {revenue} ingresos registrados",
        "fr": "{count} ventes • {revenue} de chiffre d'affaires",
        "ar": "{count} عملية بيع • إيرادات {revenue}",
    },
    "history.card.title": {"en": "Recent Sales", "es": "Ventas recientes", "fr": "Ventes récentes", "ar": "أحدث المبيعات"},
    "history.refresh": {"en": "Refresh", "es": "Actualizar", "fr": "Actualiser", "ar": "تحديث"},
    "history.table.sale_id": {"en": "Sale #", "es": "Venta #", "fr": "Vente #", "ar": "رقم البيع"},
    "history.table.timestamp": {"en": "Completed", "es": "Completada", "fr": "Terminée", "ar": "مكتمل"},
    "history.table.items": {"en": "Items", "es": "Artículos", "fr": "Articles", "ar": "العناصر"},
    "history.table.subtotal": {"en": "Subtotal", "es": "Subtotal", "fr": "Sous-total", "ar": "الإجمالي الفرعي"},
    "history.table.total": {"en": "Total", "es": "Total", "fr": "Total", "ar": "الإجمالي"},
    "history.details.title": {"en": "Sale Details", "es": "Detalles de la venta", "fr": "Détails de la vente", "ar": "تفاصيل البيع"},
    "history.details.none": {
        "en": "Select a sale to see its details.",
        "es": "Selecciona una venta para ver sus detalles.",
        "fr": "Sélectionnez une vente pour voir ses détails.",
        "ar": "اختر عملية بيع لرؤية تفاصيلها.",
    },
    "history.details.line": {
        "en": "{quantity} × {name} (@ {price}) = {total}",
        "es": "{quantity} × {name} (@ {price}) = {total}",
        "fr": "{quantity} × {name} (@ {price}) = {total}",
        "ar": "{quantity} × {name} (@ {price}) = {total}",
    },
    "history.details.subtotal": {"en": "Subtotal: {value}", "es": "Subtotal: {value}", "fr": "Sous-total : {value}", "ar": "الإجمالي الفرعي: {value}"},
    "history.details.total": {"en": "Balance Due: {value}", "es": "Total: {value}", "fr": "Montant dû : {value}", "ar": "المبلغ المستحق: {value}"},
    "history.action.open": {"en": "Open Invoice", "es": "Abrir factura", "fr": "Ouvrir la facture", "ar": "فتح الفاتورة"},
    "history.info.none": {
        "en": "No sale selected",
        "es": "No hay venta seleccionada",
        "fr": "Aucune vente sélectionnée",
        "ar": "لم يتم اختيار بيع",
    },
    "history.info.select": {
        "en": "Select a sale to open its invoice.",
        "es": "Selecciona una venta para abrir su factura.",
        "fr": "Sélectionnez une vente pour ouvrir sa facture.",
        "ar": "اختر عملية بيع لفتح فاتورتها.",
    },
    "history.status.updated": {
        "en": "History refreshed.",
        "es": "Historial actualizado.",
        "fr": "Historique actualisé.",
        "ar": "تم تحديث السجل.",
    },
    "invoice.title": {"en": "Invoice Preview", "es": "Vista previa de factura", "fr": "Aperçu de la facture", "ar": "معاينة الفاتورة"},
    "invoice.header": {"en": "POS System Invoice", "es": "Factura del sistema POS", "fr": "Facture du système POS", "ar": "فاتورة نظام نقاط البيع"},
    "invoice.columns": {
        "en": "{id:<10}{name:<26}{qty:>5}{price:>16}{total:>15}",
        "es": "{id:<10}{name:<26}{qty:>5}{price:>16}{total:>15}",
        "fr": "{id:<10}{name:<26}{qty:>5}{price:>16}{total:>15}",
        "ar": "{id:<10}{name:<26}{qty:>5}{price:>16}{total:>15}",
    },
    "invoice.column.id": {"en": "ID", "es": "ID", "fr": "ID", "ar": "المعرف"},
    "invoice.column.product": {"en": "Product", "es": "Producto", "fr": "Produit", "ar": "المنتج"},
    "invoice.column.qty": {"en": "Qty", "es": "Cant.", "fr": "Qté", "ar": "الكمية"},
    "invoice.column.price": {"en": "Price", "es": "Precio", "fr": "Prix", "ar": "السعر"},
    "invoice.column.total": {"en": "Total", "es": "Total", "fr": "Total", "ar": "الإجمالي"},
    "invoice.sale_number": {"en": "Sale #", "es": "Venta #", "fr": "Vente #", "ar": "رقم البيع"},
    "invoice.completed": {"en": "Completed:", "es": "Completado:", "fr": "Terminé :", "ar": "مكتمل:"},
    "invoice.subtotal": {"en": "Subtotal:", "es": "Subtotal:", "fr": "Sous-total :", "ar": "الإجمالي الفرعي:"},
    "invoice.total": {"en": "Balance Due:", "es": "Total:", "fr": "Montant dû :", "ar": "المبلغ المستحق:"},
    "invoice.footer": {
        "en": "Thank you for shopping with us!",
        "es": "¡Gracias por su compra!",
        "fr": "Merci de votre achat !",
        "ar": "شكراً لتسوقكم معنا!",
    },
    "invoice.save": {"en": "Save As…", "es": "Guardar como…", "fr": "Enregistrer sous…", "ar": "حفظ باسم…"},
    "invoice.print": {"en": "Print", "es": "Imprimir", "fr": "Imprimer", "ar": "طباعة"},
    "invoice.close": {"en": "Close", "es": "Cerrar", "fr": "Fermer", "ar": "إغلاق"},
    "invoice.save.title": {"en": "Save invoice", "es": "Guardar factura", "fr": "Enregistrer la facture", "ar": "حفظ الفاتورة"},
    "invoice.save.error": {
        "en": "Could not save invoice: {error}",
        "es": "No se pudo guardar la factura: {error}",
        "fr": "Impossible d'enregistrer la facture : {error}",
        "ar": "تعذر حفظ الفاتورة: {error}",
    },
    "invoice.save.success": {
        "en": "Invoice saved to {path}",
        "es": "Factura guardada en {path}",
        "fr": "Facture enregistrée dans {path}",
        "ar": "تم حفظ الفاتورة في {path}",
    },
    "invoice.print.sent": {
        "en": "Invoice sent to the default printer.",
        "es": "Factura enviada a la impresora predeterminada.",
        "fr": "Facture envoyée à l'imprimante par défaut.",
        "ar": "تم إرسال الفاتورة إلى الطابعة الافتراضية.",
    },
    "invoice.print.missing": {
        "en": "The system printing utility was not found. Save the invoice and print manually.",
        "es": "No se encontró la utilidad de impresión del sistema. Guarda la factura e imprímela manualmente.",
        "fr": "L'outil d'impression du système est introuvable. Enregistrez la facture et imprimez-la manuellement.",
        "ar": "لم يتم العثور على أداة طباعة النظام. احفظ الفاتورة واطبعها يدوياً.",
    },
    "invoice.print.error": {
        "en": "Could not print invoice: {error}",
        "es": "No se pudo imprimir la factura: {error}",
        "fr": "Impossible d'imprimer la facture : {error}",
        "ar": "تعذر طباعة الفاتورة: {error}",
    },
    "sales.invoice.none.title": {
        "en": "No invoice",
        "es": "Sin factura",
        "fr": "Aucune facture",
        "ar": "لا توجد فاتورة",
    },
    "sales.invoice.none.message": {
        "en": "Complete a sale to print an invoice.",
        "es": "Completa una venta para imprimir una factura.",
        "fr": "Finalisez une vente pour imprimer une facture.",
        "ar": "أكمل عملية البيع لطباعة الفاتورة.",
    },
    "sales.error.database": {
        "en": "Failed to finalize sale: {error}",
        "es": "No se pudo finalizar la venta: {error}",
        "fr": "Impossible de finaliser la vente : {error}",
        "ar": "تعذر إتمام البيع: {error}",
    },
    "settings.hero.title": {"en": "Preferences", "es": "Preferencias", "fr": "Préférences", "ar": "التفضيلات"},
    "settings.hero.subtitle": {
        "en": "Tailor language and currency to match your sales counter.",
        "es": "Adapta el idioma y la moneda a tu mostrador de ventas.",
        "fr": "Ajustez la langue et la devise à votre comptoir de vente.",
        "ar": "خصص اللغة والعملة لتناسب نقطة البيع لديك.",
    },
    "settings.language.label": {"en": "Language", "es": "Idioma", "fr": "Langue", "ar": "اللغة"},
    "settings.currency.label": {"en": "Currency", "es": "Moneda", "fr": "Devise", "ar": "العملة"},
    "settings.apply": {"en": "Apply Changes", "es": "Aplicar cambios", "fr": "Appliquer les modifications", "ar": "تطبيق التغييرات"},
    "settings.notice": {
        "en": "Settings updated successfully.",
        "es": "Configuración actualizada correctamente.",
        "fr": "Paramètres mis à jour avec succès.",
        "ar": "تم تحديث الإعدادات بنجاح.",
    },
    "dialog.success": {"en": "Success", "es": "Éxito", "fr": "Succès", "ar": "نجاح"},
    "dialog.error": {"en": "Error", "es": "Error", "fr": "Erreur", "ar": "خطأ"},
    "dialog.warning": {"en": "Warning", "es": "Advertencia", "fr": "Avertissement", "ar": "تحذير"},
    "dialog.info": {"en": "Information", "es": "Información", "fr": "Information", "ar": "معلومات"},
    "sales.dialog.empty": {
        "en": "Empty cart",
        "es": "Carrito vacío",
        "fr": "Panier vide",
        "ar": "سلة فارغة",
    },
    "sales.dialog.not_found": {
        "en": "Error",
        "es": "Error",
        "fr": "Erreur",
        "ar": "خطأ",
    },
    "sales.dialog.stock": {
        "en": "Insufficient stock",
        "es": "Stock insuficiente",
        "fr": "Stock insuffisant",
        "ar": "مخزون غير كافٍ",
    },
    "settings.applied.status": {
        "en": "Language changed to {language}, currency set to {currency}.",
        "es": "Idioma cambiado a {language}, moneda establecida en {currency}.",
        "fr": "Langue changée en {language}, devise définie sur {currency}.",
        "ar": "تم تغيير اللغة إلى {language}، وتم تعيين العملة إلى {currency}.",
    },
}


def translate(language: str, key: str, **kwargs: Any) -> str:
    catalog = TRANSLATIONS.get(key, {})
    template = catalog.get(language) or catalog.get(DEFAULT_LANGUAGE) or key
    try:
        return template.format(**kwargs)
    except (KeyError, IndexError, ValueError):
        return template


def format_currency(amount: float, currency_code: str) -> str:
    currency = SUPPORTED_CURRENCIES.get(currency_code, SUPPORTED_CURRENCIES[DEFAULT_CURRENCY])
    pattern = currency.get("pattern", "{symbol}{value:,.2f}")
    value = amount
    return pattern.format(symbol=currency.get("symbol", "$"), value=value, code=currency_code)


def get_currency_display(currency_code: str) -> str:
    currency = SUPPORTED_CURRENCIES.get(currency_code, SUPPORTED_CURRENCIES[DEFAULT_CURRENCY])
    return f"{currency_code} • {currency['name']}"


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
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            for key, value in ("language", DEFAULT_LANGUAGE), ("currency", DEFAULT_CURRENCY):
                cursor.execute(
                    "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                    (key, value),
                )
            conn.commit()

    def get_setting(self, key: str, default: Optional[str] = None) -> str:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
        if row is None:
            return default if default is not None else ""
        return str(row[0])

    def set_setting(self, key: str, value: str) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )
            conn.commit()

    def get_app_settings(self) -> Dict[str, str]:
        return {
            "language": self.get_setting("language", DEFAULT_LANGUAGE) or DEFAULT_LANGUAGE,
            "currency": self.get_setting("currency", DEFAULT_CURRENCY) or DEFAULT_CURRENCY,
        }

    def update_app_settings(self, language: str, currency: str) -> None:
        self.set_setting("language", language)
        self.set_setting("currency", currency)

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

    def __init__(
        self,
        parent: tk.Widget,
        db: DatabaseManager,
        on_inventory_change,
        app: "POSApp",
    ) -> None:
        super().__init__(parent, padding=20, style="Background.TFrame")
        self.db = db
        self.on_inventory_change = on_inventory_change
        self.app = app
        self.summary_var = tk.StringVar()
        self.product_id_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.price_var = tk.StringVar()
        self.stock_var = tk.StringVar()

        self.hero_title_var = tk.StringVar()
        self.hero_subtitle_var = tk.StringVar()
        self.form_title_var = tk.StringVar()
        self.product_id_label_var = tk.StringVar()
        self.name_label_var = tk.StringVar()
        self.price_label_var = tk.StringVar()
        self.stock_label_var = tk.StringVar()
        self.inventory_title_var = tk.StringVar()
        self.add_button_text = tk.StringVar()
        self.update_button_text = tk.StringVar()
        self.clear_button_text = tk.StringVar()
        self.refresh_button_text = tk.StringVar()

        self.container = ttk.Frame(self, style="Background.TFrame")
        self.container.grid(row=0, column=0, sticky="nsew")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_columnconfigure(1, weight=1)
        self.container.grid_rowconfigure(1, weight=1)

        self._build_ui()
        self.apply_settings()
        self.refresh_products()

    def _build_ui(self) -> None:
        container = self.container

        hero = ttk.Frame(container, style="Hero.TFrame", padding=(24, 18))
        hero.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 24))
        hero.grid_columnconfigure(0, weight=1)

        ttk.Label(hero, textvariable=self.hero_title_var, style="HeroTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            hero,
            textvariable=self.hero_subtitle_var,
            style="HeroSubtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))
        ttk.Label(hero, textvariable=self.summary_var, style="HeroStat.TLabel").grid(
            row=2, column=0, sticky="w", pady=(16, 0)
        )

        form_card = ttk.Frame(container, style="Card.TFrame", padding=24)
        form_card.grid(row=1, column=0, sticky="nsew", padx=(0, 16))
        form_card.grid_columnconfigure(1, weight=1)

        ttk.Label(form_card, textvariable=self.form_title_var, style="SectionTitle.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk.Separator(form_card).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 16))

        ttk.Label(form_card, textvariable=self.product_id_label_var, style="FieldLabel.TLabel").grid(
            row=2, column=0, sticky="w"
        )
        ttk.Entry(form_card, textvariable=self.product_id_var).grid(
            row=2, column=1, sticky="ew", pady=(0, 12)
        )

        ttk.Label(form_card, textvariable=self.name_label_var, style="FieldLabel.TLabel").grid(
            row=3, column=0, sticky="w"
        )
        ttk.Entry(form_card, textvariable=self.name_var).grid(
            row=3, column=1, sticky="ew", pady=(0, 12)
        )

        ttk.Label(form_card, textvariable=self.price_label_var, style="FieldLabel.TLabel").grid(
            row=4, column=0, sticky="w"
        )
        ttk.Entry(form_card, textvariable=self.price_var).grid(
            row=4, column=1, sticky="ew", pady=(0, 12)
        )

        ttk.Label(form_card, textvariable=self.stock_label_var, style="FieldLabel.TLabel").grid(
            row=5, column=0, sticky="w"
        )
        ttk.Entry(form_card, textvariable=self.stock_var).grid(
            row=5, column=1, sticky="ew", pady=(0, 16)
        )

        actions = ttk.Frame(form_card, style="Card.TFrame")
        actions.grid(row=6, column=0, columnspan=2, sticky="ew")
        for index in range(4):
            actions.grid_columnconfigure(index, weight=1)

        ttk.Button(
            actions,
            textvariable=self.add_button_text,
            command=self.add_product,
            style="Accent.TButton",
        ).grid(row=0, column=0, sticky="ew", padx=(0, 12))
        ttk.Button(
            actions,
            textvariable=self.update_button_text,
            command=self.update_product,
            style="Secondary.TButton",
        ).grid(row=0, column=1, sticky="ew", padx=(0, 12))
        ttk.Button(
            actions,
            textvariable=self.clear_button_text,
            command=self.clear_form,
            style="Secondary.TButton",
        ).grid(row=0, column=2, sticky="ew", padx=(0, 12))
        ttk.Button(
            actions,
            textvariable=self.refresh_button_text,
            command=self.refresh_products,
            style="Secondary.TButton",
        ).grid(row=0, column=3, sticky="ew")

        inventory_card = ttk.Frame(container, style="Card.TFrame", padding=24)
        inventory_card.grid(row=1, column=1, sticky="nsew")
        inventory_card.grid_rowconfigure(1, weight=1)
        inventory_card.grid_columnconfigure(0, weight=1)

        ttk.Label(inventory_card, textvariable=self.inventory_title_var, style="SectionTitle.TLabel").grid(
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
        for column in columns:
            anchor = tk.CENTER if column != "name" else tk.W
            width = 120 if column != "name" else 220
            self.tree.column(column, width=width, anchor=anchor)
        self.tree.configure(selectmode="browse")
        self.tree.grid(row=2, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(inventory_card, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=2, column=1, sticky="ns")

        self.tree.tag_configure("evenrow", background=PALETTE["surface"])
        self.tree.tag_configure("oddrow", background=PALETTE["surface_alt"])

        self.tree.bind("<Double-1>", self._on_tree_select)

    def apply_settings(self) -> None:
        self.hero_title_var.set(self.app.t("inventory.hero.title"))
        self.hero_subtitle_var.set(self.app.t("inventory.hero.subtitle"))
        self.form_title_var.set(self.app.t("inventory.card.form.title"))
        self.product_id_label_var.set(self.app.t("field.product_id"))
        self.name_label_var.set(self.app.t("field.name"))
        self.price_label_var.set(self.app.t("field.price"))
        self.stock_label_var.set(self.app.t("field.stock"))
        self.add_button_text.set(self.app.t("action.add_product"))
        self.update_button_text.set(self.app.t("action.update_product"))
        self.clear_button_text.set(self.app.t("action.clear"))
        self.refresh_button_text.set(self.app.t("action.refresh"))
        self.inventory_title_var.set(self.app.t("inventory.card.list.title"))

        headings = {
            "product_id": self.app.t("field.product_id"),
            "name": self.app.t("inventory.table.product"),
            "price": self.app.t("inventory.table.price"),
            "stock": self.app.t("inventory.table.stock"),
        }
        for column, label in headings.items():
            self.tree.heading(column, text=label)

        self.summary_var.set(self.app.t("inventory.hero.empty"))

    def _strip_currency(self, value: str) -> str:
        cleaned = ''.join(ch for ch in value if ch.isdigit() or ch in {'.', ',', '-'})
        return cleaned.replace(',', '')

    def _on_tree_select(self, _event) -> None:
        selected_item = self.tree.selection()
        if not selected_item:
            return
        item_values = self.tree.item(selected_item[0], "values")
        self.product_id_var.set(item_values[0])
        self.name_var.set(item_values[1])
        self.price_var.set(self._strip_currency(str(item_values[2])))
        self.stock_var.set(item_values[3])

    def _parse_product_from_form(self) -> Product:
        product_id = self.product_id_var.get().strip()
        name = self.name_var.get().strip()

        try:
            price = float(self.price_var.get())
            stock = int(self.stock_var.get())
        except ValueError as exc:
            raise ValueError(self.app.t("inventory.error.invalid")) from exc

        if price < 0 or stock < 0:
            raise ValueError(self.app.t("inventory.error.negative"))

        if not product_id or not name:
            raise ValueError(self.app.t("inventory.error.required"))

        return Product(product_id=product_id, name=name, price=price, stock=stock)

    def add_product(self) -> None:
        try:
            product = self._parse_product_from_form()
            self.db.add_product(product)
            messagebox.showinfo(self.app.t("dialog.success"), self.app.t("inventory.success.add"))
            self.refresh_products()
            self.clear_form()
            if self.on_inventory_change:
                self.on_inventory_change()
        except sqlite3.IntegrityError:
            messagebox.showerror(self.app.t("dialog.error"), self.app.t("inventory.error.duplicate"))
        except ValueError as exc:
            messagebox.showerror(self.app.t("dialog.error"), str(exc))

    def update_product(self) -> None:
        try:
            product = self._parse_product_from_form()
            self.db.update_product(product)
            messagebox.showinfo(self.app.t("dialog.success"), self.app.t("inventory.success.update"))
            self.refresh_products()
            self.clear_form()
            if self.on_inventory_change:
                self.on_inventory_change()
        except ValueError as exc:
            messagebox.showerror(self.app.t("dialog.error"), str(exc))
        except sqlite3.DatabaseError as exc:  # pragma: no cover - sqlite error propagation
            messagebox.showerror(
                self.app.t("dialog.error"),
                self.app.t("inventory.error.database", error=exc),
            )

    def clear_form(self) -> None:
        self.product_id_var.set("")
        self.name_var.set("")
        self.price_var.set("")
        self.stock_var.set("")

    def refresh_products(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        products = self.db.list_products()
        total_value = 0.0
        for index, product in enumerate(products):
            total_value += product.price * product.stock
            tag = "evenrow" if index % 2 == 0 else "oddrow"
            self.tree.insert(
                "",
                tk.END,
                values=(
                    product.product_id,
                    product.name,
                    self.app.format_money(product.price),
                    product.stock,
                ),
                tags=(tag,),
            )

        if products:
            summary = self.app.t(
                "inventory.hero.summary",
                count=len(products),
                value=self.app.format_money(total_value),
            )
        else:
            summary = self.app.t("inventory.hero.empty")
        self.summary_var.set(summary)
class SalesFrame(ttk.Frame):
    """GUI for handling the sales process."""

    def __init__(
        self,
        parent: tk.Widget,
        db: DatabaseManager,
        inventory_provider,
        on_sale_complete,
        app: "POSApp",
    ) -> None:
        super().__init__(parent, padding=20, style="Background.TFrame")
        self.db = db
        self.inventory_provider = inventory_provider
        self.on_sale_complete = on_sale_complete
        self.app = app
        self.cart: Dict[str, Dict[str, float]] = {}
        self.inventory_cache: Dict[str, Product] = {}
        self.last_sale: Optional[SaleRecord] = None

        self.cart_summary_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.product_id_var = tk.StringVar()
        self.quantity_var = tk.StringVar(value="1")
        self.subtotal_var = tk.StringVar()
        self.total_var = tk.StringVar()

        self.hero_title_var = tk.StringVar()
        self.hero_subtitle_var = tk.StringVar()
        self.categories_title_var = tk.StringVar()
        self.categories_subtitle_var = tk.StringVar()
        self.products_empty_var = tk.StringVar()
        self.remove_selected_text = tk.StringVar()
        self.clear_cart_text = tk.StringVar()
        self.summary_title_var = tk.StringVar()
        self.summary_subtitle_var = tk.StringVar()
        self.subtotal_label_var = tk.StringVar()
        self.balance_label_var = tk.StringVar()
        self.finalize_button_text = tk.StringVar()
        self.print_button_text = tk.StringVar()

        self.category_var = tk.StringVar(value="__all__")
        self._category_keys: List[str] = []
        self._product_card_frames: List[ttk.Frame] = []

        self.container = ttk.Frame(self, style="Background.TFrame")
        self.container.grid(row=0, column=0, sticky="nsew")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        self._build_ui()
        self.apply_settings()
        self._refresh_inventory_cache()
        self._update_totals()

    def _build_ui(self) -> None:
        container = self.container

        layout = ttk.Frame(container, style="Background.TFrame")
        layout.grid(row=0, column=0, sticky="nsew")
        layout.grid_columnconfigure(0, weight=0)
        layout.grid_columnconfigure(1, weight=1)
        layout.grid_columnconfigure(2, weight=0)
        layout.grid_rowconfigure(0, weight=1)

        self.category_panel = ttk.Frame(layout, style="SidePanel.TFrame", padding=(24, 28))
        self.category_panel.grid(row=0, column=0, sticky="nsw", padx=(0, 24))
        self.category_panel.grid_rowconfigure(2, weight=1)

        ttk.Label(
            self.category_panel,
            textvariable=self.categories_title_var,
            style="SidePanelTitle.TLabel",
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            self.category_panel,
            textvariable=self.categories_subtitle_var,
            style="SidePanelSubtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(6, 18))

        self.category_list = ttk.Frame(self.category_panel, style="SidePanel.TFrame")
        self.category_list.grid(row=2, column=0, sticky="nsew")

        products_panel = ttk.Frame(layout, style="Background.TFrame", padding=(12, 24))
        products_panel.grid(row=0, column=1, sticky="nsew")
        products_panel.grid_columnconfigure(0, weight=1)
        products_panel.grid_rowconfigure(1, weight=1)

        header = ttk.Frame(products_panel, style="Background.TFrame")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 18))
        header.grid_columnconfigure(0, weight=1)

        ttk.Label(header, textvariable=self.hero_title_var, style="WorkspaceTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            header,
            textvariable=self.hero_subtitle_var,
            style="WorkspaceSubtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))
        ttk.Label(
            header,
            textvariable=self.cart_summary_var,
            style="WorkspaceMeta.TLabel",
        ).grid(row=0, column=1, rowspan=2, sticky="ne")

        self.products_canvas = tk.Canvas(
            products_panel,
            highlightthickness=0,
            bd=0,
            background=PALETTE["bg"],
        )
        self.products_canvas.grid(row=1, column=0, sticky="nsew")

        self.products_scrollbar = ttk.Scrollbar(
            products_panel, orient=tk.VERTICAL, command=self.products_canvas.yview
        )
        self.products_scrollbar.grid(row=1, column=1, sticky="ns")
        self.products_canvas.configure(yscrollcommand=self.products_scrollbar.set)

        self.products_frame = ttk.Frame(self.products_canvas, style="Background.TFrame")
        self.products_window = self.products_canvas.create_window(
            (0, 0), window=self.products_frame, anchor="nw"
        )

        self.products_frame.bind(
            "<Configure>",
            lambda event: self.products_canvas.configure(scrollregion=self.products_canvas.bbox("all")),
        )
        self.products_canvas.bind(
            "<Configure>",
            lambda event: self.products_canvas.itemconfigure(self.products_window, width=event.width),
        )

        summary_panel = ttk.Frame(layout, style="SummaryPanel.TFrame", padding=(24, 28))
        summary_panel.grid(row=0, column=2, sticky="nse", padx=(24, 0))
        summary_panel.grid_rowconfigure(2, weight=1)

        ttk.Label(summary_panel, textvariable=self.summary_title_var, style="SummaryTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            summary_panel,
            textvariable=self.summary_subtitle_var,
            style="SummarySubtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 18))

        columns = ("product_id", "name", "quantity", "line_total")
        self.tree = ttk.Treeview(summary_panel, columns=columns, show="headings", height=10)
        widths = {"product_id": 110, "name": 180, "quantity": 80, "line_total": 120}
        anchors = {
            "product_id": tk.W,
            "name": tk.W,
            "quantity": tk.CENTER,
            "line_total": tk.E,
        }
        for column in columns:
            self.tree.column(column, width=widths[column], anchor=anchors[column], stretch=False)
        self.tree.grid(row=2, column=0, sticky="nsew")
        summary_panel.grid_rowconfigure(2, weight=1)

        tree_scroll = ttk.Scrollbar(summary_panel, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.grid(row=2, column=1, sticky="ns")

        self.tree.tag_configure("evenrow", background=PALETTE["surface"])
        self.tree.tag_configure("oddrow", background=PALETTE["surface_alt"])
        self.tree.bind("<Delete>", lambda _event: self.remove_selected_item())
        self.tree.bind("<Double-1>", lambda _event: self.remove_selected_item())

        actions = ttk.Frame(summary_panel, style="SummaryPanel.TFrame")
        actions.grid(row=3, column=0, sticky="ew", pady=(16, 0))
        actions.grid_columnconfigure(0, weight=1)
        actions.grid_columnconfigure(1, weight=1)

        ttk.Button(
            actions,
            textvariable=self.remove_selected_text,
            command=self.remove_selected_item,
            style="Ghost.TButton",
        ).grid(row=0, column=0, sticky="ew", padx=(0, 12))
        ttk.Button(
            actions,
            textvariable=self.clear_cart_text,
            command=self.clear_cart,
            style="Ghost.TButton",
        ).grid(row=0, column=1, sticky="ew")

        totals = ttk.Frame(summary_panel, style="SummaryPanel.TFrame")
        totals.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(24, 16))
        totals.grid_columnconfigure(1, weight=1)

        ttk.Label(totals, textvariable=self.subtotal_label_var, style="SummaryMeta.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(totals, textvariable=self.subtotal_var, style="SummaryValue.TLabel").grid(
            row=0, column=1, sticky="e"
        )
        ttk.Label(totals, textvariable=self.balance_label_var, style="SummaryMeta.TLabel").grid(
            row=1, column=0, sticky="w", pady=(8, 0)
        )
        ttk.Label(totals, textvariable=self.total_var, style="SummaryTotal.TLabel").grid(
            row=1, column=1, sticky="e", pady=(8, 0)
        )

        self.finalize_button = ttk.Button(
            summary_panel,
            textvariable=self.finalize_button_text,
            command=self.finalize_sale,
            style="Pay.TButton",
        )
        self.finalize_button.grid(row=5, column=0, columnspan=2, sticky="ew")

        self.print_button = ttk.Button(
            summary_panel,
            textvariable=self.print_button_text,
            command=self.print_invoice,
            style="Secondary.TButton",
        )
        self.print_button.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        self.print_button.state(["disabled"])

        self.status_label = ttk.Label(container, textvariable=self.status_var, style="Status.TLabel")
        self.status_label.grid(row=1, column=0, sticky="w", pady=(18, 0))

    def apply_settings(self) -> None:
        self.hero_title_var.set(self.app.t("sales.hero.title"))
        self.hero_subtitle_var.set(self.app.t("sales.hero.subtitle"))
        self.categories_title_var.set(self.app.t("sales.categories.title"))
        self.categories_subtitle_var.set(self.app.t("sales.categories.subtitle"))
        self.summary_title_var.set(self.app.t("sales.summary.title"))
        self.summary_subtitle_var.set(self.app.t("sales.summary.subtitle"))
        self.subtotal_label_var.set(self.app.t("label.subtotal"))
        self.balance_label_var.set(self.app.t("label.balance_due"))
        self.finalize_button_text.set(self.app.t("action.finalize_sale"))
        self.print_button_text.set(self.app.t("action.print_invoice"))
        self.remove_selected_text.set(self.app.t("action.remove_selected"))
        self.clear_cart_text.set(self.app.t("action.clear_cart"))
        self.products_empty_var.set(self.app.t("sales.products.empty"))

        headings = {
            "product_id": self.app.t("sales.cart.heading.product_id"),
            "name": self.app.t("sales.cart.heading.name"),
            "quantity": self.app.t("sales.cart.heading.quantity"),
            "line_total": self.app.t("sales.cart.heading.total"),
        }
        for column, text in headings.items():
            self.tree.heading(column, text=text)

        self._render_categories()
        self._render_product_cards()
        self._populate_cart_tree()
        self._update_totals()
        self.status_var.set(self.app.t("sales.status.prompt"))

    def _refresh_inventory_cache(self) -> None:
        products = list(self.inventory_provider())
        self.inventory_cache = {product.product_id: product for product in products}

        category_keys = sorted({self._category_key(product) for product in products})
        if "__uncategorized__" in category_keys:
            category_keys = [key for key in category_keys if key != "__uncategorized__"] + [
                "__uncategorized__"
            ]

        self._category_keys = ["__all__"] + category_keys
        if self.category_var.get() not in self._category_keys:
            self.category_var.set("__all__")

        self._render_categories()
        self._render_product_cards()

    def _render_categories(self) -> None:
        if not hasattr(self, "category_list"):
            return

        for child in self.category_list.winfo_children():
            child.destroy()

        if not self._category_keys:
            self._category_keys = ["__all__"]

        if self.category_var.get() not in self._category_keys:
            self.category_var.set("__all__")

        for key in self._category_keys:
            ttk.Radiobutton(
                self.category_list,
                text=self._format_category_label(key),
                value=key,
                variable=self.category_var,
                command=self._on_category_selected,
                style="Category.TRadiobutton",
                indicatoron=0,
                padding=12,
                takefocus=0,
            ).pack(fill="x", pady=6)

    def _on_category_selected(self) -> None:
        self._render_product_cards()

    def _format_category_label(self, key: str) -> str:
        if key == "__all__":
            return self.app.t("sales.categories.all")
        if key == "__uncategorized__":
            return self.app.t("sales.categories.uncategorized")
        return key

    def _category_key(self, product: Product) -> str:
        product_id = (product.product_id or "").strip()
        if "-" in product_id:
            prefix = product_id.split("-", 1)[0].replace("_", " ").strip()
            if prefix:
                return prefix.title()

        name = (product.name or "").strip()
        if not name:
            return "__uncategorized__"

        token = name.split()[0]
        cleaned = token.strip(".,")
        if not cleaned or cleaned.isdigit():
            return "__uncategorized__"
        return cleaned.title()

    def _category_matches(self, product: Product) -> bool:
        selected = self.category_var.get()
        if selected == "__all__":
            return True
        return self._category_key(product) == selected

    def _product_icon_for_category(self, category_key: str) -> str:
        base = category_key.lower().split()[0] if category_key else ""
        icon_map = {
            "coffee": "☕",
            "drink": "🥤",
            "juice": "🧃",
            "tea": "🍵",
            "pizza": "🍕",
            "burger": "🍔",
            "sandwich": "🥪",
            "salad": "🥗",
            "dessert": "🍰",
            "taco": "🌮",
            "pasta": "🍝",
        }
        return icon_map.get(base, "🛒")

    def _bind_card_click(self, widget: tk.Widget, product_id: str) -> None:
        widget.bind(
            "<Button-1>", lambda _event, pid=product_id: self._quick_add(pid), add="+"
        )
        if hasattr(widget, "winfo_children"):
            for child in widget.winfo_children():
                self._bind_card_click(child, product_id)

    def _render_product_cards(self) -> None:
        if not hasattr(self, "products_frame"):
            return

        for child in self.products_frame.winfo_children():
            child.destroy()
        self._product_card_frames.clear()

        for col in range(6):
            self.products_frame.grid_columnconfigure(col, weight=0)

        visible_products = [
            product
            for product in self.inventory_cache.values()
            if self._category_matches(product)
        ]

        if not visible_products:
            message = (
                self.products_empty_var.get()
                if not self.inventory_cache
                else self.app.t("sales.products.empty_category")
            )
            ttk.Label(
                self.products_frame,
                text=message,
                style="EmptyState.TLabel",
                anchor="center",
                justify="center",
                wraplength=360,
            ).grid(row=0, column=0, sticky="nsew", padx=24, pady=48)
            self.products_frame.grid_columnconfigure(0, weight=1)
            return

        columns = min(3, max(1, len(visible_products)))
        for column in range(columns):
            self.products_frame.grid_columnconfigure(column, weight=1)

        for index, product in enumerate(visible_products):
            row = index // columns
            column = index % columns

            card = ttk.Frame(self.products_frame, style="ProductCard.TFrame", padding=18)
            card.grid(row=row, column=column, padx=12, pady=12, sticky="nsew")
            card.grid_propagate(False)
            card.configure(width=190, height=160)

            icon_label = ttk.Label(
                card,
                text=self._product_icon_for_category(self._category_key(product)),
                style="ProductIcon.TLabel",
            )
            icon_label.pack(pady=(0, 12))

            name_label = ttk.Label(
                card,
                text=product.name,
                style="ProductName.TLabel",
                justify="center",
                wraplength=150,
            )
            name_label.pack(fill="x")

            price_label = ttk.Label(
                card,
                text=self.app.format_money(product.price),
                style="ProductPrice.TLabel",
            )
            price_label.pack(pady=(8, 0))

            stock_label = ttk.Label(
                card,
                text=f"{self.app.t('field.stock')}: {product.stock}",
                style="ProductMeta.TLabel",
            )
            stock_label.pack(pady=(2, 0))

            self._bind_card_click(card, product.product_id)
            self._product_card_frames.append(card)

    def _quick_add(self, product_id: str) -> None:
        self.product_id_var.set(product_id)
        self.quantity_var.set("1")
        self.add_to_cart()

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
            messagebox.showerror(
                self.app.t("sales.dialog.invalid_quantity"),
                self.app.t("sales.error.quantity"),
            )
            self._set_status(self.app.t("sales.error.quantity"))
            return

        if product_id not in self.inventory_cache:
            messagebox.showerror(self.app.t("dialog.error"), self.app.t("sales.status.not_found"))
            self._set_status(self.app.t("sales.status.not_found"))
            return

        product = self.inventory_cache[product_id]
        if quantity > product.stock:
            messagebox.showerror(
                self.app.t("sales.dialog.stock"),
                self.app.t("sales.error.insufficient_stock", stock=product.stock, name=product.name),
            )
            self._set_status(
                self.app.t("sales.status.stock", stock=product.stock, name=product.name)
            )
            return

        if product_id in self.cart:
            new_qty = self.cart[product_id]["quantity"] + quantity
            if new_qty > product.stock:
                messagebox.showerror(
                    self.app.t("sales.dialog.stock"),
                    self.app.t("sales.error.insufficient_stock", stock=product.stock, name=product.name),
                )
                self._set_status(
                    self.app.t("sales.status.stock", stock=product.stock, name=product.name)
                )
                return
            self.cart[product_id]["quantity"] = new_qty
            self.cart[product_id]["line_total"] = new_qty * product.price
            status_message = self.app.t(
                "sales.status.updated",
                name=product.name,
                quantity=new_qty,
            )
        else:
            self.cart[product_id] = {
                "name": product.name,
                "price": product.price,
                "quantity": quantity,
                "line_total": quantity * product.price,
            }
            status_message = self.app.t(
                "sales.status.added",
                name=product.name,
                quantity=quantity,
            )

        self._populate_cart_tree()
        self._update_totals()
        self._set_status(status_message, accent=True)
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
                    data["quantity"],
                    self.app.format_money(data["line_total"]),
                ),
                tags=(tag,),
            )

    def _update_totals(self) -> None:
        subtotal = sum(item["line_total"] for item in self.cart.values())
        total = subtotal
        self.subtotal_var.set(self.app.format_money(subtotal))
        self.total_var.set(self.app.format_money(total))

        if self.cart:
            item_count = sum(item["quantity"] for item in self.cart.values())
            label_key = "sales.hero.item" if item_count == 1 else "sales.hero.items"
            summary = self.app.t(
                "sales.hero.summary",
                count=item_count,
                label=self.app.t(label_key),
                total=self.app.format_money(total),
            )
            self.cart_summary_var.set(summary)
        else:
            self.cart_summary_var.set(self.app.t("sales.hero.empty"))
            self.subtotal_var.set(self.app.format_money(0.0))
            self.total_var.set(self.app.format_money(0.0))

    def clear_cart(self, notify: bool = True) -> None:
        self.cart.clear()
        self._populate_cart_tree()
        self._update_totals()
        if notify:
            self._set_status(self.app.t("sales.status.cleared"))
        self.print_button.state(["disabled"])

    def remove_selected_item(self) -> None:
        selection = self.tree.selection()
        if not selection:
            self._set_status(self.app.t("sales.status.select_item"))
            return
        product_id = self.tree.item(selection[0], "values")[0]
        if product_id in self.cart:
            removed_name = self.cart[product_id]["name"]
            del self.cart[product_id]
            self._populate_cart_tree()
            self._update_totals()
            self._set_status(self.app.t("sales.status.removed", name=removed_name))
        else:
            self._set_status(self.app.t("sales.status.not_found"))

    def finalize_sale(self) -> None:
        if not self.cart:
            messagebox.showwarning(
                self.app.t("sales.dialog.empty"),
                self.app.t("sales.warning.empty"),
            )
            self._set_status(self.app.t("sales.warning.add_items"))
            return

        self._refresh_inventory_cache()

        for product_id, item in self.cart.items():
            product = self.inventory_cache.get(product_id)
            if product is None:
                message = self.app.t("sales.status.no_longer_exists", product_id=product_id)
                messagebox.showerror(self.app.t("dialog.error"), message)
                self._set_status(message)
                return
            if item["quantity"] > product.stock:
                messagebox.showerror(
                    self.app.t("sales.dialog.stock"),
                    self.app.t("sales.error.insufficient_stock", stock=product.stock, name=product.name),
                )
                self._set_status(
                    self.app.t("sales.status.stock", stock=product.stock, name=product.name)
                )
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

        try:
            with self.db._get_connection() as conn:
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
            messagebox.showerror(
                self.app.t("dialog.error"),
                self.app.t("sales.error.database", error=exc),
            )
            self._set_status(self.app.t("sales.error.generic"))
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

        messagebox.showinfo(
            self.app.t("dialog.success"),
            self.app.t("sales.success.total", total=self.app.format_money(total)),
        )
        self.clear_cart(notify=False)
        self._refresh_inventory_cache()
        timestamp = datetime.now().strftime('%I:%M:%S %p').lstrip('0')
        self._set_status(
            self.app.t("sales.status.ready", timestamp=timestamp),
            accent=True,
        )

        if self.on_sale_complete:
            try:
                self.on_sale_complete(sale_record)
            except Exception:  # pragma: no cover - guard callbacks
                pass

    def print_invoice(self) -> None:
        if not self.last_sale:
            messagebox.showinfo(
                self.app.t("sales.invoice.none.title"),
                self.app.t("sales.invoice.none.message"),
            )
            return

        InvoicePreview(self, self.app, format_invoice(self.last_sale, self.app))
class PurchaseHistoryFrame(ttk.Frame):
    """GUI for reviewing and exporting past sales."""

    def __init__(self, parent: tk.Widget, db: DatabaseManager, app: "POSApp") -> None:
        super().__init__(parent, padding=20, style="Background.TFrame")
        self.db = db
        self.app = app
        self.sales: List[SaleRecord] = []
        self.summary_var = tk.StringVar()

        self.hero_title_var = tk.StringVar()
        self.hero_subtitle_var = tk.StringVar()
        self.history_title_var = tk.StringVar()
        self.refresh_text_var = tk.StringVar()
        self.details_title_var = tk.StringVar()
        self.open_invoice_text = tk.StringVar()

        self.container = ttk.Frame(self, style="Background.TFrame")
        self.container.grid(row=0, column=0, sticky="nsew")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.container.grid_rowconfigure(1, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self._build_ui()
        self.apply_settings()
        self.refresh_history()

    def _build_ui(self) -> None:
        container = self.container

        hero = ttk.Frame(container, style="Hero.TFrame", padding=(24, 18))
        hero.grid(row=0, column=0, sticky="ew", pady=(0, 24))
        hero.grid_columnconfigure(0, weight=1)

        ttk.Label(hero, textvariable=self.hero_title_var, style="HeroTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            hero,
            textvariable=self.hero_subtitle_var,
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

        ttk.Label(header, textvariable=self.history_title_var, style="SectionTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Button(
            header,
            textvariable=self.refresh_text_var,
            command=self.refresh_history,
            style="Secondary.TButton",
        ).grid(row=0, column=1, sticky="e")

        ttk.Separator(history_card).grid(row=1, column=0, sticky="ew", pady=(8, 16))

        columns = ("sale_id", "timestamp", "items", "subtotal", "total")
        self.tree = ttk.Treeview(history_card, columns=columns, show="headings", height=12)
        widths = {
            "sale_id": 80,
            "timestamp": 160,
            "items": 80,
            "subtotal": 120,
            "total": 120,
        }
        for column in columns:
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

        ttk.Label(details_card, textvariable=self.details_title_var, style="SectionTitle.TLabel").grid(
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
            textvariable=self.open_invoice_text,
            command=self.open_invoice,
            style="Secondary.TButton",
        )
        self.view_button.grid(row=3, column=0, sticky="ew", pady=(16, 0))
        self.view_button.state(["disabled"])

    def apply_settings(self) -> None:
        self.hero_title_var.set(self.app.t("history.hero.title"))
        self.hero_subtitle_var.set(self.app.t("history.hero.subtitle"))
        self.history_title_var.set(self.app.t("history.card.title"))
        self.refresh_text_var.set(self.app.t("history.refresh"))
        self.details_title_var.set(self.app.t("history.details.title"))
        self.open_invoice_text.set(self.app.t("history.action.open"))
        self.summary_var.set(self.app.t("history.hero.empty"))

        headings = {
            "sale_id": self.app.t("history.table.sale_id"),
            "timestamp": self.app.t("history.table.timestamp"),
            "items": self.app.t("history.table.items"),
            "subtotal": self.app.t("history.table.subtotal"),
            "total": self.app.t("history.table.total"),
        }
        for column, text in headings.items():
            self.tree.heading(column, text=text)

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
                    self.app.format_money(sale.subtotal),
                    self.app.format_money(sale.total),
                ),
                tags=(tag,),
            )

        if self.sales:
            summary = self.app.t(
                "history.hero.summary",
                count=len(self.sales),
                revenue=self.app.format_money(total_revenue),
            )
        else:
            summary = self.app.t("history.hero.empty")
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
            self.detail_text.insert(tk.END, self.app.t("history.details.none"))
            self.detail_text.configure(state="disabled")
            return

        self.view_button.state(["!disabled"])
        details_lines = [
            f"{self.app.t('history.table.sale_id')} {sale.sale_id}",
            sale.timestamp.strftime("%B %d, %Y • %I:%M %p").lstrip("0").replace(" 0", " "),
            "",
        ]
        for item in sale.items:
            details_lines.append(
                self.app.t(
                    "history.details.line",
                    quantity=item["quantity"],
                    name=item["name"],
                    price=self.app.format_money(item["price"]),
                    total=self.app.format_money(item["line_total"]),
                )
            )
        details_lines.append("")
        details_lines.append(
            self.app.t("history.details.subtotal", value=self.app.format_money(sale.subtotal))
        )
        details_lines.append(
            self.app.t("history.details.total", value=self.app.format_money(sale.total))
        )

        self.detail_text.configure(state="normal")
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.insert(tk.END, "\n".join(details_lines))
        self.detail_text.configure(state="disabled")

    def open_invoice(self) -> None:
        sale = self._get_selected_sale()
        if sale is None:
            messagebox.showinfo(
                self.app.t("history.info.none"),
                self.app.t("history.info.select"),
            )
            return

        InvoicePreview(self, self.app, format_invoice(sale, self.app))
def format_invoice(sale: SaleRecord, app: "POSApp") -> str:
    """Create a printable invoice string from a sale."""

    header_width = 72
    lines = [
        app.t("invoice.header").center(header_width),
        "=" * header_width,
        f"{app.t('invoice.sale_number')} {sale.sale_id}",
        f"{app.t('invoice.completed')} {sale.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * header_width,
        app.t(
            "invoice.columns",
            id=app.t("invoice.column.id"),
            name=app.t("invoice.column.product"),
            qty=app.t("invoice.column.qty"),
            price=app.t("invoice.column.price"),
            total=app.t("invoice.column.total"),
        ),
        "-" * header_width,
    ]

    for item in sale.items or []:
        name = str(item.get("name", ""))
        display_name = (name[:23] + "...") if len(name) > 26 else name
        quantity = int(item.get("quantity", 0))
        price = float(item.get("price", 0.0))
        line_total = float(item.get("line_total", quantity * price))
        price_str = app.format_money(price)
        total_str = app.format_money(line_total)
        lines.append(
            f"{str(item.get('product_id', '')):<10}"
            f"{display_name:<26}"
            f"{quantity:>5}"
            f"{price_str:>16}"
            f"{total_str:>15}"
        )

    lines.append("-" * header_width)
    subtotal_str = app.format_money(sale.subtotal)
    total_str = app.format_money(sale.total)
    lines.append(f"{app.t('invoice.subtotal'):>56}{subtotal_str:>16}")
    lines.append(f"{app.t('invoice.total'):>56}{total_str:>16}")
    lines.append("=" * header_width)
    lines.append(app.t("invoice.footer"))

    return "\n".join(lines)
class InvoicePreview(tk.Toplevel):
    """Preview window that supports saving or printing invoices."""

    def __init__(self, parent: tk.Widget, app: "POSApp", invoice_text: str) -> None:
        super().__init__(parent)
        self.app = app
        self.title(self.app.t("invoice.title"))
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

        ttk.Label(container, text=self.app.t("invoice.title"), style="SectionTitle.TLabel").grid(
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
            text=self.app.t("invoice.save"),
            command=self._save_invoice,
            style="Secondary.TButton",
        ).grid(row=0, column=0, sticky="ew", padx=(0, 12))
        ttk.Button(
            button_bar,
            text=self.app.t("invoice.print"),
            command=self._send_to_printer,
            style="Accent.TButton",
        ).grid(row=0, column=1, sticky="ew", padx=(0, 12))
        ttk.Button(
            button_bar,
            text=self.app.t("invoice.close"),
            command=self.destroy,
            style="Secondary.TButton",
        ).grid(row=0, column=2, sticky="ew")

    def _save_invoice(self) -> None:
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*")),
            title=self.app.t("invoice.save.title"),
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(self.invoice_text)
        except OSError as exc:
            messagebox.showerror(
                self.app.t("dialog.error"),
                self.app.t("invoice.save.error", error=exc),
            )
            return

        messagebox.showinfo(
            self.app.t("dialog.success"),
            self.app.t("invoice.save.success", path=file_path),
        )

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
                    raise RuntimeError(
                        "Printing is not supported on this Windows configuration."
                    )
            elif system in {"darwin", "linux"}:
                subprocess.run(["lp", tmp_path], check=True)
            else:
                raise RuntimeError("Printing is not supported on this platform.")

            messagebox.showinfo(
                self.app.t("dialog.success"),
                self.app.t("invoice.print.sent"),
            )
        except FileNotFoundError:
            messagebox.showerror(
                self.app.t("dialog.error"),
                self.app.t("invoice.print.missing"),
            )
        except (OSError, subprocess.CalledProcessError, RuntimeError) as exc:
            messagebox.showerror(
                self.app.t("dialog.error"),
                self.app.t("invoice.print.error", error=exc),
            )
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass


class SettingsFrame(ttk.Frame):
    """Preferences panel for language and currency."""

    def __init__(self, parent: tk.Widget, app: "POSApp") -> None:
        super().__init__(parent, padding=20, style="Background.TFrame")
        self.app = app
        self.language_var = tk.StringVar()
        self.currency_var = tk.StringVar()
        self.notice_var = tk.StringVar()

        self.hero_title_var = tk.StringVar()
        self.hero_subtitle_var = tk.StringVar()
        self.language_label_var = tk.StringVar()
        self.currency_label_var = tk.StringVar()
        self.apply_button_text = tk.StringVar()

        self.container = ttk.Frame(self, style="Background.TFrame")
        self.container.grid(row=0, column=0, sticky="nsew")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self._build_ui()
        self.apply_settings()

    def _build_ui(self) -> None:
        container = self.container

        hero = ttk.Frame(container, style="Hero.TFrame", padding=(24, 18))
        hero.grid(row=0, column=0, sticky="ew", pady=(0, 24))
        hero.grid_columnconfigure(0, weight=1)

        ttk.Label(hero, textvariable=self.hero_title_var, style="HeroTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            hero,
            textvariable=self.hero_subtitle_var,
            style="HeroSubtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))
        ttk.Label(hero, textvariable=self.notice_var, style="HeroStat.TLabel").grid(
            row=2, column=0, sticky="w", pady=(16, 0)
        )

        card = ttk.Frame(container, style="Card.TFrame", padding=24)
        card.grid(row=1, column=0, sticky="nsew")
        card.grid_columnconfigure(1, weight=1)

        ttk.Label(card, textvariable=self.language_label_var, style="FieldLabel.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        self.language_combo = ttk.Combobox(
            card,
            textvariable=self.language_var,
            state="readonly",
            values=self._language_options(),
        )
        self.language_combo.grid(row=0, column=1, sticky="ew", pady=(0, 16))

        ttk.Label(card, textvariable=self.currency_label_var, style="FieldLabel.TLabel").grid(
            row=1, column=0, sticky="w"
        )
        self.currency_combo = ttk.Combobox(
            card,
            textvariable=self.currency_var,
            state="readonly",
            values=self._currency_options(),
        )
        self.currency_combo.grid(row=1, column=1, sticky="ew", pady=(0, 16))

        ttk.Button(
            card,
            textvariable=self.apply_button_text,
            command=self._apply,
            style="Accent.TButton",
        ).grid(row=2, column=0, columnspan=2, sticky="ew")

    def _language_options(self) -> List[str]:
        return [SUPPORTED_LANGUAGES[code]["name"] for code in SUPPORTED_LANGUAGES]

    def _currency_options(self) -> List[str]:
        return [get_currency_display(code) for code in SUPPORTED_CURRENCIES]

    def apply_settings(self) -> None:
        self.hero_title_var.set(self.app.t("settings.hero.title"))
        self.hero_subtitle_var.set(self.app.t("settings.hero.subtitle"))
        self.language_label_var.set(self.app.t("settings.language.label"))
        self.currency_label_var.set(self.app.t("settings.currency.label"))
        self.apply_button_text.set(self.app.t("settings.apply"))
        self.notice_var.set(self.app.t("settings.notice"))

        current_language = self.app.settings.get("language", DEFAULT_LANGUAGE)
        current_currency = self.app.settings.get("currency", DEFAULT_CURRENCY)

        self.language_combo["values"] = self._language_options()
        self.currency_combo["values"] = self._currency_options()

        language_name = SUPPORTED_LANGUAGES.get(current_language, SUPPORTED_LANGUAGES[DEFAULT_LANGUAGE])["name"]
        currency_display = get_currency_display(current_currency)
        self.language_var.set(language_name)
        self.currency_var.set(currency_display)

    def _apply(self) -> None:
        language_selection = self.language_var.get()
        currency_selection = self.currency_var.get()

        language_code = next(
            (code for code, data in SUPPORTED_LANGUAGES.items() if data["name"] == language_selection),
            self.app.settings.get("language", DEFAULT_LANGUAGE),
        )
        currency_code = next(
            (code for code in SUPPORTED_CURRENCIES if get_currency_display(code) == currency_selection),
            self.app.settings.get("currency", DEFAULT_CURRENCY),
        )

        self.app.update_settings(language_code, currency_code)
        self.notice_var.set(
            self.app.t(
                "settings.applied.status",
                language=SUPPORTED_LANGUAGES[language_code]["name"],
                currency=get_currency_display(currency_code),
            )
        )
class POSApp(tk.Tk):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()
        self.db = DatabaseManager(DB_FILE)
        self.settings = self.db.get_app_settings()

        self.title(self.t("app.title"))
        self.geometry("1100x720")
        self.configure(bg=PALETTE["bg"])
        self.option_add("*Font", (FONT_FAMILY, 11))

        self.style = ttk.Style(self)
        self._configure_style()

        self._build_ui()
        self.apply_settings()

    def t(self, key: str, **kwargs: Any) -> str:
        language = self.settings.get("language", DEFAULT_LANGUAGE)
        return translate(language, key, **kwargs)

    def format_money(self, amount: float) -> str:
        currency = self.settings.get("currency", DEFAULT_CURRENCY)
        return format_currency(amount, currency)

    def _configure_style(self) -> None:
        style = self.style
        if "clam" in style.theme_names():
            style.theme_use("clam")

        self.nav_font = tkfont.Font(family=FONT_FAMILY, size=12, weight="bold")

        style.configure("TFrame", background=PALETTE["bg"])
        style.configure("Background.TFrame", background=PALETTE["bg"])
        style.configure("NavBar.TFrame", background=PALETTE["surface"], relief="flat", borderwidth=0)
        style.configure("Card.TFrame", background=PALETTE["surface"], relief="flat", borderwidth=0)
        style.configure("SidePanel.TFrame", background=PALETTE["panel"], relief="flat", borderwidth=0)
        style.configure("SummaryPanel.TFrame", background=PALETTE["surface"], relief="flat", borderwidth=0)
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
            "SidePanelTitle.TLabel",
            background=PALETTE["panel"],
            foreground=PALETTE["text"],
            font=(FONT_FAMILY, 18, "bold"),
        )
        style.configure(
            "SidePanelSubtitle.TLabel",
            background=PALETTE["panel"],
            foreground=PALETTE["muted"],
            font=(FONT_FAMILY, 11),
        )
        style.configure(
            "WorkspaceTitle.TLabel",
            background=PALETTE["bg"],
            foreground=PALETTE["text"],
            font=(FONT_FAMILY, 26, "bold"),
        )
        style.configure(
            "WorkspaceSubtitle.TLabel",
            background=PALETTE["bg"],
            foreground=PALETTE["muted"],
            font=(FONT_FAMILY, 12),
        )
        style.configure(
            "WorkspaceMeta.TLabel",
            background=PALETTE["bg"],
            foreground=PALETTE["muted"],
            font=(FONT_FAMILY, 11, "bold"),
        )
        style.configure(
            "SummaryTitle.TLabel",
            background=PALETTE["surface"],
            foreground=PALETTE["text"],
            font=(FONT_FAMILY, 17, "bold"),
        )
        style.configure(
            "SummarySubtitle.TLabel",
            background=PALETTE["surface"],
            foreground=PALETTE["muted"],
            font=(FONT_FAMILY, 11),
        )
        style.configure(
            "SummaryMeta.TLabel",
            background=PALETTE["surface"],
            foreground=PALETTE["muted"],
            font=(FONT_FAMILY, 11),
        )
        style.configure(
            "SummaryValue.TLabel",
            background=PALETTE["surface"],
            foreground=PALETTE["text"],
            font=(FONT_FAMILY, 14, "bold"),
        )
        style.configure(
            "SummaryTotal.TLabel",
            background=PALETTE["surface"],
            foreground=PALETTE["primary"],
            font=(FONT_FAMILY, 24, "bold"),
        )
        style.configure(
            "ProductCard.TFrame",
            background=PALETTE["surface"],
            borderwidth=1,
            relief="solid",
        )
        style.configure(
            "ProductIcon.TLabel",
            background=PALETTE["surface"],
            foreground=PALETTE["accent"],
            font=(FONT_FAMILY, 28),
        )
        style.configure(
            "ProductName.TLabel",
            background=PALETTE["surface"],
            foreground=PALETTE["text"],
            font=(FONT_FAMILY, 12, "bold"),
        )
        style.configure(
            "ProductPrice.TLabel",
            background=PALETTE["surface"],
            foreground=PALETTE["muted"],
            font=(FONT_FAMILY, 11, "bold"),
        )
        style.configure(
            "ProductMeta.TLabel",
            background=PALETTE["surface"],
            foreground=PALETTE["muted"],
            font=(FONT_FAMILY, 10),
        )
        style.configure(
            "EmptyState.TLabel",
            background=PALETTE["bg"],
            foreground=PALETTE["muted"],
            font=(FONT_FAMILY, 12),
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
        style.configure(
            "NavCurrent.TLabel",
            background=PALETTE["surface"],
            foreground=PALETTE["muted"],
            font=(FONT_FAMILY, 12, "bold"),
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
            "Pay.TButton",
            background=PALETTE["primary"],
            foreground="#ffffff",
            font=(FONT_FAMILY, 14, "bold"),
            padding=(20, 12),
        )
        style.map(
            "Pay.TButton",
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
            "Ghost.TButton",
            background=PALETTE["panel"],
            foreground=PALETTE["muted"],
            padding=(12, 8),
            relief="solid",
            borderwidth=1,
        )
        style.map(
            "Ghost.TButton",
            background=[("active", PALETTE["surface_alt"]), ("pressed", PALETTE["surface_alt"])],
            foreground=[("active", PALETTE["text"]), ("pressed", PALETTE["text"])],
        )
        style.configure(
            "Category.TRadiobutton",
            background=PALETTE["panel"],
            foreground=PALETTE["muted"],
            font=(FONT_FAMILY, 12, "bold"),
            relief="flat",
            borderwidth=0,
            focuscolor=PALETTE["panel"],
        )
        style.map(
            "Category.TRadiobutton",
            background=[
                ("selected", PALETTE["surface"]),
                ("active", PALETTE["surface_alt"]),
            ],
            foreground=[("selected", PALETTE["text"]), ("active", PALETTE["text"])],
        )
        style.configure(
            "Nav.TMenubutton",
            background=PALETTE["primary"],
            foreground="#ffffff",
            font=self.nav_font,
            padding=(18, 12),
            relief="flat",
        )
        style.map(
            "Nav.TMenubutton",
            background=[("active", PALETTE["primary_dark"]), ("pressed", PALETTE["primary_dark"])],
            foreground=[("disabled", "#cbd5f5")],
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
            background=PALETTE["panel"],
            foreground=PALETTE["text"],
            font=(FONT_FAMILY, 11, "bold"),
            relief="flat",
        )
        style.map(
            "Treeview.Heading",
            background=[("active", PALETTE["surface_alt"])],
            foreground=[("active", PALETTE["text"])],
        )

        style.configure("TScrollbar", troughcolor=PALETTE["surface"], background=PALETTE["primary"])

    def _build_ui(self) -> None:
        self.container = ttk.Frame(self, style="Background.TFrame")
        self.container.pack(fill=tk.BOTH, expand=True)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(1, weight=1)

        self.navbar = ttk.Frame(self.container, style="NavBar.TFrame", padding=(24, 18))
        self.navbar.grid(row=0, column=0, sticky="ew")
        self.navbar.grid_columnconfigure(0, weight=0)
        self.navbar.grid_columnconfigure(1, weight=1)

        self.nav_button_text = tk.StringVar()
        self.nav_button = ttk.Menubutton(
            self.navbar,
            textvariable=self.nav_button_text,
            style="Nav.TMenubutton",
            direction="below",
        )
        self.nav_button.grid(row=0, column=0, sticky="w", padx=(0, 16))

        self.navigation_menu = tk.Menu(self.nav_button, tearoff=0)
        self.nav_button["menu"] = self.navigation_menu
        self.navigation_menu.configure(font=self.nav_font)

        self.nav_current_view_var = tk.StringVar()
        self.nav_current_view_label = ttk.Label(
            self.navbar,
            textvariable=self.nav_current_view_var,
            style="NavCurrent.TLabel",
        )
        self.nav_current_view_label.grid(row=0, column=1, sticky="e", padx=(16, 0))

        self.active_view = tk.StringVar(value="sales")
        self._current_view: Optional[str] = None

        self.content = ttk.Frame(self.container, style="Background.TFrame")
        self.content.grid(row=1, column=0, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self.sales_frame = SalesFrame(
            self.content,
            db=self.db,
            inventory_provider=self.db.list_products,
            on_sale_complete=self._handle_sale_complete,
            app=self,
        )

        self.product_manager = ProductManagerFrame(
            self.content,
            db=self.db,
            on_inventory_change=self._notify_inventory_change,
            app=self,
        )

        self.history_frame = PurchaseHistoryFrame(self.content, db=self.db, app=self)
        self.settings_frame = SettingsFrame(self.content, app=self)

        self.views = {
            "sales": {"frame": self.sales_frame, "label_key": "tab.sales"},
            "products": {"frame": self.product_manager, "label_key": "tab.products"},
            "history": {"frame": self.history_frame, "label_key": "tab.history"},
            "settings": {"frame": self.settings_frame, "label_key": "tab.settings"},
        }

        self._nav_entries: Dict[str, int] = {}
        self._nav_base_labels: Dict[str, str] = {}
        for key in ["sales", "products", "history", "settings"]:
            view = self.views[key]
            frame = view["frame"]
            frame.grid(row=0, column=0, sticky="nsew")
            frame.grid_remove()

            base_label = self.t(view["label_key"])
            self.navigation_menu.add_radiobutton(
                label=base_label,
                variable=self.active_view,
                value=key,
                command=lambda target=key: self._show_view(target),
            )
            self._nav_entries[key] = self.navigation_menu.index("end")
            self._nav_base_labels[key] = base_label

        self._update_nav_geometry()

        self._show_view("sales")

    def apply_settings(self) -> None:
        self.title(self.t("app.title"))

        if hasattr(self, "nav_button_text"):
            self.nav_button_text.set(f"{self.t('menu.navigate')} ▾")
        if hasattr(self, "navigation_menu"):
            if not hasattr(self, "_nav_base_labels"):
                self._nav_base_labels = {}
            for key, entry_index in self._nav_entries.items():
                label_key = self.views[key]["label_key"]
                base_label = self.t(label_key)
                self._nav_base_labels[key] = base_label
                self.navigation_menu.entryconfig(entry_index, label=base_label)
            self._update_nav_geometry()
        if hasattr(self, "nav_current_view_var") and self._current_view:
            current_label_key = self.views[self._current_view]["label_key"]
            self.nav_current_view_var.set(self.t(current_label_key))

        self.product_manager.apply_settings()
        self.product_manager.refresh_products()

        self.sales_frame.apply_settings()
        self.sales_frame._refresh_inventory_cache()
        self.sales_frame._populate_cart_tree()
        self.sales_frame._update_totals()

        self.history_frame.apply_settings()
        self.history_frame.refresh_history()

        self.settings_frame.apply_settings()

    def _show_view(self, key: str) -> None:
        if key not in self.views:
            return

        if self._current_view is not None:
            self.views[self._current_view]["frame"].grid_remove()

        frame = self.views[key]["frame"]
        frame.grid()
        self._current_view = key

        if self.active_view.get() != key:
            self.active_view.set(key)

        if hasattr(self, "nav_current_view_var"):
            label_key = self.views[key]["label_key"]
            self.nav_current_view_var.set(self.t(label_key))

    def _pad_menu_label(self, label: str, target_width: int, font: tkfont.Font) -> str:
        if target_width <= 0:
            return label

        padded = label
        spacer = "\u2007"
        if font.measure(spacer) == 0:
            spacer = " "

        while font.measure(padded) < target_width:
            padded += spacer

        return padded

    def _update_nav_geometry(self) -> None:
        if not hasattr(self, "nav_button") or not hasattr(self, "navigation_menu"):
            return

        if not getattr(self, "_nav_entries", None):
            return

        nav_font = getattr(self, "nav_font", tkfont.Font(family=FONT_FAMILY, size=12, weight="bold"))
        base_labels = getattr(self, "_nav_base_labels", {})
        texts = [base_labels.get(key, "") for key in self._nav_entries]
        texts = [text for text in texts if text]

        if not texts:
            return

        zero_width = nav_font.measure("0") or 1
        max_text_width = max(nav_font.measure(text) for text in texts)
        char_width = max(int(round(max_text_width / zero_width)) + 4, 8)
        self.nav_button.configure(width=char_width)

        self.update_idletasks()
        target_width = self.nav_button.winfo_width()
        if target_width <= 0:
            target_width = self.nav_button.winfo_reqwidth()

        menu_font = tkfont.Font(font=self.navigation_menu.cget("font"))

        for key, entry_index in self._nav_entries.items():
            base_label = base_labels.get(key, "")
            self.navigation_menu.entryconfig(entry_index, label=base_label)

        self.navigation_menu.update_idletasks()
        inner_target = max(target_width - 24, 0)

        for key, entry_index in self._nav_entries.items():
            base_label = base_labels.get(key, "")
            padded_label = self._pad_menu_label(base_label, inner_target, menu_font)
            self.navigation_menu.entryconfig(entry_index, label=padded_label)

    def update_settings(self, language: str, currency: str) -> None:
        if language not in SUPPORTED_LANGUAGES:
            language = DEFAULT_LANGUAGE
        if currency not in SUPPORTED_CURRENCIES:
            currency = DEFAULT_CURRENCY

        self.settings["language"] = language
        self.settings["currency"] = currency
        self.db.update_app_settings(language, currency)
        self.apply_settings()

    def _notify_inventory_change(self) -> None:
        self.sales_frame._refresh_inventory_cache()
        self.sales_frame._populate_cart_tree()
        self.sales_frame._update_totals()

    def _handle_sale_complete(self, _sale: SaleRecord) -> None:
        self.history_frame.refresh_history()

def main() -> None:
    app = POSApp()
    app.mainloop()


if __name__ == "__main__":
    main()
