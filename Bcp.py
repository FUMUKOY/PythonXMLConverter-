import os
import xml.etree.ElementTree as ET
import xml.dom.minidom
from argparse import ArgumentParser
import pyodbc
import tempfile
import shutil
import os
import tkinter as tk
from tkinter import filedialog

sql_server_name = '127.0.0.1,1533'
database_name = 'STT'
username = 'sa'
password = '@DevelopmentPassword1'
Data = {}
parser = ArgumentParser()
args = parser.parse_args() 

manufacturer_xml = """<M>
    <CManufacturer>	<!-- This stays like that coz it inside the DataBase --> 
      <MANUF_ID>1</MANUF_ID>
      <MANUF_CODE>CC</MANUF_CODE>
      <MANUF_NAME>CellC</MANUF_NAME>
    </CManufacturer>
    <CManufacturer>
      <MANUF_ID>2</MANUF_ID>
      <MANUF_CODE>MT</MANUF_CODE>
      <MANUF_NAME>MTN</MANUF_NAME>
    </CManufacturer>
    <CManufacturer>
      <MANUF_ID>3</MANUF_ID>
      <MANUF_CODE>VO</MANUF_CODE>
      <MANUF_NAME>Vodacom</MANUF_NAME>
    </CManufacturer>
    <CManufacturer>
      <MANUF_ID>4</MANUF_ID>
      <MANUF_CODE>VI</MANUF_CODE>
      <MANUF_NAME>Virgin</MANUF_NAME>
    </CManufacturer>
    <CManufacturer>
      <MANUF_ID>5</MANUF_ID>
      <MANUF_CODE>TL</MANUF_CODE>
      <MANUF_NAME>Telkom</MANUF_NAME>
    </CManufacturer>
    <CManufacturer>
      <MANUF_ID>6</MANUF_ID>
      <MANUF_CODE>PH</MANUF_CODE>
      <MANUF_NAME>Mobile Phones</MANUF_NAME>
    </CManufacturer>
  </M>"""


connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={sql_server_name};DATABASE={database_name};UID={username};PWD={password}'
sql_server_connection = pyodbc.connect(connection_string)

cursor = sql_server_connection.cursor()

# Define SQL queries
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
    'Q2': """
        SELECT InvoiceDetail.InvoiceID as [INVOICE_NO],
                1 as INVOICE_ITEM, 
                RIGHT(Products.ProductCode, 2) AS PROD_ID, 
                InvoiceDetail.Qty as [SALES_QTY],
                InvoiceDetail.UnitIncVat as [SALES_PRICE],
                0 as [CUST_REBATE], 
                0 as [CUST_OGR], 
                'true' as SCANNED, 
                0 as COST_PRICE,
                0 as SUPP_ID,
                'false' as BUNDLED,
                'false' as PRELOAD_EXPORTED
        FROM InvoiceDetail
        INNER JOIN Products WITH (nolock) ON InvoiceDetail.ProductID = Products.ProductID
        WHERE InvoiceDetail.InvoiceID = 2
        for xml path ('D')
        """,
    'Q3': """
        SELECT RIGHT(Products.ProductCode, 2) AS PID,
                SimStockMaster.SimBarcode AS SNO,
                LEFT(BoxNumbers.Barcode, 3) AS PFIX,
                SUBSTRING(BoxNumbers.Barcode, 4, 9) AS BOX,
                '' AS 'MS'
        FROM InvoiceSimDetail
                INNER JOIN Customer WITH (nolock)
                INNER JOIN Invoice WITH (nolock) ON Customer.CustomerID = Invoice.CustomerID ON InvoiceSimDetail.InvoiceID = Invoice.InvoiceID
        INNER JOIN Products WITH (nolock)
        INNER JOIN BoxNumbers ON Products.ProductID = BoxNumbers.ProductID
        INNER JOIN SimStockMaster ON BoxNumbers.BoxID = SimStockMaster.BoxID ON InvoiceSimDetail.StockID = SimStockMaster.StockID
        WHERE Invoice.InvoiceID = 2
        for xml path ('CInvItemSerial')
        """
}

# Execute queries and store results in Data dictionary.
for query_name, query in queries.items():
    cursor.execute(query)
    Data[query_name] = cursor.fetchall()
    print(Data[query_name])


def store_dict_to_tempfile(Data):

    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        
        # Write the opening root element
        temp_file.write('<CInvoiceExport xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n')
        temp_file.write(manufacturer_xml)
        
        # Write the product data (P section)
        for query_value in Data['Q0']:
            temp_file.write(query_value[0])
        
        # Write the invoice data (H section)
        for query_value in Data['Q1']:
            temp_file.write(query_value[0])

        # Write the opening root1 element
        temp_file.write('<I>\n')

        # Write the opening root2 element
        temp_file.write('<CInvoiceItemExport>\n')

        # Write the detailed invoice items data (D section)
        for query_value in Data['Q2']:
            temp_file.write(query_value[0])
            
        temp_file.write('<S>\n')
        # Write the remaining data
        for query_value in Data['Q3']:
            temp_file.write(query_value[0])
        temp_file.write('</S>\n')

        # Write the closing root2 element
        temp_file.write('</CInvoiceItemExport>\n')
        
        # Write the closing root1 element
        temp_file.write('</I>\n')
        
        # Write the closing CInvoiceExport root element
        temp_file.write('</CInvoiceExport>\n')

        return temp_file.name
    


def save_file_dialog(file_content):
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    file_path = filedialog.asksaveasfilename(defaultextension=".xml", filetypes=[("XML files", "*.xml")])
    if file_path:
        with open(file_path, 'w') as file:
            file.write(file_content)
        print("File saved successfully at:", file_path)
    else:
        print("Saving cancelled.")


temp_file_path = store_dict_to_tempfile(Data)
with open(temp_file_path, 'r') as temp_file:
    temp_file_content = temp_file.read()


temp_file_path = store_dict_to_tempfile(Data)
print("Temporary file created:", temp_file_path)

save_file_dialog(temp_file_content)





            

           


