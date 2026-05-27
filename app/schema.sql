CREATE TABLE IF NOT EXISTS company (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    seller_type TEXT NOT NULL DEFAULT 'company',
    name TEXT NOT NULL,
    orgnr TEXT,
    mva INTEGER NOT NULL DEFAULT 0,
    foretaksregisteret INTEGER NOT NULL DEFAULT 0,
    address TEXT,
    email TEXT,
    phone TEXT,
    bank_account TEXT,
    contact_name TEXT,
    contact_email TEXT,
    contact_phone TEXT,
    invoice_number_start INTEGER NOT NULL,
    initialized INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    orgnr TEXT,
    address TEXT,
    email TEXT,
    phone TEXT,
    contact_name TEXT,
    contact_email TEXT,
    contact_phone TEXT
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    unit TEXT,
    unit_price REAL NOT NULL DEFAULT 0,
    vat_percent REAL NOT NULL DEFAULT 25
);

CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_number INTEGER NOT NULL UNIQUE,
    invoice_date TEXT NOT NULL,
    due_date TEXT NOT NULL,

    seller_name TEXT NOT NULL,
    seller_orgnr TEXT NOT NULL,
    seller_mva INTEGER NOT NULL,
    seller_foretaksregisteret INTEGER NOT NULL,
    seller_address TEXT,
    seller_email TEXT,
    seller_phone TEXT,
    seller_bank_account TEXT,
    our_reference TEXT,
    our_reference_email TEXT,
    our_reference_phone TEXT,

    customer_name TEXT NOT NULL,
    customer_orgnr TEXT,
    customer_address TEXT,
    customer_email TEXT,
    customer_phone TEXT,
    customer_reference TEXT,
    customer_reference_email TEXT,
    customer_reference_phone TEXT,

    delivery_place TEXT,
    delivery_date TEXT,

    subtotal REAL NOT NULL,
    vat_total REAL NOT NULL,
    total REAL NOT NULL,

    locked INTEGER NOT NULL DEFAULT 1,
    pdf_filename TEXT
);

CREATE TABLE IF NOT EXISTS invoice_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    quantity REAL NOT NULL,
    unit TEXT,
    unit_price REAL NOT NULL,
    vat_percent REAL NOT NULL,
    line_subtotal REAL NOT NULL,
    line_vat REAL NOT NULL,
    line_total REAL NOT NULL
);
