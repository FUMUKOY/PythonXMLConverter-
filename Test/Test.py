import os
import pyodbc
import logging
from argparse import ArgumentParser
from dotenv import load_dotenv
from datetime import datetime

# Find the .env file automatically
dotenv_path = r'C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\170\Tools\Binn\.env'

# Load the .env file
load_dotenv(dotenv_path)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load database configuration from environment variables
config = {
    "db_host": os.getenv("DB_HOST"),
    "db_port": os.getenv("DB_PORT"),
    "db_name": os.getenv("DB_NAME"),
    "db_user": os.getenv("DB_USER"),
    "db_password": os.getenv("DB_PASSWORD"),
}

# Establish a database connection
try:
    connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={config["db_host"]};PORT={config["db_port"]};DATABASE={config["db_name"]};UID={config["db_user"]};PWD={config["db_password"]}'
    sql_server_connection = pyodbc.connect(connection_string)
    logger.info("Successfully connected to the database")
except pyodbc.Error as e:
    logger.error(f"Failed to connect to the database: {e}")
    exit(1)

# Argument parser setup
parser = ArgumentParser()
parser.add_argument('-o', '--outfile', help="Output data file for query result", required=False)
parser.add_argument('-id', '--ID', type=int, help="InvoiceID", required=False, default=1)  # Set default ID to 1
args = parser.parse_args()

# Function to fetch default file name from the database
def fetch_default_file_name(invoice_id):
    query = """
        SELECT Company.CompanyName + '_' + Invoice.InvoiceNumber + '.xml' AS FileName
        FROM Invoice with(nolock)
        INNER JOIN Company with (nolock)ON Invoice.CompanyID = Company.CompanyID
        WHERE Invoice.InvoiceID = ?
    """
    try:
        cursor = sql_server_connection.cursor()
        cursor.execute(query, (invoice_id,))
        result = cursor.fetchone()
        return result.FileName if result else None
    except pyodbc.Error as e:
        logger.error(f"Failed to fetch default file name: {e}")
        return None

# Generate a default output file name based on a SQL query if not provided
if not args.outfile:
    default_file_name = fetch_default_file_name(args.ID)
    if default_file_name:
        args.outfile = os.path.join('C:\\Users\\enochn\\Documents', default_file_name)
    else:
        # Fallback to current date and time if query fails
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        args.outfile = f'C:\\Users\\enochn\\Documents\\Doc_{current_time}.xml'

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
        FOR XML PATH ('CProduct'), ROOT ('P')
        """,
    'Q1': """
        SELECT Invoice.InvoiceID AS [INVOICE_NO], 
                Invoice.InvoiceNumber AS [REFERENCE], 
                1 AS [WAREHOUSE_ID],
                38248 AS [CUST_ID], 
                Customer.CustomerCode AS [CUST_CODE], 
                Invoice.CreateDate AS [INVOICE_DATE], 
                11 AS [SALES_PERSON_ID], 
                'true' AS [POSTED]
        FROM Invoice
        INNER JOIN Customer WITH (nolock) ON Invoice.CustomerID = Customer.CustomerID
        WHERE Invoice.InvoiceID = {ID}  
        FOR XML PATH ('H')
        """,
    'Q2': """
        SELECT InvoiceDetail.InvoiceID AS [INVOICE_NO],
                1 AS INVOICE_ITEM, 
                RIGHT(Products.ProductCode, 2) AS PROD_ID, 
                InvoiceDetail.Qty AS [SALES_QTY],
                InvoiceDetail.UnitIncVat AS [SALES_PRICE],
                0 AS [CUST_REBATE], 
                0 AS [CUST_OGR], 
                'true' AS SCANNED, 
                0 AS COST_PRICE,
                0 AS SUPP_ID,
                'false' AS BUNDLED,
                'false' AS PRELOAD_EXPORTED
        FROM InvoiceDetail
        INNER JOIN Products WITH (nolock) ON InvoiceDetail.ProductID = Products.ProductID
        WHERE InvoiceDetail.InvoiceID = {ID}  
        FOR XML PATH ('D')
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
        FOR XML PATH ('CInvItemSerial')
        """
}

# Initialize Data dictionary
Data = {}

# Execute queries and store results in Data dictionary
cursor = sql_server_connection.cursor()
for query_name, query in queries.items():
    try:
        cursor.execute(query.format(ID=args.ID))
        Data[query_name] = cursor.fetchall()
        logger.info(f"Query '{query_name}' executed successfully")
    except pyodbc.Error as e:
        logger.error(f"Error executing query '{query_name}': {e}")

# Manufacturer XML string
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

# Function to store data to XML file
def store_dict_to_tempfile(Data, output_file):
    with open(output_file, mode="w") as file:
        file.write('<CInvoiceExport xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n')
        file.write(manufacturer_xml)

        # Write the product data (P section)
        for query_value in Data['Q0']:
            file.write(query_value[0])

        # Write the invoice data (H section)
        for query_value in Data['Q1']:
            file.write(query_value[0])

        # Write the opening root1 element
        file.write('<I>\n')

        # Write the opening root2 element
        file.write('<CInvoiceItemExport>\n')

        # Write the detailed invoice items data (D section)
        for query_value in Data['Q2']:
            file.write(query_value[0])
            
        file.write('<S>\n')
        # Write the remaining data
        for query_value in Data['Q3']:
            file.write(query_value[0])
        file.write('</S>\n')

        # Write the closing root2 element
        file.write('</CInvoiceItemExport>\n')
        
        # Write the closing root1 element
        file.write('</I>\n')
        
        # Write the closing CInvoiceExport root element
        file.write('</CInvoiceExport>\n')

        return file.name

# Store the results to an XML file using the specified output file path
try:
    file_path = store_dict_to_tempfile(Data, args.outfile)
    logger.info(f"Data successfully exported to {file_path}")
except Exception as e:
    logger.error(f"An error occurred: {e}")
