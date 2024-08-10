
from argparse import ArgumentParser
from dotenv import load_dotenv, find_dotenv
import os
import pyodbc
import logging
from DebugSetUp.SetupLogging import setup_logging

# Find the .env file automatically
dotenv_path = r'C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\170\Tools\Binn\.env'

# Load the .env file
load_dotenv(dotenv_path)

setup_logging()

config = {
    "db_host": os.getenv("DB_HOST"),
    "db_port" : os.getenv('DB_PORT'),
    "db_name": os.getenv("DB_NAME"),
    "db_user": os.getenv("DB_USER"),
    "db_password": os.getenv("DB_PASSWORD"),
} 

try:
    connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={config["db_host"]};PORT={config["db_port"]};DATABASE={config["db_name"]};UID={config["db_user"]};PWD={config["db_password"]}'
    sql_server_connection = pyodbc.connect(connection_string)
    logging.info("Successfull connection")
except  pyodbc.Error as e:
    logging.error(f"Failed to connect to the database: {e}")


Data = {}

manufacturer_xml = """<M>
    <CManufacturer>	
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
   
    
parser = ArgumentParser()
parser.add_argument('-o', '--outfile', help="Output data file for query result", required=False, default='C:\\Users\\enochn\\Documents\\Doc.xml')
parser.add_argument('-id', '--ID', type=int, help="InvoiceID", required=False, default=None)
args = parser.parse_args()

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
        WHERE InvoiceDetail.InvoiceID = {ID}  
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
        WHERE Invoice.InvoiceID = {ID}  
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
        WHERE InvoiceDetail.InvoiceID = {ID}  
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
        WHERE Invoice.InvoiceID = {ID}  
        for xml path ('CInvItemSerial')
        """
}

cursor = sql_server_connection.cursor()
# Execute queries and store results in Data dictionary.
for query_name, query in queries.items():
    try:
      cursor.execute(query.format(ID=args.ID))
      Data[query_name] = cursor.fetchall()
    except pyodbc.Error as e:
        logging.error(f"Error executing query '{query_name}': {e}")



def store_dict_to_tempfile(Data):

    # with tempfile.NamedTemporaryFile(mode='w', delete=False) as file :
    with open(args.outfile ,mode="w") as file :
        
        # Write the opening root element
        file .write('<CInvoiceExport xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n')
        file .write(manufacturer_xml)
        
        # Write the product data (P section)
        for query_value in Data['Q0']:
            file .write(query_value[0])
        
        # Write the invoice data (H section)
        for query_value in Data['Q1']:
            file .write(query_value[0])

        # Write the opening root1 element
        file .write('<I>\n')

        # Write the opening root2 element
        file .write('<CInvoiceItemExport>\n')

        # Write the detailed invoice items data (D section)
        for query_value in Data['Q2']:
            file .write(query_value[0])
            
        file .write('<S>\n')
        # Write the remaining data
        for query_value in Data['Q3']:
            file .write(query_value[0])
        file .write('</S>\n')

        # Write the closing root2 element
        file .write('</CInvoiceItemExport>\n')
        
        # Write the closing root1 element
        file .write('</I>\n')
        
        # Write the closing CInvoiceExport root element
        file .write('</CInvoiceExport>\n')

        return file.name
    
try:                 
  file_path = store_dict_to_tempfile(Data)
  logging.info(f"Data successfully exported to {file_path}")
except Exception as e:
    logging.error(f"An error occurred: {e}")













    










            

           




