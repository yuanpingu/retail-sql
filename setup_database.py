import sqlite3
import pandas as pd

conn = sqlite3.connect("ecommerce.db")
cursor = conn.cursor()

with open("create_tables.sql", "r") as file:
    cursor.executescript(file.read())

df = pd.read_csv("Online Retail 2015 dataset.csv", encoding="utf-8-sig") #read csv

print("Columns before rename:")
print(df.columns.tolist())

df = df.rename(columns={ #rename the columns
    "InvoiceNo": "invoice_no",
    "StockCode": "stock_code",
    "Description": "description",
    "Quantity": "qty",
    "InvoiceDate": "invoice_date",
    "UnitPrice": "price_per_unit",
    "CustomerID": "customer_id",
    "Country": "country_name"
})

print("Columns after rename:")
print(df.columns.tolist())

df["invoice_date"] = pd.to_datetime( #format the date
    df["invoice_date"],
    dayfirst=True,
    errors="coerce"
)

df["invoice_date"] = df["invoice_date"].dt.strftime("%Y-%m-%d %H:%M:%S")

df = df.dropna() #removing invalid rows
df = df.drop_duplicates() #removing duplicated rows

countries_df = (df[["country_name"]].drop_duplicates(subset=["country_name"])) #country table
customers_df = (df[["customer_id"]].drop_duplicates(subset=["customer_id"])) #customer table
products_df = (df[["stock_code", "description"]].drop_duplicates(subset=["stock_code"])) #products table

invoices_df = df[[ #invoices table
    "invoice_no",
    "stock_code",
    "qty",
    "invoice_date",
    "price_per_unit",
    "customer_id",
    "country_name"
]]

# Insert data into SQL tables
countries_df.to_sql("countries", conn, if_exists="append", index=False)
customers_df.to_sql("customers", conn, if_exists="append", index=False)
products_df.to_sql("products", conn, if_exists="append", index=False)
invoices_df.to_sql("invoices", conn, if_exists="append", index=False)

conn.commit()
conn.close()

print("Database created and populated successfully.")