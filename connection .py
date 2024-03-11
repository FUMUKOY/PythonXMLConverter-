
import argparse
from argparse import ArgumentParser
# Define an ArgumentParser object


parser = ArgumentParser()

parser = argparse.ArgumentParser(description='Generate XML file from SQL Server data.')
parser.add_argument('--server', help='SQL Server name/IP', default='127.0.0.1,1533')
parser.add_argument('--database', help='Database name', default='STT')
parser.add_argument('--username', help='Username', default='sa')
parser.add_argument('--password', help='Password', default='@DevelopmentPassword1')

# Parse the command-line arguments
args = parser.parse_args()

# Access the values provided by the user
sql_server_name = args.server
database_name = args.database
username = args.username
password = args.password

# Your existing code continues from here...
