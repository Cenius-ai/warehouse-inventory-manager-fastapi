"""Idempotent seed data for the inventory manager.

Run standalone: python3 -m seed   (from the project root)
Or imported and called from the app lifespan.
"""

import datetime
import os

from sqlalchemy.orm import Session

from database import engine, SessionLocal, Base
from models import User, Category, Product, StockMovement, MovementType
from auth import hash_password

_DEMO_PASSWORD = os.environ.get("DEMO_PASSWORD") or "cenius"
_ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD") or "admin123"


def seed_data(db: Session | None = None):
    """Idempotent: checks for existing records before inserting."""
    close_after = db is None
    if db is None:
        db = SessionLocal()

    try:
        # --- Users ---
        if db.query(User).count() == 0:
            users = [
                User(
                    email="cenius@cenius.ai",
                    username="cenius",
                    hashed_password=hash_password(_DEMO_PASSWORD),
                ),
                User(
                    email="admin@example.com",
                    username="admin",
                    hashed_password=hash_password(_ADMIN_PASSWORD),
                ),
            ]
            db.add_all(users)
            db.flush()

        # --- Categories ---
        if db.query(Category).count() == 0:
            categories_data = [
                ("Electronics", "Computers, peripherals, and electronic devices"),
                ("Office Supplies", "Consumables and stationery for daily office use"),
                ("Furniture", "Desks, chairs, shelving, and workspace furniture"),
                ("Raw Materials", "Base materials for manufacturing and assembly"),
            ]
            cat_objs = []
            for name, desc in categories_data:
                cat_objs.append(Category(name=name, description=desc))
            db.add_all(cat_objs)
            db.flush()

        # --- Products ---
        if db.query(Product).count() == 0:
            # Resolve category IDs
            cat_map = {c.name: c.id for c in db.query(Category).all()}

            products_data = [
                # Electronics
                ("ELEC-001", "Laptop Pro 15\"", "High-performance business laptop, 15-inch display", "Electronics", 12, 5, "pcs"),
                ("ELEC-002", "Wireless Mouse", "Ergonomic wireless mouse with USB receiver", "Electronics", 45, 20, "pcs"),
                ("ELEC-003", "USB-C Hub 7-in-1", "Multiport USB-C hub with HDMI, SD card, and USB-A", "Electronics", 3, 10, "pcs"),
                ("ELEC-004", "27\" 4K Monitor", "Ultra-sharp 4K IPS monitor with USB-C connectivity", "Electronics", 8, 5, "pcs"),
                ("ELEC-005", "Mechanical Keyboard", "Tenkeyless mechanical keyboard, Cherry MX Brown", "Electronics", 15, 10, "pcs"),
                ("ELEC-006", "HD Webcam 1080p", "Full HD webcam with autofocus and built-in microphone", "Electronics", 2, 8, "pcs"),
                # Office Supplies
                ("OFF-001", "A4 Copy Paper (ream)", "80gsm white copy paper, 500 sheets per ream", "Office Supplies", 200, 50, "ream"),
                ("OFF-002", "Ballpoint Pens (box)", "Blue ballpoint pens, pack of 50", "Office Supplies", 500, 100, "box"),
                ("OFF-003", "Manila Folders (pack)", "A4 manila folders, pack of 100", "Office Supplies", 80, 30, "pack"),
                ("OFF-004", "Sticky Notes 3x3\"", "Yellow sticky notes, 12 pads per pack", "Office Supplies", 150, 40, "pack"),
                ("OFF-005", "Whiteboard Markers", "Assorted colours, pack of 8", "Office Supplies", 35, 20, "pack"),
                ("OFF-006", "Heavy-Duty Stapler", "Staples up to 100 sheets, includes 1000 staples", "Office Supplies", 25, 15, "pcs"),
                # Furniture
                ("FURN-001", "Ergonomic Office Chair", "Adjustable lumbar support, mesh back, 5-year warranty", "Furniture", 6, 3, "pcs"),
                ("FURN-002", "Sit-Stand Desk 160cm", "Electric height-adjustable desk, walnut top", "Furniture", 4, 5, "pcs"),
                ("FURN-003", "Open Bookshelf 5-Tier", "Industrial-style bookshelf, steel frame + wood shelves", "Furniture", 10, 5, "pcs"),
                ("FURN-004", "Mobile Filing Cabinet", "Lockable 3-drawer filing cabinet on casters", "Furniture", 7, 4, "pcs"),
                ("FURN-005", "Conference Table 8-Seat", "Solid oak conference table, 240cm x 120cm", "Furniture", 2, 3, "pcs"),
                # Raw Materials
                ("RAW-001", "Steel Sheet 2mm", "Cold-rolled steel sheet, 2000mm x 1000mm x 2mm", "Raw Materials", 50, 25, "sheet"),
                ("RAW-002", "Oak Planks 25mm", "Kiln-dried European oak, 2000mm x 150mm x 25mm", "Raw Materials", 30, 20, "plank"),
                ("RAW-003", "ABS Plastic Pellets", "White ABS pellets, 25kg bag", "Raw Materials", 500, 200, "kg"),
                ("RAW-004", "Copper Wire 1.5mm²", "Single-core copper wire, 100m reel", "Raw Materials", 18, 15, "reel"),
            ]

            product_objs = []
            for sku, name, desc, cat_name, stock, reorder, unit in products_data:
                product_objs.append(Product(
                    sku=sku,
                    name=name,
                    description=desc,
                    category_id=cat_map[cat_name],
                    current_stock=stock,
                    reorder_point=reorder,
                    unit=unit,
                ))
            db.add_all(product_objs)
            db.flush()

        # --- Stock Movements (initial stock-in for every product) ---
        if db.query(StockMovement).count() == 0:
            products = db.query(Product).all()
            movements = []
            now = datetime.datetime.utcnow()
            for i, product in enumerate(products):
                # Initial stock-in
                movements.append(StockMovement(
                    product_id=product.id,
                    type=MovementType.IN,
                    quantity=product.current_stock,
                    note="Initial stock intake",
                    created_at=now - datetime.timedelta(days=30 + i),
                ))
                # Some sample OUT movements for a few products
                if product.current_stock > 10 and i % 3 == 0:
                    out_qty = min(product.current_stock // 3, 15)
                    if out_qty > 0:
                        movements.append(StockMovement(
                            product_id=product.id,
                            type=MovementType.OUT,
                            quantity=out_qty,
                            note="Order fulfilment #" + str(1000 + i),
                            created_at=now - datetime.timedelta(days=10 + i),
                        ))
            db.add_all(movements)

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        if close_after:
            db.close()


if __name__ == "__main__":
    # Standalone seed run: create tables then seed
    Base.metadata.create_all(bind=engine)
    seed_data()
    print("Seed complete.")
