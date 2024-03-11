import os
import xml.etree.ElementTree as ET
import xml.dom.minidom
from argparse import ArgumentParser
import pyodbc
import tempfile
import argparse

sql_server_name = '127.0.0.1,1533'
database_name = 'STT'
username = 'sa'
password = '@DevelopmentPassword1'

Data = {}

connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={sql_server_name};DATABASE={database_name};UID={username};PWD={password}'
sql_server_connection = pyodbc.connect(connection_string)

cursor = sql_server_connection.cursor()

queries = {
    'Q0': """
        SELECT RIGHT(Products.ProductCode, 2) AS PROD_ID, 
                Products.ProductCode AS PROD_CODE, 
                Products.ProductName AS PROD_NAME,
                Products.ManufactID AS MANUF_ID, 
                20 AS SERIAL_NO_LENGTH, 
                20 AS DEFAULT_BOX_QTY,
                'false' AS AIRTIME_PRELOADED, 
                RIGHT(Products.ProductCode, 2) AS NEW_PROD_ID
        FROM InvoiceDetail
        INNER JOIN Products WITH (nolock) ON InvoiceDetail.ProductID = Products.ProductID
        WHERE InvoiceDetail.InvoiceID = 2.
        for xml path ('CProduct'), root ('P')
        """,
    'Q1': """
        SELECT Invoice.InvoiceID as [INVOICE_NO], 
                Invoice.InvoiceNumber as [REFERENCE], 
                1 as [WAREHOUSE_ID],
                38248 as [CUST_ID], 
                Customer.CustomerCode as [CUST_CODE], 
                Invoice.CreateDate as [INVOICE_DATE], 
                11 as [SALES_PERSON_ID], 
                'true' as [POSTED]
        FROM Invoice
        INNER JOIN Customer WITH (nolock) ON Invoice.CustomerID = Customer.CustomerID
        WHERE Invoice.InvoiceID = 2
        for xml path ('H')
        """,  
}


def store_dict_to_tempfile(Data):
 
 with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:

    for query_value in Data['Q0']:
         temp_file.write(query_value[0])
        
    for query_value in Data['Q1']:
        temp_file.write(query_value[0])

    return temp_file.name


def read_queries_from_file(file_path):
    with open(file_path, 'r') as file:
        return [query.strip() for query in file.readlines()]
    
parser = ArgumentParser()

parser = argparse.ArgumentParser(description='Python bcp program.')
parser.add_argument('-d', '--database', help="Database name", required=False, default="STT")
parser.add_argument('-q', '--queries', nargs='+', help="SQL queries", required=False)
parser.add_argument('-o', '--outfile', help="Output data file for query result", required=False, default= "xml.output")
parser.add_argument('-id', '--ID', help="InvoiceID", required=False)


args = parser.parse_args()
# Split the provided queries into individual queries
Data = {}
for i, query in enumerate(queries):
    cursor.execute(query)
    Data[f'Query_{i+1}'] = cursor.fetchall()


for query_name, query in queries.items():
    cursor.execute(query)
    Data[query_name] = cursor.fetchall()
    print(Data[query_name])


if args.database:
    # Dynamically set the database name
    database_name = args.database

if args.ID:
    # Dynamically set InvoiceID parameter in SQL queries
    invoice_id = args.ID
    queries['Q0'] = queries['Q0'].replace("WHERE InvoiceDetail.InvoiceID = 2.", f"WHERE InvoiceDetail.InvoiceID = {invoice_id}.")
    queries['Q1'] = queries['Q1'].replace("WHERE Invoice.InvoiceID = 2", f"WHERE Invoice.InvoiceID = {invoice_id}")

if args.outfile:
    # Use the value of args.outfile to specify the output file path
    output_file_path = args.outfile
    # Write XML output to the specified file...

   
   