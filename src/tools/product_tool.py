import csv
from pathlib import Path

from src.database.database import (
    get_connection,
    initialize_database,
)


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PRODUCTS_FILE = PROJECT_ROOT / "data" / "products.csv"


# ============================================================
# LOAD PRODUCTS INTO DATABASE
# ============================================================

def load_products_from_csv():
    """
    Load products from products.csv into the SQLite database.
    Existing products are updated if the product_id already exists.
    """

    initialize_database()

    connection = get_connection()

    try:

        with open(
            PRODUCTS_FILE,
            "r",
            encoding="utf-8",
            newline=""
        ) as file:

            reader = csv.DictReader(file)

            products = list(reader)

        for product in products:

            connection.execute(
                """
                INSERT INTO products (
                    product_id,
                    product_name,
                    category,
                    description,
                    price_kes,
                    stock_quantity,
                    delivery_days
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)

                ON CONFLICT(product_id)
                DO UPDATE SET
                    product_name = excluded.product_name,
                    category = excluded.category,
                    description = excluded.description,
                    price_kes = excluded.price_kes,
                    stock_quantity = excluded.stock_quantity,
                    delivery_days = excluded.delivery_days
                """,
                (
                    product["product_id"],
                    product["product_name"],
                    product["category"],
                    product["description"],
                    float(product["price_kes"]),
                    int(product["stock_quantity"]),
                    int(product["delivery_days"]),
                ),
            )

        connection.commit()

        print(f"Loaded {len(products)} products.")

    finally:
        connection.close()


# ============================================================
# GET PRODUCT
# ============================================================

def get_product(product_id: str):
    """
    Retrieve one product using its product ID.
    """

    connection = get_connection()

    try:

        cursor = connection.execute(
            """
            SELECT
                product_id,
                product_name,
                category,
                description,
                price_kes,
                stock_quantity,
                delivery_days
            FROM products
            WHERE product_id = ?
            """,
            (product_id,),
        )

        product = cursor.fetchone()

        if product is None:
            return None

        return dict(product)

    finally:
        connection.close()


# ============================================================
# SEARCH PRODUCTS
# ============================================================

def search_products(search_term: str):
    """
    Search products by name, category, or description.
    """

    connection = get_connection()

    try:

        search_pattern = f"%{search_term}%"

        cursor = connection.execute(
            """
            SELECT
                product_id,
                product_name,
                category,
                description,
                price_kes,
                stock_quantity,
                delivery_days
            FROM products
            WHERE
                product_name LIKE ?
                OR category LIKE ?
                OR description LIKE ?
            ORDER BY product_name
            """,
            (
                search_pattern,
                search_pattern,
                search_pattern,
            ),
        )

        products = cursor.fetchall()

        return [dict(product) for product in products]

    finally:
        connection.close()


# ============================================================
# CHECK STOCK
# ============================================================

def check_stock(product_id: str, quantity: int):
    """
    Check whether the requested quantity is available.
    """

    product = get_product(product_id)

    if product is None:

        return {
            "available": False,
            "message": f"Product {product_id} was not found.",
        }

    available_quantity = product["stock_quantity"]

    if available_quantity >= quantity:

        return {
            "available": True,
            "product_id": product_id,
            "product_name": product["product_name"],
            "requested_quantity": quantity,
            "available_quantity": available_quantity,
            "message": (
                f"{quantity} units of "
                f"{product['product_name']} are available."
            ),
        }

    return {
        "available": False,
        "product_id": product_id,
        "product_name": product["product_name"],
        "requested_quantity": quantity,
        "available_quantity": available_quantity,
        "message": (
            f"Only {available_quantity} units of "
            f"{product['product_name']} are currently available."
        ),
    }


# ============================================================
# GET PRODUCTS BY CATEGORY
# ============================================================

def get_products_by_category(category: str):
    """
    Return all products belonging to a category.
    """

    connection = get_connection()

    try:

        cursor = connection.execute(
            """
            SELECT
                product_id,
                product_name,
                category,
                description,
                price_kes,
                stock_quantity,
                delivery_days
            FROM products
            WHERE category LIKE ?
            ORDER BY product_name
            """,
            (f"%{category}%",),
        )

        products = cursor.fetchall()

        return [dict(product) for product in products]

    finally:
        connection.close()


# ============================================================
# TEST PRODUCT TOOL
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("KENYABIZ AI")
    print("PRODUCT DATABASE TOOL TEST")
    print("=" * 60)

    print("\n1. Loading products...")
    load_products_from_csv()

    print("\n2. Get product P001:")

    product = get_product("P001")

    print(product)

    print("\n3. Search for 'chair':")

    products = search_products("chair")

    for product in products:
        print(product)

    print("\n4. Check stock for 5 units of P001:")

    stock = check_stock("P001", 5)

    print(stock)

    print("\n5. Products in Furniture category:")

    furniture = get_products_by_category("Furniture")

    for product in furniture:
        print(
            f"{product['product_id']} | "
            f"{product['product_name']} | "
            f"KES {product['price_kes']:,.2f}"
        )

    print("\n" + "=" * 60)
    print("PRODUCT TOOL TEST COMPLETED")
    print("=" * 60)