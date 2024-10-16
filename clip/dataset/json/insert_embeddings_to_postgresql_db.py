import json
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, Table, MetaData, Double
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLAlchemy Base and ImageTextEmbeddings class definition
Base = declarative_base()

# Database configuration
DATABASE_URL = "postgresql+psycopg2://postgres:mz7zdz123@localhost:5432/cybersec_vector_db"

class ImageTextEmbeddings(Base):
    __tablename__ = 'image_text_embeddings'
    
    text_book_id = Column(Integer, primary_key=True, autoincrement=True)
    text_book_name = Column(String(255), nullable=False)
    volume = Column(Text, nullable=False)
    published_year = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=False)
    image_location_path = Column(String(255), nullable=False)
    textbook_location_path = Column(String(255), nullable=False)
    image_embeddings = Column(ARRAY(Double), nullable=False)
    text_embeddings = Column(ARRAY(Double))

# Create a SQLAlchemy engine and metadata object
engine = create_engine(DATABASE_URL)

# Create a session
Session = sessionmaker(bind=engine)
session = Session()

# Load the JSON data from the file
with open('image_embeddings.json', 'r') as f:
    data_list = json.load(f)

# Insert entries one by one (row by row)
def insert_embeddings(data_list):
    session.bulk_insert_mappings(ImageTextEmbeddings, data_list)
    session.commit()
    print("Inserted entries to postgresql db")

insert_embeddings(data_list)
# print(len(data_list[0]["image_embeddings"]))