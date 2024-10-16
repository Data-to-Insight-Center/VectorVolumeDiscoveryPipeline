
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://k11:gdgBTA67MjLNuMRd@cybersec-smart-search-c.ss8xy.mongodb.net/?retryWrites=true&w=majority&appName=cybersec-smart-search-cluster"

def make_mongodb_connection():
    # Create a new client and connect to the server
    client = MongoClient(uri, server_api=ServerApi('1'))

    # Sending a ping to confirm a successful connection
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
        return client
    except Exception as e:
        print(e)