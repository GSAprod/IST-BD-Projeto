#!/usr/bin/python3
import os
from logging.config import dictConfig

import psycopg
from flask import flash
from flask import Flask
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from psycopg.rows import namedtuple_row
from psycopg_pool import ConnectionPool


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
                ORDER BY sku ASC;
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
    

    if request.method == "GET":
        product = {
            'name': "",
            'sku': "",
            'ean': None,
            'price': None,
            'description': ""
        }
        return render_template("products/update.html", product=product)
    
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
            flash(error)
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
                        flash(error)
                conn.commit()
            return redirect(url_for("product_index"))
    

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
            flash(error)
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

    return render_template("products/update.html", product=product)


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
    

    if request.method == "GET":
        supplier = {
            'tin': "",
            'name': "",
            'address': "",
            'sku': "",
            'date': ""
        }
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
            flash(error)
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
                        flash(error)
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
            flash(error)
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

    return render_template("suppliers/update.html", supplier=supplier)

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
    

    if request.method == "GET":
        customer = {
            'cust_no': "",
            'name': "",
            'email': "",
            'phone': "",
            'address': ""
        }
        return render_template("customers/update.html", customer=customer)
    
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
            flash(error)
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
                        flash(error)
                conn.commit()
            return redirect(url_for("customer_index"))

@app.route("/customers/<cust_no>/delete", methods=("POST",))
def customer_delete(cust_no):
    """Delete the customer."""

    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
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
            flash(error)
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

    return render_template("customers/update.html", customer=customer)

@app.route("/customers/<cust_no>/view", methods=("GET", ))
def customer_view(cust_no):
    """Update the account balance."""

    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur2:
            customer = cur2.execute(
                """
                SELECT cust_no, name, email, phone, address
                FROM customer
                WHERE cust_no = %(cust_no)s;
                """,
                {"cust_no": cust_no},
            ).fetchone()
            log.debug(f"Found {cur2.rowcount} rows.")
        
        with conn.cursor(row_factory=namedtuple_row) as cur2:
            orders = cur2.execute(
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
            log.debug(f"Found {cur2.rowcount} rows.")

        

    return render_template("customers/view.html", customer=customer, orders=orders)

@app.route("/ping", methods=("GET",))
def ping():
    log.debug("ping!")
    return jsonify({"message": "pong!", "status": "success"})


if __name__ == "__main__":
    app.run()
