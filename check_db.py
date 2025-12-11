import sqlite3
import json

# Connect to database
conn = sqlite3.connect('invoicereader.db')
cursor = conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("=== DATABASE TABLES ===")
for table in tables:
    print(f"- {table[0]}")

print("\n=== INVOICES TABLE CONTENT ===")
try:
    cursor.execute("SELECT id, filename, status, extracted_data FROM invoices LIMIT 5;")
    invoices = cursor.fetchall()
    if invoices:
        for invoice in invoices:
            print(f"ID: {invoice[0]}")
            print(f"Filename: {invoice[1]}")
            print(f"Status: {invoice[2]}")
            if invoice[3]:  # extracted_data JSON
                data = json.loads(invoice[3])
                print(f"Extracted Fields: {list(data.get('extracted_fields', {}).keys())}")
            print("---")
    else:
        print("No invoices found in database")
except Exception as e:
    print(f"Error reading invoices: {e}")

print("\n=== FIELD SELECTIONS TABLE ===")
try:
    cursor.execute("SELECT invoice_id, field_name, field_value, selected_for_export FROM field_selections LIMIT 5;")
    selections = cursor.fetchall()
    if selections:
        for sel in selections:
            print(f"Invoice ID: {sel[0]}, Field: {sel[1]}, Value: {sel[2]}, Selected: {sel[3]}")
    else:
        print("No field selections found")
except Exception as e:
    print(f"Error reading field selections: {e}")

conn.close()