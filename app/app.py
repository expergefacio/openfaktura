from datetime import date, timedelta
from pathlib import Path
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    send_file,
    session,
)

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from db import get_db, close_db, init_db

app = Flask(__name__)

app.secret_key = "change-this-random-string"

LOGIN_PASSWORD = "supersecret"

app.teardown_appcontext(close_db)

init_db(app)

PDF_DIR = Path("/data/pdfs")
PDF_DIR.mkdir(parents=True, exist_ok=True)


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper


def rowdict(row):
    return dict(row) if row else None


def get_company():
    return rowdict(
        get_db().execute(
            "SELECT * FROM company WHERE id = 1"
        ).fetchone()
    )


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        if request.form.get("password") == LOGIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("index"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/setup", methods=["GET", "POST"])
@login_required
def setup():

    db = get_db()

    company = get_company()

    if request.method == "POST":

        if company:

            db.execute("""
                UPDATE company SET
                seller_type=?, name=?, orgnr=?, mva=?, foretaksregisteret=?,
                address=?, email=?, phone=?, bank_account=?,
                contact_name=?, contact_email=?, contact_phone=?
                WHERE id=1
            """, (
                request.form["seller_type"],
                request.form["name"],
                request.form.get("orgnr"),
                1 if request.form.get("mva") and request.form["seller_type"] == "company" else 0,
                1 if request.form.get("foretaksregisteret") and request.form["seller_type"] == "company" else 0,
                request.form.get("address"),
                request.form.get("email"),
                request.form.get("phone"),
                request.form.get("bank_account"),
                request.form.get("contact_name"),
                request.form.get("contact_email"),
                request.form.get("contact_phone"),
            ))

        else:

            db.execute("""
                INSERT INTO company
                (
                    id,
                    seller_type,
                    name,
                    orgnr,
                    mva,
                    foretaksregisteret,
                    address,
                    email,
                    phone,
                    bank_account,
                    contact_name,
                    contact_email,
                    contact_phone,
                    invoice_number_start,
                    initialized
                )
                VALUES (
                    1,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1
                )
            """, (
                request.form["seller_type"],
                request.form["name"],
                request.form.get("orgnr"),
                1 if request.form.get("mva") and request.form["seller_type"] == "company" else 0,
                1 if request.form.get("foretaksregisteret") and request.form["seller_type"] == "company" else 0,
                request.form.get("address"),
                request.form.get("email"),
                request.form.get("phone"),
                request.form.get("bank_account"),
                request.form.get("contact_name"),
                request.form.get("contact_email"),
                request.form.get("contact_phone"),
                int(request.form["invoice_number_start"]),
            ))

        db.commit()

        return redirect(url_for("index"))

    return render_template("setup.html", company=company)


@app.route("/customers")
@login_required
def customers():
    return render_template("customers.html")


@app.route("/products")
@login_required
def products():
    return render_template("products.html")


@app.get("/api/customers")
@login_required
def api_customers_get():

    rows = get_db().execute("""
        SELECT
            id,
            name,
            orgnr,
            address,
            email,
            phone,
            contact_name,
            contact_email,
            contact_phone
        FROM customers
        ORDER BY id
    """).fetchall()

    return jsonify([dict(r) for r in rows])


@app.post("/api/customers")
@login_required
def api_customers_save():

    data = request.get_json(force=True)

    db = get_db()

    db.execute("DELETE FROM customers")

    for row in data:

        if not row.get("name"):
            continue

        db.execute("""
            INSERT INTO customers
            (
                name,
                orgnr,
                address,
                email,
                phone,
                contact_name,
                contact_email,
                contact_phone
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row.get("name"),
            row.get("orgnr"),
            row.get("address"),
            row.get("email"),
            row.get("phone"),
            row.get("contact_name"),
            row.get("contact_email"),
            row.get("contact_phone"),
        ))

    db.commit()

    return jsonify({"ok": True})


@app.get("/api/products")
@login_required
def api_products_get():

    rows = get_db().execute("""
        SELECT
            id,
            name,
            description,
            unit,
            unit_price,
            vat_percent
        FROM products
        ORDER BY id
    """).fetchall()

    return jsonify([dict(r) for r in rows])


@app.post("/api/products")
@login_required
def api_products_save():

    data = request.get_json(force=True)

    db = get_db()

    db.execute("DELETE FROM products")

    for row in data:

        if not row.get("name"):
            continue

        db.execute("""
            INSERT INTO products
            (
                name,
                description,
                unit,
                unit_price,
                vat_percent
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            row.get("name"),
            row.get("description"),
            row.get("unit"),
            float(row.get("unit_price") or 0),
            float(row.get("vat_percent") or 0),
        ))

    db.commit()

    return jsonify({"ok": True})


@app.route("/invoices")
@login_required
def invoices():

    rows = get_db().execute("""
        SELECT
            id,
            invoice_number,
            invoice_date,
            due_date,
            customer_name,
            total
        FROM invoices
        ORDER BY invoice_number DESC
    """).fetchall()

    return render_template(
        "invoices.html",
        invoices=rows
    )


@app.route("/invoices/new", methods=["GET", "POST"])
@login_required
def invoice_new():

    db = get_db()

    company = get_company()

    if not company:
        return redirect(url_for("setup"))

    customers = db.execute(
        "SELECT * FROM customers ORDER BY name"
    ).fetchall()

    products = db.execute(
        "SELECT * FROM products ORDER BY name"
    ).fetchall()

    if request.method == "POST":

        customer = rowdict(db.execute(
            "SELECT * FROM customers WHERE id=?",
            (request.form["customer_id"],)
        ).fetchone())

        if not customer:
            return "Missing customer", 400

        last = db.execute(
            "SELECT MAX(invoice_number) AS n FROM invoices"
        ).fetchone()["n"]

        invoice_number = (
            last if last is not None
            else company["invoice_number_start"]
        ) + 1

        subtotal = 0
        vat_total = 0

        lines = []

        descriptions = request.form.getlist("description[]")
        quantities = request.form.getlist("quantity[]")
        units = request.form.getlist("unit[]")
        prices = request.form.getlist("unit_price[]")
        vats = request.form.getlist("vat_percent[]")

        for desc, qty, unit, price, vat in zip(
            descriptions,
            quantities,
            units,
            prices,
            vats
        ):

            if not desc.strip():
                continue

            qty = float(qty or 0)
            price = float(price or 0)
            vat = float(vat or 0)

            line_subtotal = qty * price
            line_vat = line_subtotal * vat / 100
            line_total = line_subtotal + line_vat

            subtotal += line_subtotal
            vat_total += line_vat

            lines.append((
                desc,
                qty,
                unit,
                price,
                vat,
                line_subtotal,
                line_vat,
                line_total
            ))

        total = subtotal + vat_total

        cur = db.execute("""
            INSERT INTO invoices (
                invoice_number,
                invoice_date,
                due_date,

                seller_name,
                seller_orgnr,
                seller_mva,
                seller_foretaksregisteret,
                seller_address,
                seller_email,
                seller_phone,
                seller_bank_account,

                our_reference,
                our_reference_email,
                our_reference_phone,

                customer_name,
                customer_orgnr,
                customer_address,
                customer_email,
                customer_phone,

                customer_reference,
                customer_reference_email,
                customer_reference_phone,

                delivery_place,
                delivery_date,

                subtotal,
                vat_total,
                total,
                locked
            )
            VALUES (
                ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?,
                ?, ?, ?, 1
            )
        """, (

            invoice_number,
            request.form["invoice_date"],
            request.form["due_date"],

            company["name"],
            company["orgnr"],
            company["mva"],
            company["foretaksregisteret"],
            company["address"],
            company["email"],
            company["phone"],
            company["bank_account"],

            company["contact_name"],
            company["contact_email"],
            company["contact_phone"],

            customer["name"],
            customer["orgnr"],
            customer["address"],
            customer["email"],
            customer["phone"],

            customer["contact_name"],
            customer["contact_email"],
            customer["contact_phone"],

            request.form.get("delivery_place"),
            request.form.get("delivery_date"),

            subtotal,
            vat_total,
            total,
        ))

        invoice_id = cur.lastrowid

        for line in lines:

            db.execute("""
                INSERT INTO invoice_lines (
                    invoice_id,
                    description,
                    quantity,
                    unit,
                    unit_price,
                    vat_percent,
                    line_subtotal,
                    line_vat,
                    line_total
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice_id,
                *line
            ))

        db.commit()

        generate_pdf(invoice_id)

        return redirect(
            url_for(
                "invoice_view",
                invoice_id=invoice_id
            )
        )

    today = date.today()

    return render_template(
        "invoice_new.html",
        customers=customers,
        products=products,
        today=today.isoformat(),
        due=(today + timedelta(days=14)).isoformat()
    )


@app.route("/invoices/<int:invoice_id>")
@login_required
def invoice_view(invoice_id):

    db = get_db()

    invoice = db.execute(
        "SELECT * FROM invoices WHERE id=?",
        (invoice_id,)
    ).fetchone()

    lines = db.execute(
        "SELECT * FROM invoice_lines WHERE invoice_id=?",
        (invoice_id,)
    ).fetchall()

    return render_template(
        "invoice_view.html",
        invoice=invoice,
        lines=lines
    )


@app.route("/invoices/<int:invoice_id>/pdf")
@login_required
def invoice_pdf(invoice_id):

    invoice = get_db().execute(
        "SELECT * FROM invoices WHERE id=?",
        (invoice_id,)
    ).fetchone()

    if not invoice or not invoice["pdf_filename"]:
        return "PDF not found", 404

    return send_file(
        PDF_DIR / invoice["pdf_filename"],
        as_attachment=False
    )


def generate_pdf(invoice_id):

    db = get_db()

    invoice = db.execute(
        "SELECT * FROM invoices WHERE id=?",
        (invoice_id,)
    ).fetchone()

    lines = db.execute(
        "SELECT * FROM invoice_lines WHERE invoice_id=?",
        (invoice_id,)
    ).fetchall()

    filename = f"faktura-{invoice['invoice_number']}.pdf"

    path = PDF_DIR / filename

    c = canvas.Canvas(str(path), pagesize=A4)

    w, h = A4

    y = h - 50

    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, y, f"Faktura {invoice['invoice_number']}")

    y -= 40

    c.setFont("Helvetica", 10)

    c.drawString(50, y, f"Dato: {invoice['invoice_date']}")
    c.drawString(250, y, f"Forfall: {invoice['due_date']}")

    y -= 40

    c.drawString(50, y, invoice["seller_name"])

    y -= 14

    if invoice["seller_orgnr"]:

        seller_org = invoice["seller_orgnr"]

        if invoice["seller_mva"]:
            seller_org += " MVA"

        c.drawString(50, y, f"Org.nr: {seller_org}")

        y -= 14

    if invoice["seller_foretaksregisteret"]:

        c.drawString(50, y, "Foretaksregisteret")

        y -= 14

    if invoice["seller_address"]:

        for line in invoice["seller_address"].splitlines():

            c.drawString(50, y, line)

            y -= 14

    y -= 10

    c.drawString(
        50,
        y,
        f"Vår ref.: {invoice['our_reference'] or ''}"
    )

    y = h - 130

    c.drawString(330, y, "Kunde:")

    y -= 14

    c.drawString(330, y, invoice["customer_name"])

    y -= 14

    if invoice["customer_orgnr"]:

        c.drawString(
            330,
            y,
            f"Org.nr: {invoice['customer_orgnr']}"
        )

        y -= 14

    if invoice["customer_address"]:

        for line in invoice["customer_address"].splitlines():

            c.drawString(330, y, line)

            y -= 14

    y -= 10

    c.drawString(
        330,
        y,
        f"Deres ref.: {invoice['customer_reference'] or ''}"
    )

    y = h - 330

    c.setFont("Helvetica-Bold", 9)

    c.drawString(50, y, "Beskrivelse")
    c.drawRightString(320, y, "Antall")
    c.drawString(335, y, "Enh.")
    c.drawRightString(430, y, "Pris")
    c.drawRightString(490, y, "MVA")
    c.drawRightString(550, y, "Sum")

    c.setFont("Helvetica", 9)

    y -= 16

    vat_summary = {}

    for line in lines:

        c.drawString(50, y, line["description"][:45])

        c.drawRightString(
            320,
            y,
            f"{line['quantity']:.2f}"
        )

        c.drawString(335, y, line["unit"] or "")

        c.drawRightString(
            430,
            y,
            f"{line['unit_price']:.2f}"
        )

        c.drawRightString(
            490,
            y,
            f"{line['vat_percent']:.0f}%"
        )

        c.drawRightString(
            550,
            y,
            f"{line['line_total']:.2f}"
        )

        vat_summary.setdefault(
            line["vat_percent"],
            [0, 0]
        )

        vat_summary[line["vat_percent"]][0] += line["line_subtotal"]
        vat_summary[line["vat_percent"]][1] += line["line_vat"]

        y -= 16

    y -= 20

    c.drawRightString(
        550,
        y,
        f"Netto: {invoice['subtotal']:.2f}"
    )

    y -= 16

    c.drawRightString(
        550,
        y,
        f"MVA: {invoice['vat_total']:.2f}"
    )

    y -= 16

    c.setFont("Helvetica-Bold", 11)

    c.drawRightString(
        550,
        y,
        f"Å betale: {invoice['total']:.2f}"
    )

    y -= 40

    c.setFont("Helvetica-Bold", 9)

    c.drawString(50, y, "MVA-spesifikasjon")

    c.setFont("Helvetica", 9)

    y -= 16

    for vat, sums in sorted(vat_summary.items()):

        c.drawString(
            50,
            y,
            f"{vat:.0f}% grunnlag: {sums[0]:.2f}    MVA: {sums[1]:.2f}"
        )

        y -= 14

    y -= 20

    c.drawString(
        50,
        y,
        f"Bankkonto: {invoice['seller_bank_account'] or ''}"
    )

    c.save()

    db.execute(
        "UPDATE invoices SET pdf_filename=? WHERE id=?",
        (filename, invoice_id)
    )

    db.commit()
