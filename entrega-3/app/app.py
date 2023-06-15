#!/usr/bin/python3
import os
from logging.config import dictConfig

import psycopg
from flask import Flask
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from psycopg.rows import namedtuple_row
from psycopg_pool import ConnectionPool
from datetime import date


# postgres://{user}:{password}@{hostname}:{port}/{database-name}
DATABASE_URL = os.environ.get("DATABASE_URL", "postgres://db:db@postgres/db")

pool = ConnectionPool(conninfo=DATABASE_URL)
# the pool starts connecting immediately.

dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s:%(lineno)s - %(funcName)20s(): %(message)s",
            }
        },
        "handlers": {
            "wsgi": {
                "class": "logging.StreamHandler",
                "stream": "ext://flask.logging.wsgi_errors_stream",
                "formatter": "default",
            }
        },
        "root": {"level": "INFO", "handlers": ["wsgi"]},
    }
)

app = Flask(__name__)
log = app.logger


@app.route("/", methods=("GET",))
@app.route("/products", methods=("GET",))
def product_index():
    """Show all the accounts, most recent first."""

    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            products = cur.execute(
                """
                SELECT sku, name, price, ean
                FROM product
                ORDER BY sku DESC;
                """,
                {},
            ).fetchall()
            log.debug(f"Found {cur.rowcount} rows.")

    # API-like response is returned to clients that request JSON explicitly (e.g., fetch)
    if (
        request.accept_mimetypes["application/json"]
        and not request.accept_mimetypes["text/html"]
    ):
        return jsonify(products)

    return render_template("products/index.html", products=products)

@app.route("/products/create", methods=("GET", "POST"))
def product_create():
    """Add a new product"""
    
    product = {
        'name': "",
        'sku': "",
        'ean': None,
        'price': None,
        'description': ""
    }

    if request.method == "GET":
        error = None
        return render_template("products/update.html", product=product, error=error)
    
    elif request.method == "POST":
        sku = request.form["sku"]
        name = request.form["name"]
        price = request.form["price"]
        description = request.form["description"]
        ean = request.form["ean"]

        error = None

        if not sku:
            error = "Sku is required."

        elif not name:
            error = "Name is required."

        elif not price:
            error = "Price is required"
            if not price.isnumeric():
                error = "Price is required to be numeric."
        
        elif ean:
            if not ean.isnumeric():
                error = "EAN is required to be numeric."
            elif not 1000000000000 < int(ean) < 9999999999999:
                error = "EAN is required to have 13 digits."

        if error is not None:
            return render_template('products/update.html', product=product, error=error)
        else:
            with pool.connection() as conn:
                with conn.cursor(row_factory=namedtuple_row) as cur:
                    try:
                        if ean:
                            cur.execute(
                                """
                                INSERT INTO product
                                VALUES (%(sku)s, %(name)s, %(description)s, %(price)s, %(ean)s);
                                """,
                                {"sku": sku, "ean": ean, "name": name, "price": price, "description": description},
                            )
                        else:
                            cur.execute(
                                """
                                INSERT INTO product
                                VALUES (%(sku)s, %(name)s, %(description)s, %(price)s, NULL);
                                """,
                                {"sku": sku, "ean": ean, "name": name, "price": price, "description": description},
                            )
                    except psycopg.errors.IntegrityError:   # Raised when sku already exists on the database
                        conn.rollback()
                        error = "SKU already exists."
                        return render_template('products/update.html', product=product, error=error)
                conn.commit()
            return redirect(url_for("product_index"))

@app.route("/product/<product_sku>/view", methods=("GET", ))
def product_view(product_sku):
    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            product = cur.execute(
                """
                SELECT name, sku, ean, price, description
                FROM product
                WHERE sku = %(product_sku)s;
                """, 
                {"product_sku": product_sku},
            ).fetchone()
            log.debug(f"Found {cur.rowcount} rows.")

    return render_template("products/view.html", product=product, just_view=True)

@app.route("/products/<product_sku>/update", methods=("GET", "POST"))
def product_update(product_sku):
    """Update the product details."""

    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            product = cur.execute(
                """
                SELECT name, sku, ean, price, description
                FROM product
                WHERE sku = %(product_sku)s;
                """,
                {"product_sku": product_sku},
            ).fetchone()

            log.debug(f"Found {cur.rowcount} rows.")

    if request.method == "POST":
        name = request.form["name"]
        price = request.form["price"]
        description = request.form["description"]
        ean = request.form["ean"]

        error = None

        if not name:
            error = "Name is required."

        elif not price:
            error = "Price is required"
            if not price.isnumeric():
                error = "Price is required to be numeric."
        
        elif ean:
            if not ean.isnumeric():
                error = "EAN is required to be numeric."
            elif not 1000000000000 < int(ean) < 9999999999999:
                error = "EAN is required to have 13 digits."

        if error is not None:
            return render_template('products/update.html', product=product, error=error)
        else:
            with pool.connection() as conn:
                with conn.cursor(row_factory=namedtuple_row) as cur:
                    if ean:
                        cur.execute(
                            """
                            UPDATE product
                            SET ean = %(ean)s, name = %(name)s, price = %(price)s, description = %(description)s
                            WHERE sku = %(product_sku)s;
                            """,
                            {"product_sku": product_sku, "ean": ean, "name": name, "price": price, "description": description},
                        )
                    else:
                        cur.execute(
                            """
                            UPDATE product
                            SET ean = NULL, name = %(name)s, price = %(price)s, description = %(description)s
                            WHERE sku = %(product_sku)s;
                            """,
                            {"product_sku": product_sku, "name": name, "price": price, "description": description},
                        )
                conn.commit()
            return redirect(url_for("product_index"))

    return render_template("products/update.html", product=product, error=None)


@app.route("/products/<product_sku>/delete", methods=("POST",))
def product_delete(product_sku):
    """Delete the product."""

    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            
            # Here, the trigger for every order being in contains 
            # only runs after the transaction is made
            cur.execute(
                """
                DELETE FROM contains
                WHERE sku = %(product_sku)s;
                """, {"product_sku": product_sku}) 

            cur.execute(
                """
                DELETE FROM process
                WHERE order_no IN (
                    SELECT order_no FROM orders
                    EXCEPT
                    SELECT order_no FROM contains);
                """)
            
            cur.execute(
                """
                DELETE FROM pay
                WHERE order_no IN (
                    SELECT order_no FROM orders
                    EXCEPT
                    SELECT order_no FROM contains);
                """
            )

            # Take out the sku from the supplier whose product was deleted
            cur.execute(
                """
                UPDATE supplier
                SET sku = NULL
                WHERE sku = %(product_sku)s;
                """, # É preciso fazer mais deletes....
                {"product_sku": product_sku},
            )

            # Finally, after all restrictions have been lifted, delete the product
            cur.execute(
                """
                DELETE FROM product
                WHERE sku = %(product_sku)s;
                """, {"product_sku": product_sku})
            
        conn.commit()
    return redirect(url_for("product_index"))

@app.route("/suppliers", methods=("GET",))
def supplier_index():
    """Show all the accounts, most recent first."""

    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            suppliers = cur.execute(
                """
                SELECT tin, name, address, sku, date
                FROM supplier
                ORDER BY tin DESC;
                """,
                {},
            ).fetchall()
            log.debug(f"Found {cur.rowcount} rows.")

    # API-like response is returned to clients that request JSON explicitly (e.g., fetch)
    if (
        request.accept_mimetypes["application/json"]
        and not request.accept_mimetypes["text/html"]
    ):
        return jsonify(suppliers)

    return render_template("suppliers/index.html", suppliers=suppliers)

@app.route("/suppliers/create", methods=("GET", "POST"))
def supplier_create():
    """Add a new supplier"""
    
    supplier = {
        'tin': "",
        'name': "",
        'address': "",
        'sku': "",
        'date': ""
    }

    if request.method == "GET":
        return render_template("suppliers/update.html", supplier=supplier)
    
    elif request.method == "POST":
        tin = request.form["tin"]
        name = request.form["name"]
        address = request.form["address"]
        sku = request.form["sku"]
        date = request.form["date"]

        error = None

        if not address:
            error = "Address is required."
        else:
            if len(address)>255:
                error = "Address cannot have more than 255 characters."
        if not name:
            error = "Name is required."
        else:
            if len(name)>200:
                error = "Name cannot have more than 200 characters."
        if not date:
            error = "Date is required."

        if error is not None:
            return render_template("suppliers/update.html", supplier=supplier, error=error)
        else:
            with pool.connection() as conn:
                with conn.cursor(row_factory=namedtuple_row) as cur:
                    try:
                        cur.execute(
                            """
                            INSERT INTO supplier
                            VALUES (%(tin)s, %(name)s, %(address)s, %(sku)s, %(date)s);
                            """,
                            {"tin": tin, "name": name, "address": address, "sku": sku, "date": date},
                        )
                    except psycopg.errors.IntegrityError:
                        conn.rollback()
                        error = "TIN already exists."
                        return render_template("suppliers/update.html", supplier=supplier, error=error)
                conn.commit()
            return redirect(url_for("supplier_index"))

@app.route("/suppliers/<tin>/delete", methods=("POST",))
def supplier_delete(tin):
    """Delete the supplier."""

    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            cur.execute(
                """
                DELETE FROM delivery
                WHERE tin = %(tin)s;
                """, 
                {"tin": tin},
            )

            cur.execute(
                """
                DELETE FROM supplier
                WHERE tin = %(tin)s;
                """,
                {"tin": tin},
            )
        conn.commit()
    return redirect(url_for("supplier_index"))

@app.route("/suppliers/<tin>/update", methods=("GET", "POST"))
def supplier_update(tin):
    """Update the account balance."""

    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            supplier = cur.execute(
                """
                SELECT tin, name, address, sku, date
                FROM supplier
                WHERE tin = %(tin)s;
                """,
                {"tin": tin},
            ).fetchone()
            log.debug(f"Found {cur.rowcount} rows.")

    if request.method == "POST":
        address = request.form["address"]
        name = request.form["name"]
        date = request.form["date"]

        error = None

        if not address:
            error = "Address is required."
        else:
            if len(address)>255:
                error = "Address cannot have more than 255 characters."
        if not name:
            error = "Name is required."
        else:
            if len(name)>200:
                error = "Name cannot have more than 200 characters."
        if not date:
            error = "Date is required."

        if error is not None:
            return render_template('suppliers/update.html', supplier=supplier, error=error)
        else:
            with pool.connection() as conn:
                with conn.cursor(row_factory=namedtuple_row) as cur:
                    cur.execute(
                        """
                        UPDATE supplier
                        SET address = %(address)s, name = %(name)s, date = %(date)s
                        WHERE tin = %(tin)s;
                        """,
                        {"tin": tin, "address": address, "name": name, "date": date},
                    )
                conn.commit()
            return redirect(url_for("supplier_index"))

    return render_template("suppliers/update.html", supplier=supplier, error=None)

@app.route("/customers", methods=("GET",))
def customer_index():
    """Show all the accounts, most recent first."""

    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            customers = cur.execute(
                """
                SELECT cust_no, name, email, phone, address
                FROM customer
                ORDER BY cust_no DESC;
                """,
                {},
            ).fetchall()
            log.debug(f"Found {cur.rowcount} rows.")

    # API-like response is returned to clients that request JSON explicitly (e.g., fetch)
    if (
        request.accept_mimetypes["application/json"]
        and not request.accept_mimetypes["text/html"]
    ):
        return jsonify(customers)

    return render_template("customers/index.html", customers=customers)

@app.route("/customers/create", methods=("GET", "POST"))
def customer_create():
    """Add a new customer"""
    
    customer = {
        'cust_no': "",
        'name': "",
        'email': "",
        'phone': "",
        'address': ""
    }

    if request.method == "GET":
        return render_template("customers/update.html", customer=customer, error=None)
    
    elif request.method == "POST":
        cust_no = request.form["cust_no"]
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        address = request.form["address"]

        error = None

        if not address:
            error = "Address is required."
        else:
            if len(address)>255:
                error = "Address cannot have more than 255 characters."
        if not name:
            error = "Name is required."
        else:
            if len(name)>80:
                error = "Name cannot have more than 80 characters."
        if not phone:
            error = "Phone is required."
        else:
            if len(phone)>15:
                error = "Phone cannot have more than 15 characters."
        if not email:
            error = "Email is required."
        else:
            if len(email)>254:
                error = "Email cannot have more than 254 characters."

        if error is not None:
            return render_template("customers/update.html", customer=customer, error=error)
        else:
            with pool.connection() as conn:
                with conn.cursor(row_factory=namedtuple_row) as cur:
                    try:
                        cur.execute(
                            """
                            INSERT INTO customer
                            VALUES (%(cust_no)s, %(name)s, %(email)s, %(phone)s, %(address)s);
                            """,
                            {"cust_no": cust_no, "name": name, "email": email, "phone": phone, "address": address},
                        )
                    except psycopg.errors.IntegrityError:
                        conn.rollback()
                        error = "Customer already exists."
                        return render_template("customers/update.html", customer=customer, error=error)
                conn.commit()
            return redirect(url_for("customer_index"))

@app.route("/customers/<cust_no>/delete", methods=("POST",))
def customer_delete(cust_no):
    """Delete the customer."""

    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            cur.execute(
                """
                DELETE FROM pay
                WHERE cust_no = %(cust_no)s;
                """,
                {"cust_no": cust_no},
            )
            cur.execute(
                """
                DELETE FROM process
                WHERE order_no IN (
                    SELECT order_no FROM orders
                    WHERE cust_no = %(cust_no)s);
                """,
                {"cust_no": cust_no})
            cur.execute(
                """
                DELETE FROM contains
                WHERE order_no IN (
                    SELECT order_no FROM orders
                    WHERE cust_no = %(cust_no)s);
                """,
                {"cust_no": cust_no})
            cur.execute(
                """
                DELETE FROM orders
                WHERE cust_no = %(cust_no)s;
                """,
                {"cust_no": cust_no},
            )
            cur.execute(
                """
                DELETE FROM customer
                WHERE cust_no = %(cust_no)s;
                """,
                {"cust_no": cust_no},
            )
        conn.commit()
    return redirect(url_for("customer_index"))

@app.route("/customers/<cust_no>/update", methods=("GET", "POST"))
def customer_update(cust_no):
    """Update the account balance."""

    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            customer = cur.execute(
                """
                SELECT cust_no, name, email, phone, address
                FROM customer
                WHERE cust_no = %(cust_no)s;
                """,
                {"cust_no": cust_no},
            ).fetchone()
            log.debug(f"Found {cur.rowcount} rows.")

    if request.method == "POST":
        address = request.form["address"]
        phone = request.form["phone"]
        name = request.form["name"]
        email = request.form["email"]

        error = None

        if not name:
            error = "Name is required."
        else:
            if len(name)>80:
                error = "Name cannot have more than 80 characters"
        if not phone:
            error = "Phone is required."
        else:
            if len(phone)>15:
                error = "Phone cannot have more than 15 characters"
        if not email:
            error = "Email is required."
        else:
            if len(email)>254:
                error = "Email cannot have more than 254 characters"
        if not address:
            error = "Address is required."
        else:
            if len(address)>255:
                error = "Address cannot have more than 255 characters"

        if error is not None:
            return render_template("customers/update.html", customer=customer, error=error)
        else:
            with pool.connection() as conn:
                with conn.cursor(row_factory=namedtuple_row) as cur:
                    cur.execute(
                        """
                        UPDATE customer
                        SET address = %(address)s, phone = %(phone)s, email = %(email)s, name = %(name)s 
                        WHERE cust_no = %(cust_no)s;
                        """,
                        {"cust_no": cust_no, "address": address, "phone": phone, "email": email, "name": name},
                    )
                conn.commit()
            return redirect(url_for("customer_index"))

    return render_template("customers/update.html", customer=customer, error=None)

@app.route("/customers/<cust_no>/view", methods=("GET", ))
def customer_view(cust_no):
    """View the account details, as well as the orders issued by the account."""

    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur3:
            customer = cur3.execute(
                """
                SELECT cust_no, name, email, phone, address
                FROM customer
                WHERE cust_no = %(cust_no)s;
                """,
                {"cust_no": cust_no},
            ).fetchone()
            log.debug(f"Found {cur3.rowcount} rows.")
        
        with conn.cursor(row_factory=namedtuple_row) as cur3:
            orders = cur3.execute(
                """
                SELECT order_no, date, SUM(qty) AS num_items, SUM(qty*price) AS total_price,
                    order_no IN (SELECT order_no FROM pay) AS paid
                FROM orders JOIN contains USING (order_no) JOIN product USING (sku)
                WHERE cust_no = %(cust_no)s
                GROUP BY order_no
                ORDER BY date DESC;
                """,
                {"cust_no": cust_no},
            ).fetchall()
            log.debug(f"Found {cur3.rowcount} rows.")

    return render_template("customers/view.html", customer=customer, orders=orders)

@app.route("/customers/<cust_no>/new_order", methods=("GET","POST",))
def customer_new_order(cust_no):
    """Show all the products available to order."""

    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            products = cur.execute(
                """
                SELECT sku, name, price, ean
                FROM product
                ORDER BY sku DESC;
                """,
                {},
            ).fetchall()
            log.debug(f"Found {cur.rowcount} rows.")

    # API-like response is returned to clients that request JSON explicitly (e.g., fetch)
    if (
        request.accept_mimetypes["application/json"]
        and not request.accept_mimetypes["text/html"]
    ):
        return jsonify(products)

    return render_template("products/index.html", products=products, cust_no=cust_no)

@app.route("/customers/<cust_no>/<order_no>/show_products", methods=("GET","POST",))
def show_products(cust_no, order_no):
    """Show all the products available to order."""

    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            products = cur.execute(
                """
                SELECT sku, name, price, ean
                FROM product
                ORDER BY sku DESC;
                """,
                {},
            ).fetchall()
            log.debug(f"Found {cur.rowcount} rows.")

    # API-like response is returned to clients that request JSON explicitly (e.g., fetch)
    if (
        request.accept_mimetypes["application/json"]
        and not request.accept_mimetypes["text/html"]
    ):
        return jsonify(products)

    return render_template("products/index.html", products=products, cust_no=cust_no, order_no=order_no)


@app.route("/orders/<product_sku>/<cust_no>/add_product", methods=("GET", ))
def order_add_product(product_sku, cust_no):
    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            product = cur.execute(
                """
                SELECT name, sku, ean, price, description
                FROM product
                WHERE sku = %(product_sku)s;
                """, 
                {"product_sku": product_sku},
            ).fetchone()
            log.debug(f"Found {cur.rowcount} rows.")

    return render_template("products/view.html", product=product, cust_no=cust_no)

@app.route("/orders/<product_sku>/<cust_no>/<order_no>/add_product", methods=("GET", ))
def order_add_more_product(product_sku, cust_no, order_no):
    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            product = cur.execute(
                """
                SELECT name, sku, ean, price, description
                FROM product
                WHERE sku = %(product_sku)s;
                """, 
                {"product_sku": product_sku},
            ).fetchone()
            log.debug(f"Found {cur.rowcount} rows.")

    return render_template("products/view.html", product=product, cust_no=cust_no, order_no=order_no)

@app.route("/orders/<sku>/<cust_no>/create_order", methods=("GET","POST", ))
def create_order(sku, cust_no):
    qty=1 
    global order_no_count
    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            cur.execute(
                """
                SELECT order_no FROM orders
                ORDER BY order_no DESC;
                """,
            )
            orders = cur.fetchall()
            order_no_count = 0
            if orders:
                order_no_count = orders[0][0]
            cur.execute(
                """
                INSERT INTO orders
                VALUES (%(order_no)s, %(cust_no)s, CURRENT_TIMESTAMP);
                """,
                {"order_no": order_no_count+1, "cust_no": cust_no},
            )
            cur.execute(
                """
                INSERT INTO contains
                VALUES (%(order_no)s, %(sku)s, %(qty)s);
                """,
                {"order_no": order_no_count+1, "sku": sku, "qty": qty},
            )
            products = cur.execute(
                """
                SELECT sku, name, price, ean
                FROM product
                ORDER BY sku ASC;
                """,
                {},
            ).fetchall()
            log.debug(f"Found {cur.rowcount} rows.")
            log.debug(f"Found {cur.rowcount} rows.")
        conn.commit()

    return render_template("products/index.html", products=products, cust_no=cust_no,order_no=order_no_count+1)



@app.route("/orders/<sku>/<cust_no>/<order_no>/add_product_qty", methods=("POST", ))
def add_product_qty(sku, cust_no, order_no):
    qty=int(request.form["qty"])
    # No need to check if qty is <= 0, the html element already takes care of it

    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            product_in_order = cur.execute(
                """
                SELECT COUNT(1) FROM contains
                WHERE order_no = %(order_no)s AND sku = %(sku)s;
                """,
                {"order_no": order_no, "sku": sku}
            ).fetchone()
            if product_in_order[0] == 1:
                cur.execute(
                    """
                    UPDATE contains
                    SET qty = qty + %(qty)s
                    WHERE order_no = %(order_no)s AND sku = %(sku)s;
                    """,
                    {"order_no": order_no, "sku": sku, "qty": qty},
                )
            else:
                cur.execute(
                    """
                    INSERT INTO contains
                    VALUES (%(order_no)s, %(sku)s, %(qty)s);
                    """,
                    {"order_no": order_no, "sku": sku, "qty": qty},
                )
        conn.commit()

    return redirect(url_for("show_products", cust_no=cust_no, order_no=order_no))

@app.route("/orders/<order_no>/view", methods=("GET", ))
def order_view(order_no):
    """View the details and the items of an order"""

    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            order = cur.execute(
                """
                SELECT order_no, cust_no, name AS cust_name, date, order_no IN (SELECT order_no FROM pay) AS paid
                FROM orders JOIN customer USING (cust_no)
                WHERE order_no = %(order_no)s;
                """, {"order_no": order_no},
            ).fetchone()
            log.debug(f"Found {cur.rowcount} rows.")

        with conn.cursor(row_factory=namedtuple_row) as cur2:
            items = cur2.execute(
                """
                SELECT sku, name, price, qty, price * qty AS qty_price
                FROM product JOIN contains USING (sku)
                WHERE order_no = %(order_no)s;
                """, {"order_no": order_no},
            ).fetchall()
            log.debug(f"Found {cur2.rowcount} rows.")
        
        log.debug(f"Items: {items[0][4]}")
        total = 0
        for i in range(len(items)):
            total += items[i][4]

    return render_template("orders/view.html", order=order, items=items, total=total)

@app.route("/orders/<order_no>/delete-item/<product_sku>/", methods=("POST", ))
def order_delete_item(order_no, product_sku):
    """Remove a product from an order"""

    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            cur.execute(
                """
                DELETE FROM contains
                WHERE order_no = %(order_no)s AND sku = %(product_sku)s;
                """, {"order_no": order_no, "product_sku": product_sku}
            )

            order_has_products = cur.execute(
                """
                SELECT COUNT(1) FROM contains
                WHERE order_no = %(order_no)s;
                """, {"order_no": order_no}
            ).fetchone()
            if(order_has_products[0] == 0):
                cur.execute(
                    """
                    DELETE FROM process 
                    WHERE order_no = %(order_no)s;
                    """, {"order_no": order_no}
                )
                cur.execute(
                    """
                    DELETE FROM pay
                    WHERE order_no = %(order_no)s;
                    """, {"order_no": order_no}
                )
                cur.execute(
                    """
                    DELETE FROM orders
                    WHERE order_no = %(order_no)s;
                    """, {"order_no": order_no}
                )
        conn.commit()
        if order_has_products[0] == 0:
            return redirect(url_for("customer_index"))

    return redirect(url_for("order_view", order_no=order_no))
    


@app.route("/ping", methods=("GET",))
def ping():
    log.debug("ping!")
    return jsonify({"message": "pong!", "status": "success"})


if __name__ == "__main__":
    app.run()
