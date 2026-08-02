from flask import Flask, render_template, request, redirect, send_file
import mysql.connector
from reportlab.pdfgen import canvas
import os

app = Flask(__name__)

# ==========================
# DATABASE CONNECTION
# ==========================

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Jatin#6099",      # Apna password yahan rakho
    database="inventory_db"
)

cursor = conn.cursor()

# ==========================
# HOME
# ==========================

@app.route("/")
def home():
    return render_template("login.html")


# ==========================
# LOGIN
# ==========================

@app.route("/login", methods=["POST"])
def login():

    username = request.form["username"]
    password = request.form["password"]

    if username == "_jatinkhokhar_" and password == "Jatin#6099":
        return redirect("/dashboard")

    return """
    <center style="margin-top:100px;">
        <h2 style="color:red;">Invalid Username or Password</h2>
        <br>
        <a href="/">Back to Login</a>
    </center>
    """


# ==========================
# DASHBOARD
# ==========================

@app.route("/dashboard")
def dashboard():

    # Total Products
    cursor.execute("SELECT COUNT(*) FROM products")
    total_products = cursor.fetchone()[0]

    # Inventory Value
    cursor.execute("""
        SELECT IFNULL(SUM(price * quantity),0)
        FROM products
    """)
    total_value = cursor.fetchone()[0]

    # Low Stock
    cursor.execute("""
        SELECT COUNT(*)
        FROM products
        WHERE quantity < 5
    """)
    low_stock = cursor.fetchone()[0]

    return render_template(
        "dashboard.html",
        total_products=total_products,
        total_value=total_value,
        low_stock=low_stock
    )
# ======================================================
# PRODUCT MODULE
# ======================================================

# Add Product

@app.route("/add_product", methods=["GET", "POST"])
def add_product():

    if request.method == "POST":

        name = request.form["name"]
        category = request.form["category"]
        quantity = request.form["quantity"]
        price = request.form["price"]

        cursor.execute("""
            INSERT INTO products
            (name, category, quantity, price)
            VALUES(%s,%s,%s,%s)
        """, (
            name,
            category,
            quantity,
            price
        ))

        conn.commit()

        return redirect("/view_products")

    cursor.execute("""
        SELECT category_name
        FROM categories
        ORDER BY category_name
    """)

    categories = cursor.fetchall()

    return render_template(
        "add_product.html",
        categories=categories
    )


# ======================================================
# VIEW PRODUCTS
# ======================================================

@app.route("/view_products")
def view_products():

    cursor.execute("""
        SELECT *
        FROM products
        ORDER BY id DESC
    """)

    products = cursor.fetchall()

    return render_template(
        "view_products.html",
        products=products
    )


# ======================================================
# SEARCH PRODUCT
# ======================================================

@app.route("/search", methods=["POST"])
def search():

    keyword = request.form["keyword"]

    cursor.execute("""
        SELECT *
        FROM products
        WHERE
        name LIKE %s
        OR category LIKE %s
        ORDER BY id DESC
    """, (
        "%" + keyword + "%",
        "%" + keyword + "%"
    ))

    products = cursor.fetchall()

    return render_template(
        "view_products.html",
        products=products
    )


# ======================================================
# EDIT PRODUCT
# ======================================================

@app.route("/edit_product/<int:id>", methods=["GET", "POST"])
def edit_product(id):

    if request.method == "POST":

        name = request.form["name"]
        category = request.form["category"]
        quantity = request.form["quantity"]
        price = request.form["price"]

        cursor.execute("""
            UPDATE products
            SET
                name=%s,
                category=%s,
                quantity=%s,
                price=%s
            WHERE id=%s
        """, (
            name,
            category,
            quantity,
            price,
            id
        ))

        conn.commit()

        return redirect("/view_products")

    cursor.execute(
        "SELECT * FROM products WHERE id=%s",
        (id,)
    )

    product = cursor.fetchone()

    cursor.execute("""
        SELECT category_name
        FROM categories
        ORDER BY category_name
    """)

    categories = cursor.fetchall()

    return render_template(
        "edit_product.html",
        product=product,
        categories=categories
    )


# ======================================================
# DELETE PRODUCT
# ======================================================

@app.route("/delete_product/<int:id>")
def delete_product(id):

    cursor.execute(
        "DELETE FROM products WHERE id=%s",
        (id,)
    )

    conn.commit()

    return redirect("/view_products")
# ======================================================
# CATEGORY MODULE
# ======================================================

@app.route("/categories")
def categories():

    cursor.execute("""
        SELECT *
        FROM categories
        ORDER BY id DESC
    """)

    categories = cursor.fetchall()

    return render_template(
        "categories.html",
        categories=categories
    )


# ======================================================
# ADD CATEGORY
# ======================================================

@app.route("/add_category", methods=["POST"])
def add_category():

    category_name = request.form["category_name"]

    cursor.execute("""
        INSERT INTO categories(category_name)
        VALUES(%s)
    """, (category_name,))

    conn.commit()

    return redirect("/categories")


# ======================================================
# DELETE CATEGORY
# ======================================================

@app.route("/delete_category/<int:id>")
def delete_category(id):

    cursor.execute(
        "DELETE FROM categories WHERE id=%s",
        (id,)
    )

    conn.commit()

    return redirect("/categories")


# ======================================================
# SUPPLIER MODULE
# ======================================================

@app.route("/suppliers")
def suppliers():

    cursor.execute("""
        SELECT *
        FROM suppliers
        ORDER BY id DESC
    """)

    suppliers = cursor.fetchall()

    return render_template(
        "supplier.html",
        suppliers=suppliers
    )


# ======================================================
# ADD SUPPLIER
# ======================================================

@app.route("/add_supplier", methods=["POST"])
def add_supplier():

    supplier_name = request.form["supplier_name"]
    company = request.form["company"]
    mobile = request.form["mobile"]
    email = request.form["email"]
    address = request.form["address"]

    cursor.execute("""
        INSERT INTO suppliers
        (supplier_name, company, mobile, email, address)
        VALUES(%s,%s,%s,%s,%s)
    """, (
        supplier_name,
        company,
        mobile,
        email,
        address
    ))

    conn.commit()

    return redirect("/suppliers")


# ======================================================
# DELETE SUPPLIER
# ======================================================

@app.route("/delete_supplier/<int:id>")
def delete_supplier(id):

    cursor.execute(
        "DELETE FROM suppliers WHERE id=%s",
        (id,)
    )

    conn.commit()

    return redirect("/suppliers")
# ======================================================
# PURCHASE MODULE
# ======================================================

@app.route("/purchases")
def purchases():

    # Product List
    cursor.execute("""
        SELECT id, name
        FROM products
        ORDER BY name
    """)
    products = cursor.fetchall()

    # Supplier List
    cursor.execute("""
        SELECT id, supplier_name
        FROM suppliers
        ORDER BY supplier_name
    """)
    suppliers = cursor.fetchall()

    # Purchase History
    cursor.execute("""
        SELECT
            purchases.id,
            products.name,
            suppliers.supplier_name,
            purchases.quantity,
            purchases.purchase_price,
            purchases.purchase_date
        FROM purchases
        INNER JOIN products
            ON purchases.product_id = products.id
        INNER JOIN suppliers
            ON purchases.supplier_id = suppliers.id
        ORDER BY purchases.id DESC
    """)

    purchase_list = cursor.fetchall()

    return render_template(
        "purchase.html",
        products=products,
        suppliers=suppliers,
        purchases=purchase_list
    )


# ======================================================
# ADD PURCHASE
# ======================================================

@app.route("/add_purchase", methods=["POST"])
def add_purchase():

    product_id = request.form["product_id"]
    supplier_id = request.form["supplier_id"]
    quantity = int(request.form["quantity"])
    purchase_price = request.form["purchase_price"]

    # Purchase Entry

    cursor.execute("""
        INSERT INTO purchases
        (
            product_id,
            supplier_id,
            quantity,
            purchase_price
        )
        VALUES(%s,%s,%s,%s)
    """, (
        product_id,
        supplier_id,
        quantity,
        purchase_price
    ))

    # Update Product Stock

    cursor.execute("""
        UPDATE products
        SET quantity = quantity + %s
        WHERE id = %s
    """, (
        quantity,
        product_id
    ))

    conn.commit()

    return redirect("/purchases")
# ======================================================
# SALES MODULE
# ======================================================

@app.route("/sales")
def sales():

    # Product List
    cursor.execute("""
        SELECT id, name
        FROM products
        ORDER BY name
    """)
    products = cursor.fetchall()

    # Sales History
    cursor.execute("""
        SELECT
            sales.id,
            products.name,
            sales.customer_name,
            sales.quantity,
            sales.selling_price,
            sales.sale_date
        FROM sales
        INNER JOIN products
            ON sales.product_id = products.id
        ORDER BY sales.id DESC
    """)

    sales_list = cursor.fetchall()

    return render_template(
        "sales.html",
        products=products,
        sales=sales_list
    )


# ======================================================
# ADD SALE
# ======================================================

@app.route("/add_sale", methods=["POST"])
def add_sale():

    product_id = request.form["product_id"]
    customer_name = request.form["customer_name"]
    quantity = int(request.form["quantity"])
    selling_price = float(request.form["selling_price"])

    # Current Stock Check
    cursor.execute(
        "SELECT quantity FROM products WHERE id=%s",
        (product_id,)
    )

    stock = cursor.fetchone()

    if stock is None:
        return "<h3>Product not found.</h3>"

    available_stock = stock[0]

    if quantity > available_stock:
        return f"""
        <center style='margin-top:80px;font-family:Arial'>
            <h2 style='color:red;'>Insufficient Stock!</h2>
            <p>Available Stock : <b>{available_stock}</b></p>
            <br>
            <a href='/sales'>⬅ Back</a>
        </center>
        """

    # Save Sale
    cursor.execute("""
        INSERT INTO sales
        (
            product_id,
            customer_name,
            quantity,
            selling_price
        )
        VALUES(%s,%s,%s,%s)
    """, (
        product_id,
        customer_name,
        quantity,
        selling_price
    ))

    sale_id = cursor.lastrowid

    # Reduce Stock
    cursor.execute("""
        UPDATE products
        SET quantity = quantity - %s
        WHERE id=%s
    """, (
        quantity,
        product_id
    ))

    conn.commit()

    return redirect("/invoice/" + str(sale_id))
# ======================================================
# REPORTS MODULE
# ======================================================

@app.route("/reports")
def reports():

    # Total Products
    cursor.execute("SELECT COUNT(*) FROM products")
    total_products = cursor.fetchone()[0]

    # Total Purchases
    cursor.execute("SELECT COUNT(*) FROM purchases")
    total_purchases = cursor.fetchone()[0]

    # Total Sales
    cursor.execute("SELECT COUNT(*) FROM sales")
    total_sales = cursor.fetchone()[0]

    # Inventory Value
    cursor.execute("""
        SELECT IFNULL(SUM(price * quantity), 0)
        FROM products
    """)
    inventory_value = cursor.fetchone()[0]

    # Recent Purchases
    cursor.execute("""
        SELECT
            purchases.id,
            products.name,
            purchases.quantity,
            purchases.purchase_price
        FROM purchases
        INNER JOIN products
            ON purchases.product_id = products.id
        ORDER BY purchases.id DESC
        LIMIT 10
    """)

    purchases = cursor.fetchall()

    # Recent Sales
    cursor.execute("""
        SELECT
            sales.id,
            products.name,
            sales.quantity,
            sales.selling_price
        FROM sales
        INNER JOIN products
            ON sales.product_id = products.id
        ORDER BY sales.id DESC
        LIMIT 10
    """)

    sales = cursor.fetchall()

    return render_template(
        "reports.html",
        total_products=total_products,
        total_purchases=total_purchases,
        total_sales=total_sales,
        inventory_value=inventory_value,
        purchases=purchases,
        sales=sales
    )


# ======================================================
# PDF INVOICE
# ======================================================

@app.route("/invoice/<int:sale_id>")
def invoice(sale_id):

    cursor.execute("""
        SELECT
            sales.id,
            products.name,
            sales.customer_name,
            sales.quantity,
            sales.selling_price,
            sales.sale_date
        FROM sales
        INNER JOIN products
            ON sales.product_id = products.id
        WHERE sales.id=%s
    """, (sale_id,))

    sale = cursor.fetchone()

    if sale is None:
        return "Invoice Not Found"

    if not os.path.exists("invoices"):
        os.makedirs("invoices")

    pdf_path = f"invoices/invoice_{sale_id}.pdf"

    c = canvas.Canvas(pdf_path)

    c.setFont("Helvetica-Bold", 18)
    c.drawString(180, 800, "Inventory Invoice")

    c.setFont("Helvetica", 12)

    c.drawString(50, 750, f"Invoice ID : {sale[0]}")
    c.drawString(50, 725, f"Customer : {sale[2]}")
    c.drawString(50, 700, f"Product : {sale[1]}")
    c.drawString(50, 675, f"Quantity : {sale[3]}")
    c.drawString(50, 650, f"Price : Rs. {sale[4]}")

    total = sale[3] * float(sale[4])

    c.drawString(50, 625, f"Total : Rs. {total:.2f}")

    c.drawString(50, 600, f"Date : {sale[5]}")

    c.line(50, 580, 550, 580)

    c.drawString(50, 550, "Thank you for your business!")

    c.save()

    return send_file(
        pdf_path,
        as_attachment=True
    )


# ======================================================
# LOGOUT
# ======================================================

@app.route("/logout")
def logout():
    return redirect("/")


# ======================================================
# RUN APPLICATION
# ======================================================

if __name__ == "__main__":
    app.run(
        debug=True
    )