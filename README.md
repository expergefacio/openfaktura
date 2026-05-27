# OpenFaktura

Minimal self-hosted Norwegian invoice (`faktura`) system built with:

- Ai
- Flask
- SQLite
- ReportLab
- jspreadsheet-ce
- Docker

Designed to stay intentionally simple:

- no accounts/users
- no external services
- no email integration
- no payment integration
- no ERP/accounting system
- locked invoices after creation
- local PDF generation
- LAN/selfhost friendly

---

# Features

- Company or private-person issuer
- Customer registry
- Product/service registry
- Invoice PDF generation
- Locked invoice snapshots
- Norwegian VAT (`MVA`) support
- VAT summaries per rate
- Sequential invoice numbering
- Very small/simple codebase
- Basic password protection

---

# Requirements

- Docker
- Docker Compose

Example host platforms:

- Ubuntu
- Debian
- macOS
- Unraid
- Synology (with Docker)

---

# Install

Clone repository:

```bash
git clone https://github.com/expergefacio/openfaktura.git
cd openfaktura
```

Create data directory:

```bash
mkdir -p data/pdfs
```

---

# Configure Password

Edit:

```text
app/app.py
```

Change:

```python
LOGIN_PASSWORD = "supersecret"
```

to your own password.

Also change:

```python
app.secret_key = "change-this-random-string"
```

to random garbage.

Example:

```python
app.secret_key = "f83j2f9j23fj239fj23f"
LOGIN_PASSWORD = "correct horse battery staple"
```

---

# Run

Build and start:

```bash
docker compose up --build
```

Open:

```text
http://YOUR-IP:41414
```

Example:

```text
http://192.168.1.50:41414
```

---

# First Setup

On first startup:

1. Open `/setup`
2. Configure issuer/company info
3. Set current invoice number

Example:

```text
10025
```

Next invoice becomes:

```text
10026
```

Invoice start number becomes locked after initialization.

---

# Usage

## Customers

Add/edit customers:

```text
Kunder
```

Includes:

- customer name
- org number
- address
- contact person
- email
- phone

---

## Products

Add/edit products/services:

```text
Varer/tjenester
```

Includes:

- name
- description
- unit
- price
- VAT rate

---

## Invoices

Create invoices:

```text
Ny faktura
```

Features:

- customer selection
- product selection
- auto-fill VAT
- auto-fill delivery address
- multiple invoice lines
- PDF generation

Invoices are locked after creation.

---

# Data Storage

Everything is stored locally in:

```text
./data
```

SQLite database:

```text
./data/faktura.sqlite
```

Generated PDFs:

```text
./data/pdfs
```

---

# Backup

Backup the entire data directory:

```bash
tar czf openfaktura-backup.tar.gz data/
```

Restore:

```bash
tar xzf openfaktura-backup.tar.gz
```

---

# Update

Pull latest changes:

```bash
git pull
docker compose up --build -d
```

---

# Notes

This is intentionally an MVP/simple system.

Not intended to replace:

- Tripletex
- Fiken
- Visma
- ERP/accounting systems

Goal is:

```text
simple self-hosted invoice generation
```

for small/internal/simple use cases.

---

# License

MIT License.
