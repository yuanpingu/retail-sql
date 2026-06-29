# Online retail SQL dashboard
This app aims to visualize online retail data using SQL queries and graphs.

## Demo App
[![Open in Streamlit](https://img.shields.io/badge/Open%20in-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://retail-sql-3fstunbfbbmrdyhcgt7nau.streamlit.app/)

## Dataset
This project was inspired by and developed using the Online Retail (2015) dataset from the UC Irvine Machine Learning Repository.

Dataset citation: Chen, D. (2015). Online Retail [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5BW33.

## Variables
- InvoiceNo (Categorical) - Unique number assigned to each transaction
- StockCode (Categorical) - Unique number assigned to distinct products
- Description (Categorical) - Product name
- Quantity (Numerical) - Quantities of each product per transaction
- InvoiceDate (Numerical) - Day and time of each transaction
- UnitPrice (Numerical) - Product price per unit
- CustomerID (Categorical) - Unique number assigned to each customer
- Country (Categorical) - Name of the country the customer resides in 

## Features
- Database creation
- Entity relationship diagram
- Individual overviews
- Graphs to visualize trends

## Tools
- Python
- Streamlit
- pandas

## How to use the app
1. Install required packages using 'pip install -r requirements.txt'
2. Run the app using 'streamlit run streamlit_app.py'

## Further Reading
- [Python Documentation](https://docs.python.org/3/)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [Streamlit Documentation](https://docs.streamlit.io/)

