import sqlite3
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from streamlit_mermaid_interactive import mermaid
from pathlib import Path
import subprocess
import sys


DB_PATH = Path("ecommerce.db")

if not DB_PATH.exists():
    subprocess.run([sys.executable, "setup_database.py"], check=True)



st.title("Online retail SQL dashboard", text_alignment="center")
st.write("This app aims to visualize online retail data using SQL queries.")

conn = sqlite3.connect("ecommerce.db") #connecting to the database with the dataset



#Database introduction
st.header("Database Overview", divider=True, text_alignment="center")
st.write("This section gives a brief overview of the database structure and relationships.")
st.subheader("Entity Relationship Diagram (ERD) of database") 

erd_code = """
erDiagram

    COUNTRIES ||--o{ CUSTOMERS : has

    CUSTOMERS ||--o{ INVOICES : places

    PRODUCTS |{--o{ INVOICES : in
"""

mermaid(erd_code)

create_tables = """
CREATE TABLE IF NOT EXISTS countries (
	country_name			VARCHAR(64) 	PRIMARY KEY);

CREATE TABLE IF NOT EXISTS customers (
	customer_id 				INTEGER 		PRIMARY KEY);

CREATE TABLE IF NOT EXISTS products (
	stock_code 			VARCHAR(12) 	PRIMARY KEY, 
	description 	VARCHAR(128) 	
);

CREATE TABLE IF NOT EXISTS invoices (
	invoice_no 		VARCHAR(12) 	NOT NULL,
	stock_code		VARCHAR(12)		NOT NULL
		REFERENCES products (stock_code) ON UPDATE CASCADE ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED,
	qty				INTEGER			NOT NULL,
	invoice_date	TIMESTAMP		NOT NULL,
	price_per_unit 	NUMERIC(10,2)	NOT NULL,
	customer_id 	INTEGER		
		REFERENCES customers (customer_id) ON UPDATE CASCADE ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED,
	country_name	VARCHAR(64) 	NOT NULL
		REFERENCES countries (country_name) ON UPDATE CASCADE ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED
	
);
"""

st.subheader("Explanation of ERD")
st.write("A customer can only belong to :green[1 country], while a country can be assigned to :green[none or multiple customers]. " 
        "A customer can place :green[none or multiple invoices], while an invoice must only be placed by :green[a single customer]. "
        "A product can be in :green[none or multiple invoices], while each invoice must have at least :green[1 product or multiple products].")

with st.expander("Show SQL create tables code"):
    st.code(create_tables, language="sql")

st.space(50)
















# Revenue section 
st.header("Revenue Overview", divider=True, text_alignment="center")

#code 
query_monthly_revenue = """
SELECT 
    strftime('%Y-%m', invoice_date) AS month,
    SUM(qty * price_per_unit) AS total_revenue
FROM invoices
GROUP BY strftime('%Y-%m', invoice_date)
ORDER BY month;
"""
monthly_revenue_df = pd.read_sql_query(query_monthly_revenue, conn)

#description
st.write("This section analyzes the changes in total revenue over time as well as other business trends.")

st.subheader("Monthly net revenue")
st.dataframe(monthly_revenue_df)

fig, ax = plt.subplots()
ax.plot(monthly_revenue_df["month"], monthly_revenue_df["total_revenue"], marker="o")
ax.set_xlabel("Month")
ax.set_ylabel("Monthly Revenue")
ax.set_title("Graph of net revenue against month")
ax.tick_params(axis="x", rotation=45)
st.pyplot(fig)

max_row_mr = monthly_revenue_df.loc[monthly_revenue_df["total_revenue"].idxmax()]
min_row_mr = monthly_revenue_df.loc[monthly_revenue_df["total_revenue"].idxmin()]

max_mr_month = pd.to_datetime(str(max_row_mr['month'])).strftime("%B of %Y")
min_mr_month = pd.to_datetime(str(min_row_mr['month'])).strftime("%B of %Y")

st.success(f"The monthly net revenues were generally :red[**increasing**] with a maximum of "
         f"**\\${max_row_mr['total_revenue']:,.2f}** in {max_mr_month}"
         f" and a minimum of **${min_row_mr['total_revenue']:,.2f}** in {min_mr_month}.")


with st.expander("Show SQL query for monthly revenue"):
    st.code(query_monthly_revenue, language="sql")
    
st.space(10)




#code 
query_top_products_rev = """
SELECT i.stock_code,
	p.description,
	SUM(qty) AS total_qty_sold,
	SUM(qty * price_per_unit) AS revenue
FROM invoices i 
JOIN products p ON i.stock_code = p.stock_code
GROUP BY i.stock_code, p.description
ORDER BY revenue DESC;
"""
top_products_rev_df = pd.read_sql_query(query_top_products_rev, conn)

#description
st.subheader("Top Products by net revenue")
st.dataframe(top_products_rev_df)

top10_products_df = top_products_rev_df.sort_values(by="revenue", ascending=False)
top_10_rev = top_products_rev_df.head(10)

st.subheader("Top 10 products by net revenue")
st.bar_chart(top_10_rev[["description", "revenue"]], x="description", y="revenue", sort=False)

with st.expander("Show SQL query for top products by net revenue"):
    st.code(query_top_products_rev, language="sql")

st.space(10)


query_total_rev = """
SELECT SUM(qty * price_per_unit) AS total_revenue
FROM invoices
"""
total_rev = pd.read_sql_query(query_total_rev, conn)["total_revenue"].iloc[0]

query_amr = """
SELECT SUM(qty * price_per_unit) / COUNT(DISTINCT strftime('%Y-%m', invoice_date)) AS avg_monthly_revenue
FROM invoices
"""
avg_mr = pd.read_sql_query(query_amr, conn)["avg_monthly_revenue"].iloc[0]


st.subheader("Revenue conclusion")
st.write(f"The total net revenue was :green[**\\${total_rev:,.2f}**] and the average monthly net revenue was :green[**\\${avg_mr:,.2f}**]."
           f" The month that generated the highest net revenue was {max_row_mr['month']} with a net revenue of :green[**\\${max_row_mr['total_revenue']:,.2f}**],"
           f" and the top performing product in generating net revenue was the {top_10_rev.head(1)['description'].values[0].title()}"
           f" which generated a total revenue of :green[**${top_10_rev.head(1)['revenue'].values[0]:,.2f}**].")

with st.expander("Show SQL query for total net revenue"):
    st.code(query_total_rev, language="sql")
with st.expander("Show SQL query for average monthly net revenue"):
    st.code(query_amr, language="sql")
    
st.space(50)









# Invoices section 
st.header("Invoices Analysis", divider=True, text_alignment="center")
st.write("This section analyzes invoice-level trends, including monthly invoice volume, average invoice value, and average units per invoice.")


# Monthly invoices
query_monthly_invoices = """
SELECT 
    strftime('%Y-%m', invoice_date) AS month,
    COUNT(DISTINCT invoice_no) AS total_invoices
FROM invoices
GROUP BY month
ORDER BY month;
"""

monthly_invoices_df = pd.read_sql_query(query_monthly_invoices, conn)

st.subheader("Monthly Invoices")
st.dataframe(monthly_invoices_df)

fig, ax = plt.subplots()
ax.plot(monthly_invoices_df["month"], monthly_invoices_df["total_invoices"], marker="o")
ax.set_xlabel("Month")
ax.set_ylabel("Monthly Invoices")
ax.set_title("Graph of Invoices Against Month")
ax.tick_params(axis="x", rotation=45)
st.pyplot(fig)

max_row_mi = monthly_invoices_df.loc[monthly_invoices_df["total_invoices"].idxmax()]
min_row_mi = monthly_invoices_df.loc[monthly_invoices_df["total_invoices"].idxmin()]

max_mi_month = pd.to_datetime(str(max_row_mi['month'])).strftime("%B of %Y")
min_mi_month = pd.to_datetime(str(min_row_mi['month'])).strftime("%B of %Y")

st.success(
    f"The monthly invoices were generally :red[**increasing**], with a maximum of "
    f"**{max_row_mi['total_invoices']}** invoices in {max_mi_month} "
    f"and a minimum of **{min_row_mi['total_invoices']}** invoices in {min_mi_month}."
)

with st.expander("Show SQL query for monthly invoices"):
    st.code(query_monthly_invoices, language="sql")

st.space(10)


# Average monthly invoice value
query_avg_invoice_val = """
SELECT 
    month, 
    AVG(total_invoice_value) AS avg_invoice_value
FROM (
    SELECT 
        strftime('%Y-%m', invoice_date) AS month,
        invoice_no, 
        SUM(qty * price_per_unit) AS total_invoice_value
    FROM invoices
    GROUP BY month, invoice_no
)
GROUP BY month
ORDER BY month;
"""

avg_invoice_val_df = pd.read_sql_query(query_avg_invoice_val, conn)

st.subheader("Average Monthly Invoice Value")
st.dataframe(avg_invoice_val_df)

fig, ax = plt.subplots()
ax.plot(avg_invoice_val_df["month"], avg_invoice_val_df["avg_invoice_value"], marker="o")
ax.set_xlabel("Month")
ax.set_ylabel("Average Monthly Invoice Value")
ax.set_title("Graph of Average Invoice Value Against Month")
ax.tick_params(axis="x", rotation=45)
st.pyplot(fig)

max_row_aiv = avg_invoice_val_df.loc[avg_invoice_val_df["avg_invoice_value"].idxmax()]
min_row_aiv = avg_invoice_val_df.loc[avg_invoice_val_df["avg_invoice_value"].idxmin()]

max_aiv_month = pd.to_datetime(str(max_row_aiv['month'])).strftime("%B of %Y")
min_aiv_month = pd.to_datetime(str(min_row_aiv['month'])).strftime("%B of %Y")

st.success(
    f"The average monthly invoice values were generally :red[**increasing**], with a maximum value of "
    f"**\\${max_row_aiv['avg_invoice_value']:,.2f}** in {max_aiv_month} "
    f"and a minimum value of **\\${min_row_aiv['avg_invoice_value']:,.2f}** in {min_aiv_month}."
)

with st.expander("Show SQL query for average monthly invoice value"):
    st.code(query_avg_invoice_val, language="sql")

st.space(10)


# Average monthly units per invoice
query_units_per_invoice = """
SELECT 
    month, 
    AVG(units_per_invoice) AS avg_units_per_invoice
FROM (
    SELECT 
        strftime('%Y-%m', invoice_date) AS month, 
        invoice_no,
        SUM(qty) AS units_per_invoice
    FROM invoices
    GROUP BY month, invoice_no
)
GROUP BY month
ORDER BY month;
"""

units_per_invoice_df = pd.read_sql_query(query_units_per_invoice, conn)

st.subheader("Average Monthly Units per Invoice")
st.dataframe(units_per_invoice_df)

fig, ax = plt.subplots()
ax.plot(
    units_per_invoice_df["month"],
    units_per_invoice_df["avg_units_per_invoice"],
    marker="o"
)
ax.set_xlabel("Month")
ax.set_ylabel("Average Units per Invoice")
ax.set_title("Graph of Average Units per Invoice Against Month")
ax.tick_params(axis="x", rotation=45)
st.pyplot(fig)

max_row_upi = units_per_invoice_df.loc[units_per_invoice_df["avg_units_per_invoice"].idxmax()]
min_row_upi = units_per_invoice_df.loc[units_per_invoice_df["avg_units_per_invoice"].idxmin()]

max_upi_month = pd.to_datetime(str(max_row_upi['month'])).strftime("%B of %Y")
min_upi_month = pd.to_datetime(str(min_row_upi['month'])).strftime("%B of %Y")

st.success(
    f"The average monthly units per invoice were generally :red[**increasing**], with a maximum of "
    f"**{max_row_upi['avg_units_per_invoice']:,.0f}** units on average in {max_upi_month} "
    f"and a minimum of **{min_row_upi['avg_units_per_invoice']:,.0f}** units on average in {min_upi_month}."
)

with st.expander("Show SQL query for average monthly units per invoice"):
    st.code(query_units_per_invoice, language="sql")

st.space(10)


# Invoices conclusion
st.subheader("Invoices Conclusion")

query_total_inv = """
SELECT 
    COUNT(DISTINCT invoice_no) AS total_invoices
FROM invoices;
"""

total_inv = pd.read_sql_query(query_total_inv, conn)["total_invoices"].iloc[0]

query_avg_monthly_inv = """
SELECT 
    COUNT(DISTINCT invoice_no) / COUNT(DISTINCT strftime('%Y-%m', invoice_date)) AS avg_monthly_invoices
FROM invoices;
"""

avg_monthly_inv = pd.read_sql_query(query_avg_monthly_inv, conn)["avg_monthly_invoices"].iloc[0]


st.write(
    f"The total number of invoices was :green[**{total_inv}**], and the average monthly invoice count was "
    f":green[**{avg_monthly_inv}**]. "
    f"The month with the largest number of invoices was {max_row_mi['month']} with "
    f":green[**{max_row_mi['total_invoices']}**] invoices."
)

with st.expander("Show SQL query for total invoices"):
    st.code(query_total_inv, language="sql")

with st.expander("Show SQL query for average monthly invoices"):
    st.code(query_avg_monthly_inv, language="sql")

st.space(50)










# Products section 
st.header("Products Analysis", divider=True, text_alignment="center")
st.write("This section analyzes the gross and net performance of products, including the best and worst performing product sold.")


query_net_performance = """
SELECT 
    i.stock_code,
    p.description,
    SUM(CASE WHEN i.qty > 0 THEN i.qty ELSE 0 END) AS gross_qty_sold,
    ABS(SUM(CASE WHEN i.qty < 0 THEN i.qty ELSE 0 END)) AS qty_returned,
    SUM(i.qty) AS net_qty_sold,
    SUM(CASE WHEN i.qty > 0 THEN i.qty * i.price_per_unit ELSE 0 END) AS gross_revenue,
    ABS(SUM(CASE WHEN i.qty < 0 THEN i.qty * i.price_per_unit ELSE 0 END)) AS refund_value,
    SUM(i.qty * i.price_per_unit) AS net_revenue
FROM invoices i
JOIN products p 
ON i.stock_code = p.stock_code

GROUP BY i.stock_code, p.description
ORDER BY net_revenue DESC;
"""

performance_df = pd.read_sql_query(query_net_performance, conn)

st.subheader("Net performance of products sorted by descending net revenue")
st.dataframe(performance_df)

st.info("Negative net quantity sold and net revenue would imply that the product was not purchased in the timeframe of the current dataset, " \
"but was refunded in this timeframe hence causing the amount returned to be larger than the amount sold.")

with st.expander("Show SQL query for products performance"):
    st.code(query_net_performance, language="sql")


st.space(10)





# Top products by net quantity sold
query_top_products_nqs = """
SELECT 
    i.stock_code,
    p.description,
    SUM(qty) AS total_qty_sold,
    SUM(qty * price_per_unit) AS revenue
FROM invoices i 
JOIN products p 
ON i.stock_code = p.stock_code
GROUP BY i.stock_code, p.description
ORDER BY total_qty_sold DESC;
"""

top_products_nqs_df = pd.read_sql_query(query_top_products_nqs, conn)

st.subheader("Top Products by Net Quantity Sold")
st.dataframe(top_products_nqs_df)

top_10_nqs = top_products_nqs_df.head(10)

st.subheader("Top 10 Products by Net Quantity Sold")
st.bar_chart(
    top_10_nqs[["description", "total_qty_sold"]],
    x="description",
    y="total_qty_sold",
    sort=False
)

with st.expander("Show SQL query for top products by net quantity sold"):
    st.code(query_top_products_nqs, language="sql")

st.space(10)

top_productn_name = top_10_nqs.head(1)["description"].values[0].title()
top_productn_qty = top_10_nqs.head(1)["total_qty_sold"].values[0]



# Top products by gross quantity sold
query_top_products_qs = """
SELECT 
    i.stock_code,
    p.description,
    SUM(qty) AS total_qty_sold,
    SUM(qty * price_per_unit) AS revenue
FROM invoices i 
JOIN products p 
ON i.stock_code = p.stock_code
WHERE i.qty > 0
GROUP BY i.stock_code, p.description
ORDER BY total_qty_sold DESC;
"""

top_products_qs_df = pd.read_sql_query(query_top_products_qs, conn)

st.subheader("Top Products by Gross Quantity Sold")
st.dataframe(top_products_qs_df)

top_10_qs = top_products_qs_df.head(10)

st.subheader("Top 10 Products by Gross Quantity Sold")
st.bar_chart(
    top_10_qs[["description", "total_qty_sold"]],
    x="description",
    y="total_qty_sold",
    sort=False
)

with st.expander("Show SQL query for top products by gross quantity sold"):
    st.code(query_top_products_qs, language="sql")

st.space(10)

top_productg_name = top_10_qs.head(1)["description"].values[0].title()
top_productg_qty = top_10_qs.head(1)["total_qty_sold"].values[0]



#code 
query_least_products_qs = """
SELECT i.stock_code,
	p.description,
	SUM(qty) AS total_qty_sold,
	SUM(qty * price_per_unit) AS revenue
FROM invoices i 
JOIN products p ON i.stock_code = p.stock_code
WHERE i.qty >= 0
GROUP BY i.stock_code, p.description
ORDER BY total_qty_sold ASC;
"""
least_products_qs_df = pd.read_sql_query(query_least_products_qs, conn)

#description
st.subheader("Worst Selling Products (Gross)")
st.dataframe(least_products_qs_df)

st.info("Finding the worst performing products in terms of :green[net] quantity sold is not very meaningful as some products" \
" could have negative quantity sold due to the purchase being made in a seperate timeframe.")

with st.expander("Show SQL query for least gross sold products"):
    st.code(query_least_products_qs, language="sql")



st.space(10)


#code 
query_refunded_products = """
SELECT i.stock_code,
	p.description,
	ABS(SUM(CASE WHEN i.qty < 0 THEN i.qty ELSE 0 END)) AS total_qty_refunded,
	ABS(SUM(CASE WHEN i.qty > 0 THEN i.qty ELSE 0 END )) AS total_gross_quantity_sold,
    ABS(SUM(CASE WHEN i.qty < 0 THEN i.qty * i.price_per_unit ELSE 0 END)) AS refund_value,
    ROUND(ABS(SUM(CASE WHEN i.qty < 0 THEN i.qty ELSE 0 END)) * 100.0
        / NULLIF(SUM(CASE WHEN i.qty > 0 THEN i.qty ELSE 0 END), 0),
        2
    ) AS refund_percentage
FROM invoices i 
JOIN products p ON i.stock_code = p.stock_code
GROUP BY i.stock_code, p.description
ORDER BY refund_percentage DESC;
"""
refunded_products_df = pd.read_sql_query(query_refunded_products, conn)

#description
st.subheader("Most Refunded Products")
st.dataframe(refunded_products_df)

most_refunded_product_p = refunded_products_df.head(1)["description"].values[0].title()
most_refunded_percent = refunded_products_df.head(1)["refund_percentage"].values[0]

top_qty_row = refunded_products_df.loc[refunded_products_df["total_qty_refunded"].idxmax()]
most_refunded_product_qs = top_qty_row["description"].title()
most_refunded_qty = top_qty_row["total_qty_refunded"]


with st.expander("Show SQL query for most refunded products"):
    st.code(query_refunded_products, language="sql")

st.space(10)

st.subheader("Products conclusion")
st.write(f"The top performing product in terms of net quantity sold is :green[{top_productn_name}] with **:green[{top_productn_qty}]** units sold and"
         f" :green[{top_productg_name}] in terms of gross quantity sold with **:green[{top_productg_qty}]** units sold."
         f" The product with the most quantity refunded is :red[{most_refunded_product_qs}] with a total of **:red[{most_refunded_qty}]** units refunded."
         f" The most refunded product in terms of refund percentage is :red[{most_refunded_product_p}] with **:red[{most_refunded_percent}%]** refunded,"
         " suggesting that more units were bought from a seperated timeframe and refunded in the timeframe of the dataset.")


st.space(50)











# Customers section
st.header("Customer Analysis", divider=True, text_alignment="center")
st.write("This section analyzes the customers' spendings and uniqueness.")




#code
query_uniqcust = """
SELECT 
    strftime('%Y-%m', invoice_date) AS month, 
    COUNT(DISTINCT customer_id) AS total_unique_customers
FROM invoices
GROUP BY month;
"""
unique_customers_df = pd.read_sql_query(query_uniqcust, conn)

#description
st.subheader("Quantity of monthly unique customers")
st.dataframe(unique_customers_df)

fig, ax = plt.subplots()
ax.plot(unique_customers_df["month"], unique_customers_df["total_unique_customers"], marker="o")
ax.set_xlabel("Month")
ax.set_ylabel("Unique customers")
ax.set_title("Graph of Unique Customers Against Month")
ax.tick_params(axis="x", rotation=45)
st.pyplot(fig)

max_uc = unique_customers_df.loc[unique_customers_df["total_unique_customers"].idxmax()]
min_uc = unique_customers_df.loc[unique_customers_df["total_unique_customers"].idxmin()]

max_uc_month = pd.to_datetime(str(max_uc['month'])).strftime("%B of %Y")
min_uc_month = pd.to_datetime(str(min_uc['month'])).strftime("%B of %Y")

st.success("The total number of monthly unique customers was generally :red[increasing] with a maximum of "
           f"**{max_uc['total_unique_customers']}** in {max_uc_month} and a minimum of "
           f"**{min_uc['total_unique_customers']}** in {min_uc_month}.")

with st.expander("Show SQL query for monthly unique customers"):
    st.code(query_uniqcust, language= "sql")

st.space(10)




#code
query_repcust = """
SELECT month, COUNT(*) AS total_repeat_customers
FROM (
    SELECT strftime('%Y-%m', invoice_date) AS month, customer_id
    FROM invoices
    GROUP BY month, customer_id
    HAVING COUNT(*) > 1
)
GROUP BY month;
"""
repeat_customers_df = pd.read_sql_query(query_repcust, conn)

#description
st.subheader("Quantity of monthly repeat customers")
st.dataframe(repeat_customers_df)

fig, ax = plt.subplots()
ax.plot(repeat_customers_df["month"], repeat_customers_df["total_repeat_customers"], marker="o")
ax.set_xlabel("Month")
ax.set_ylabel("Repeat customers")
ax.set_title("Graph of Repeat Customers Against Month")
ax.tick_params(axis="x", rotation=45)
st.pyplot(fig)

max_rc = repeat_customers_df.loc[repeat_customers_df["total_repeat_customers"].idxmax()]
min_rc = repeat_customers_df.loc[repeat_customers_df["total_repeat_customers"].idxmin()]

max_rc_month = pd.to_datetime(str(max_rc['month'])).strftime("%B of %Y")
min_rc_month = pd.to_datetime(str(min_rc['month'])).strftime("%B of %Y")

st.success("The total number of monthly repeat customers was generally :red[increasing] with a maximum of "
           f"**{max_rc['total_repeat_customers']}** in {max_rc_month} and a minimum of "
           f"**{min_rc['total_repeat_customers']}** in {min_rc_month}.")

with st.expander("Show SQL query for monthly repeat customers"):
    st.code(query_repcust, language= "sql")

st.space(10)


#code
query_top_customer = """
SELECT month, customer_id, MAX(total_spent) AS max_spending
FROM (
    SELECT 
        strftime('%Y-%m', invoice_date) AS month,
        customer_id,
        SUM(qty * price_per_unit) AS total_spent
    FROM invoices
    GROUP BY month, customer_id
)
GROUP BY month;
"""
top_customer_df = pd.read_sql_query(query_top_customer, conn)

#description
st.subheader("Top spending customer per month")
st.dataframe(top_customer_df)

fig, ax = plt.subplots()
ax.plot(top_customer_df["month"], top_customer_df["max_spending"], marker="o")
ax.set_xlabel("Month")
ax.set_ylabel("Total spending by top customer")
ax.set_title("Graph of Top Amount Spent Against Month")
ax.tick_params(axis="x", rotation=45)
st.pyplot(fig)

max_c = top_customer_df.loc[top_customer_df["max_spending"].idxmax()]
min_c = top_customer_df.loc[top_customer_df["max_spending"].idxmin()]

max_c_month = pd.to_datetime(str(max_c['month'])).strftime("%B of %Y")
min_c_month = pd.to_datetime(str(min_c['month'])).strftime("%B of %Y")

st.success(f"The top spending customer was customer {max_c['customer_id']} who spent "
           f":red[**${max_c['max_spending']:,.2f}**] in {max_c_month}. "
           f"The lowest spending customer among monthly top customers was customer {min_c['customer_id']} "
           f"who spent :red[**${min_c['max_spending']:,.2f}**] in {min_c_month}.")

with st.expander("Show SQL query for monthly top spenders"):
    st.code(query_top_customer, language= "sql")

st.space(10)



#code
query_avg_cs = """
SELECT month, ROUND(AVG(amount_spent), 2) AS avg_customer_spending
FROM (
    SELECT 
        strftime('%Y-%m', invoice_date) AS month, 
        customer_id, 
        SUM(qty * price_per_unit) AS amount_spent
    FROM invoices
    GROUP BY month, customer_id
)
GROUP BY month;
"""
avg_cs_df = pd.read_sql_query(query_avg_cs, conn)

#description
st.subheader("Average customer spend per month")
st.dataframe(avg_cs_df)

fig, ax = plt.subplots()
ax.plot(avg_cs_df["month"], avg_cs_df["avg_customer_spending"], marker="o")
ax.set_xlabel("Month")
ax.set_ylabel("Average spending per customer")
ax.set_title("Graph of Average Customer Spending Against Month")
ax.tick_params(axis="x", rotation=45)
st.pyplot(fig)

max_acs = avg_cs_df.loc[avg_cs_df["avg_customer_spending"].idxmax()]
min_acs = avg_cs_df.loc[avg_cs_df["avg_customer_spending"].idxmin()]

max_acs_month = pd.to_datetime(str(max_acs['month'])).strftime("%B of %Y")
min_acs_month = pd.to_datetime(str(min_acs['month'])).strftime("%B of %Y")

st.success(f"The largest average customer spending was :red[**${max_acs['avg_customer_spending']:,.2f}**] in {max_acs_month}, "
           f"while the lowest average customer spending was :red[**${min_acs['avg_customer_spending']:,.2f}**] in {min_acs_month}.")

with st.expander("Show SQL query for monthly average customer spending"):
    st.code(query_avg_cs, language= "sql")

st.space(10)


#Customer conclusion
st.subheader("Customers conclusion")
st.write(f"The largest amount of unique and repeating customers was in :green[{max_uc_month}] with "
         f"**:green[{max_uc['total_unique_customers']}]** unique customers and **:green[{max_rc['total_repeat_customers']}]** repeat customers recorded. "
         f"The least amount of unique and repeating customers was in :red[{min_uc_month}] with "
         f"**:red[{min_uc['total_unique_customers']}]** unique customers and **:red[{min_rc['total_repeat_customers']}]** repeat customers recorded. "
         f"The largest average customer spend was in :green[{max_acs_month}] at :green[**${max_acs['avg_customer_spending']:,.2f}**]. "
         " This month also recorded the highest individual customer spending, "
         f"with customer {max_c['customer_id']} spending :green[**${max_c['max_spending']:,.2f}**]."         
         )




