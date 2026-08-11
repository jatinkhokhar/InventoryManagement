from flask import Flask, render_template, request, redirect, send_file
import mysql.connector
from reportlab.pdfgen import canvas
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.units import mm
COMPANY_GSTIN = "24XXXXXXXXXXXXXX"
app = Flask(__name__)
app.secret_key = "inventory-management-secret-key"

# =====================================================
# DATABASE CONNECTION
# =====================================================

conn = None
cursor = None


def connect_db():
    global conn, cursor

    try:
        if conn is not None and conn.is_connected():
            return
    except:
        pass

    conn = mysql.connector.connect(
        host="gateway01.ap-southeast-1.prod.aws.tidbcloud.com",
        port=4000,
        user="2oYHttVxiPJa1jB.root",
        password="rE0fXO2tsl5Qp1pM",
        database="inventory_db",
        ssl_ca="ca.pem",   # apni CA file ka exact naam
        autocommit=True,
        connection_timeout=30
    )

    cursor = conn.cursor()


def get_cursor():
    global conn, cursor

    try:
        if conn is None or not conn.is_connected():
            connect_db()
        else:
            conn.ping(reconnect=True, attempts=3, delay=2)
    except:
        connect_db()

    return cursor


connect_db()

# =====================================================
# HOME
# =====================================================

@app.route("/")
def home():
    return render_template("login.html")


# =====================================================
# LOGIN
# =====================================================

@app.route("/login", methods=["POST"])
def login():

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    cursor = get_cursor()

    cursor.execute("""
        SELECT id, full_name, username, password, role
        FROM users
        WHERE username = %s
          AND password = %s
    """, (username, password))

    user = cursor.fetchone()

    if user:
        return redirect("/dashboard")

    return """
    <center style="margin-top:120px;font-family:Arial">
        <h2 style="color:red">Invalid Username or Password</h2>
        <a href="/">Back to Login</a>
    </center>
    """# DASHBOARD
# =====================================================

@app.route("/dashboard")
def dashboard():

    cursor = get_cursor()

    cursor.execute("SELECT COUNT(*) FROM products")
    total_products = cursor.fetchone()[0]

    cursor.execute("""
        SELECT IFNULL(SUM(price * quantity),0)
        FROM products
    """)
    inventory_value = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM products
        WHERE quantity < 5
    """)
    low_stock = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM suppliers")
    total_suppliers = cursor.fetchone()[0]

    return render_template(
        "dashboard.html",
        total_products=total_products,
        inventory_value=inventory_value,
        low_stock=low_stock,
        total_suppliers=total_suppliers
    )
# =====================================================
# CATEGORY MODULE
# =====================================================

@app.route("/categories")
def categories():

    cursor = get_cursor()

    cursor.execute("""
        SELECT *
        FROM categories
        ORDER BY category_name
    """)

    categories = cursor.fetchall()

    return render_template(
        "categories.html",
        categories=categories
    )


# =====================================================
# ADD CATEGORY
# =====================================================

@app.route("/add_category", methods=["POST"])
def add_category():

    cursor = get_cursor()

    category_name = request.form["category_name"]

    cursor.execute("""
        INSERT INTO categories(category_name)
        VALUES(%s)
    """, (category_name,))

    conn.commit()

    return redirect("/categories")


# =====================================================
# DELETE CATEGORY
# =====================================================

@app.route("/delete_category/<int:id>")
def delete_category(id):

    cursor = get_cursor()

    cursor.execute(
        "DELETE FROM categories WHERE id=%s",
        (id,)
    )

    conn.commit()

    return redirect("/categories")


# =====================================================
# VIEW PRODUCTS
# =====================================================

@app.route("/view_products")
def view_products():

    cursor = get_cursor()

    cursor.execute("""
        SELECT
            p.id,
            p.name,
            c.category_name,
            p.quantity,
            p.price,
            p.created_at
        FROM products p
        LEFT JOIN categories c
            ON p.category_id = c.id
        ORDER BY p.id DESC
    """)

    products = cursor.fetchall()

    return render_template(
        "view_products.html",
        products=products
    )


# =====================================================
# ADD PRODUCT
# =====================================================

@app.route("/add_product", methods=["GET", "POST"])
def add_product():

    cursor = get_cursor()

    if request.method == "POST":

        name = request.form["name"]
        category_id = request.form["category_id"]
        quantity = request.form["quantity"]
        price = request.form["price"]

        cursor.execute("""
            INSERT INTO products
            (
                name,
                category_id,
                quantity,
                price
            )
            VALUES(%s,%s,%s,%s)
        """, (
            name,
            category_id,
            quantity,
            price
        ))

        conn.commit()

        return redirect("/view_products")

    cursor.execute("""
        SELECT
            id,
            category_name
        FROM categories
        ORDER BY category_name
    """)

    categories = cursor.fetchall()

    return render_template(
        "add_product.html",
        categories=categories
    )# =====================================================
# SEARCH PRODUCT
# =====================================================

@app.route("/search", methods=["POST"])
def search():

    cursor = get_cursor()

    keyword = request.form["keyword"]

    cursor.execute("""
        SELECT
            p.id,
            p.name,
            c.category_name,
            p.quantity,
            p.price,
            p.created_at
        FROM products p
        LEFT JOIN categories c
            ON p.category_id = c.id
        WHERE
            p.name LIKE %s
            OR c.category_name LIKE %s
        ORDER BY p.id DESC
    """, (
        "%" + keyword + "%",
        "%" + keyword + "%"
    ))

    products = cursor.fetchall()

    return render_template(
        "view_products.html",
        products=products
    )


# =====================================================
# EDIT PRODUCT
# =====================================================

@app.route("/edit_product/<int:id>", methods=["GET", "POST"])
def edit_product(id):

    cursor = get_cursor()

    if request.method == "POST":

        name = request.form["name"]
        category_id = request.form["category_id"]
        quantity = request.form["quantity"]
        price = request.form["price"]

        cursor.execute("""
            UPDATE products
            SET
                name=%s,
                category_id=%s,
                quantity=%s,
                price=%s
            WHERE id=%s
        """, (
            name,
            category_id,
            quantity,
            price,
            id
        ))

        conn.commit()

        return redirect("/view_products")

    cursor.execute("""
        SELECT
            id,
            name,
            category_id,
            quantity,
            price
        FROM products
        WHERE id=%s
    """, (id,))

    product = cursor.fetchone()

    cursor.execute("""
        SELECT
            id,
            category_name
        FROM categories
        ORDER BY category_name
    """)

    categories = cursor.fetchall()

    return render_template(
        "edit_product.html",
        product=product,
        categories=categories
    )


# =====================================================
# DELETE PRODUCT
# =====================================================

@app.route("/delete_product/<int:id>")
def delete_product(id):

    cursor = get_cursor()

    cursor.execute(
        "DELETE FROM products WHERE id=%s",
        (id,)
    )

    conn.commit()

    return redirect("/view_products")
    # =====================================================
# SUPPLIER MODULE
# =====================================================

@app.route("/suppliers")
def suppliers():

    cursor = get_cursor()

    cursor.execute("""
        SELECT
            id,
            supplier_name,
            phone,
            email,
            address
        FROM suppliers
        ORDER BY id DESC
    """)

    suppliers = cursor.fetchall()

    return render_template(
        "supplier.html",
        suppliers=suppliers
    )


# =====================================================
# ADD SUPPLIER
# =====================================================

@app.route("/add_supplier", methods=["POST"])
def add_supplier():

    cursor = get_cursor()

    supplier_name = request.form["supplier_name"]
    phone = request.form["phone"]
    email = request.form["email"]
    address = request.form["address"]

    cursor.execute("""
        INSERT INTO suppliers
        (
            supplier_name,
            phone,
            email,
            address
        )
        VALUES(%s,%s,%s,%s)
    """, (
        supplier_name,
        phone,
        email,
        address
    ))

    conn.commit()

    return redirect("/suppliers")


# =====================================================
# DELETE SUPPLIER
# =====================================================

@app.route("/delete_supplier/<int:id>")
def delete_supplier(id):

    cursor = get_cursor()

    cursor.execute(
        "DELETE FROM suppliers WHERE id=%s",
        (id,)
    )

    conn.commit()

    return redirect("/suppliers")
# =====================================================
# PURCHASE MODULE
# =====================================================

@app.route("/purchases")
def purchases():

    cursor = get_cursor()

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
            pu.id,
            pr.name,
            s.supplier_name,
            pu.quantity,
            pu.purchase_price,
            pu.purchase_date
        FROM purchases pu
        INNER JOIN products pr
            ON pu.product_id = pr.id
        INNER JOIN suppliers s
            ON pu.supplier_id = s.id
        ORDER BY pu.id DESC
    """)

    purchase_list = cursor.fetchall()

    return render_template(
        "purchase.html",
        products=products,
        suppliers=suppliers,
        purchases=purchase_list
    )


# =====================================================
# ADD PURCHASE
# =====================================================

@app.route("/add_purchase", methods=["POST"])
def add_purchase():

    cursor = get_cursor()

    product_id = request.form["product_id"]
    supplier_id = request.form["supplier_id"]
    quantity = int(request.form["quantity"])
    purchase_price = float(request.form["purchase_price"])

    # Save Purchase
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
    cursor.execute("""
        UPDATE products
        SET quantity = quantity + %s
        WHERE id=%s
        """, (
        quantity,
        product_id
))
    # Update Stock
    cursor.execute("""
        UPDATE products
        SET quantity = quantity + %s
        WHERE id=%s
    """, (
        quantity,
        product_id
    ))

    conn.commit()

    return redirect("/purchases")
# =====================================================
# SALES MODULE
# =====================================================

@app.route("/sales")
def sales():

    cursor = get_cursor()

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
            s.id,
            p.name,
            s.customer_name,
            s.quantity,
            s.selling_price,
            s.sale_date
        FROM sales s
        INNER JOIN products p
            ON s.product_id = p.id
        ORDER BY s.id DESC
    """)

    sales_list = cursor.fetchall()

    return render_template(
        "sales.html",
        products=products,
        sales=sales_list
    )


# =====================================================
# ADD SALE
# =====================================================

@app.route("/add_sale", methods=["POST"])
def add_sale():

    cursor = get_cursor()

    product_id = request.form["product_id"]
    customer_name = request.form["customer_name"]
    customer_gstin = request.form.get("customer_gstin", "").strip().upper()
    quantity = int(request.form["quantity"])
    selling_price = float(request.form["selling_price"])
    gst_rate = float(request.form["gst_rate"])

    # Check Stock
    cursor.execute(
        "SELECT quantity FROM products WHERE id=%s",
        (product_id,)
    )

    stock = cursor.fetchone()

    if stock is None:
        return "<h2>Product Not Found</h2>"

    available_stock = stock[0]

    if quantity > available_stock:
        return f"""
        <center style='margin-top:100px;font-family:Arial'>
            <h2 style='color:red;'>Insufficient Stock</h2>
            <h3>Available Stock : {available_stock}</h3>
            <br>
            <a href='/sales'>Back</a>
        </center>
        """

    # Save Sale
    cursor.execute("""
        INSERT INTO sales
        (
            product_id,
            customer_name,
            customer_gstin,
            quantity,
            selling_price,
            gst_rate
        )
        VALUES(%s,%s,%s,%s,%s,%s)
    """, (
        product_id,
        customer_name,
        customer_gstin,
        quantity,
        selling_price,
        gst_rate
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

    return redirect("/sales")
    # =====================================================
    # PDF INVOICE
    # =====================================================
@app.route("/invoice/<int:sale_id>")
def invoice(sale_id):

    cursor = get_cursor()

    cursor.execute("""
        SELECT
            s.id,
            p.name,
            s.customer_name,
            s.customer_gstin,
            s.quantity,
            s.selling_price,
            s.sale_date,
            s.gst_rate
        FROM sales s
        INNER JOIN products p
            ON s.product_id = p.id
        WHERE s.id=%s
    """, (sale_id,))

    sale = cursor.fetchone()

    if sale is None:
        return "<h2>Invoice Not Found</h2>"

    # GST Calculation
    gst_rate = float(sale[7])

    subtotal = sale[4] * float(sale[5])

    gst_amount = subtotal * gst_rate / 100

    cgst = gst_amount / 2
    sgst = gst_amount / 2

    grand_total = subtotal + gst_amount

    # Invoice folder
    if not os.path.exists("invoices"):
        os.makedirs("invoices")

    pdf_path = f"invoices/invoice_{sale_id}.pdf"

    # A4 PDF
    pdf = canvas.Canvas(
        pdf_path,
        pagesize=A4
    )

    width, height = A4
    # =====================================================
    # COMPANY HEADER
    # =====================================================

    pdf.setFont("Helvetica-Bold", 20)
    pdf.setFillColor(colors.HexColor("#333333"))
    pdf.drawString(25 * mm, height - 25 * mm, "Inventory Management")

    pdf.setFont("Helvetica", 9)
    pdf.setFillColor(colors.black)

    pdf.drawString(25 * mm, height - 31 * mm, "Gandhinagar, Gujarat")
    pdf.drawString(25 * mm, height - 36 * mm, "Phone: +91 XXXXX XXXXX")
    pdf.drawString(25 * mm, height - 41 * mm, "Email: inventory@example.com")

    # =====================================================
    # INVOICE TITLE
    # =====================================================

    pdf.setFont("Helvetica-Bold", 28)
    pdf.setFillColor(colors.HexColor("#4A5D9A"))
    pdf.drawRightString(
        width - 25 * mm,
        height - 25 * mm,
        "INVOICE"
    )

    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica", 9)

    pdf.drawRightString(
        width - 25 * mm,
        height - 32 * mm,
        f"DATE: {sale[5]}"
    )

    pdf.drawRightString(
        width - 25 * mm,
        height - 37 * mm,
        f"INVOICE #: {sale[0]}"
    )

    pdf.drawRightString(
        width - 25 * mm,
        height - 42 * mm,
        f"CUSTOMER ID: {sale[0]}"
    )

    # =====================================================
    # BILL TO
    # =====================================================

    bill_y = height - 62 * mm

    pdf.setFillColor(colors.HexColor("#40558F"))

    pdf.rect(
    25 * mm,
    bill_y,
    60 * mm,
    7 * mm,
    fill=1,
    stroke=0
    )

    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 10)

    pdf.drawString(
    28 * mm,
    bill_y + 2 * mm,
    "BILL TO"
    )

    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica", 9)

    # Customer Name
    pdf.drawString(
    25 * mm,
    bill_y - 6 * mm,
    f"Name: {sale[2]}"
    )

    # Customer GSTIN
    pdf.drawString(
    25 * mm,
    bill_y - 12 * mm,
    f"GSTIN: {sale[3] if sale[3] else 'N/A'}"
    )

    # Company
    pdf.drawString(
    25 * mm,
    bill_y - 18 * mm,
    "Company: __________________"
    )

    # Address
    pdf.drawString(
    25 * mm,
    bill_y - 24 * mm,
    "Address: __________________"
    )

    # Phone
    pdf.drawString(
    25 * mm,
    bill_y - 30 * mm,
    "Phone: ____________________"
    )
    # =====================================================
    # PRODUCT TABLE
    # =====================================================

    table_y = height - 105 * mm

    quantity = int(sale[3])
    selling_price = float(sale[4])

    amount = quantity * selling_price

    data = [
        [
            "DESCRIPTION",
            "QTY",
            "PRICE",
            "AMOUNT"
        ],
        [
            sale[1],
            str(quantity),
            f"Rs. {selling_price:.2f}",
            f"Rs. {amount:.2f}"
        ]
    ]

    table = Table(
        data,
        colWidths=[
            95 * mm,
            20 * mm,
            35 * mm,
            35 * mm
        ],
        rowHeights=[
            9 * mm,
            9 * mm
        ]
    )

    table.setStyle(TableStyle([

        # Header
        (
            "BACKGROUND",
            (0, 0),
            (-1, 0),
            colors.HexColor("#40558F")
        ),

        (
            "TEXTCOLOR",
            (0, 0),
            (-1, 0),
            colors.white
        ),

        (
            "FONTNAME",
            (0, 0),
            (-1, 0),
            "Helvetica-Bold"
        ),

        (
            "FONTSIZE",
            (0, 0),
            (-1, -1),
            9
        ),

        (
            "ALIGN",
            (1, 0),
            (-1, -1),
            "RIGHT"
        ),

        (
            "ALIGN",
            (0, 0),
            (0, -1),
            "LEFT"
        ),

        (
            "GRID",
            (0, 0),
            (-1, -1),
            0.5,
            colors.grey
        ),

        (
            "BACKGROUND",
            (0, 1),
            (-1, 1),
            colors.HexColor("#F5F5F5")
        ),

        (
            "FONTNAME",
            (0, 1),
            (-1, 1),
            "Helvetica"
        ),

        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "MIDDLE"
        ),

    ]))

    table.wrapOn(pdf, width, height)
    table.drawOn(
        pdf,
        25 * mm,
        table_y
    )

    # =====================================================
    # TOTAL SECTION WITH GST
    # =====================================================

    total_x = width - 75 * mm

    summary_y = table_y - 18 * mm

    pdf.setFont("Helvetica", 10)
    pdf.setFillColor(colors.black)


    # -----------------------------------------------------
    # SUBTOTAL
    # -----------------------------------------------------

    pdf.drawString(
    total_x,
    summary_y,
    "Subtotal:"
    )

    pdf.drawRightString(
    width - 25 * mm,
    summary_y,
    f"Rs. {subtotal:.2f}"
    )


    # -----------------------------------------------------
    # CGST
    # -----------------------------------------------------

    pdf.drawString(
    total_x,
    summary_y - 7 * mm,
    f"CGST ({gst_rate / 2:.1f}%):"
    )

    pdf.drawRightString(
    width - 25 * mm,
    summary_y - 7 * mm,
    f"Rs. {cgst:.2f}"
    )


    # -----------------------------------------------------
    # SGST  
    # -----------------------------------------------------

    pdf.drawString(
    total_x,
    summary_y - 14 * mm,
    f"SGST ({gst_rate / 2:.1f}%):"
    )

    pdf.drawRightString(
    width - 25 * mm,
    summary_y - 14 * mm,
    f"Rs. {sgst:.2f}"
    )


    # -----------------------------------------------------
    # TOTAL BOX
    # -----------------------------------------------------

    pdf.setFillColor(colors.HexColor("#40558F"))

    pdf.rect(
    total_x - 5 * mm,
    summary_y - 28 * mm,
    55 * mm,
    11 * mm,
    fill=1,
    stroke=0
    )


    pdf.setFillColor(colors.white)

    pdf.setFont(
    "Helvetica-Bold",
    11
    )


    pdf.drawString(
    total_x,
    summary_y - 24 * mm,
    "TOTAL"
    )


    pdf.drawRightString(
    width - 25 * mm,
    summary_y - 24 * mm,
    f"Rs. {grand_total:.2f}"
    )

    # =====================================================
    # OTHER COMMENTS
    # =====================================================

    comment_y = summary_y - 48 * mm

    pdf.setFillColor(colors.HexColor("#40558F"))
    pdf.rect(
        25 * mm,
        comment_y,
        90 * mm,
        7 * mm,
        fill=1,
        stroke=0
    )

    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 9)

    pdf.drawString(
        28 * mm,
        comment_y + 2 * mm,
        "OTHER COMMENTS"
    )

    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica", 8)

    pdf.drawString(
        28 * mm,
        comment_y - 7 * mm,
        "1. Thank you for your business."
    )

    pdf.drawString(
        28 * mm,
        comment_y - 13 * mm,
        "2. Please keep this invoice for your records."
    )

    # =====================================================
    # FOOTER
    # =====================================================

    pdf.setFont("Helvetica", 8)

    pdf.drawCentredString(
        width / 2,
        30 * mm,
        "If you have any questions about this invoice, please contact us."
    )

    pdf.setFont("Helvetica-BoldOblique", 12)

    pdf.drawCentredString(
        width / 2,
        23 * mm,
        "Thank You For Your Business!"
    )

    # Save PDF
    pdf.save()

    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=f"invoice_{sale_id}.pdf"
    )

# =====================================================
# REPORTS
# =====================================================

@app.route("/reports")
def reports():

    cursor = get_cursor()

    cursor.execute("SELECT COUNT(*) FROM products")
    total_products = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM purchases")
    total_purchases = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM sales")
    total_sales = cursor.fetchone()[0]

    cursor.execute("""
        SELECT IFNULL(SUM(price * quantity),0)
        FROM products
    """)
    inventory_value = cursor.fetchone()[0]

    return render_template(
        "reports.html",
        total_products=total_products,
        total_purchases=total_purchases,
        total_sales=total_sales,
        inventory_value=inventory_value
    )


# =====================================================
# LOGOUT
# =====================================================

@app.route("/logout")
def logout():
    return redirect("/")


# =====================================================
# RUN APPLICATION
# =====================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )