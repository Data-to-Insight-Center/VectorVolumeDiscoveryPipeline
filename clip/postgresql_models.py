from sqlalchemy import create_engine, Column, Integer, String, Text, Float
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
    image_embeddings = Column(ARRAY(512), nullable=False)
    text_embeddings = Column(ARRAY(512))


def create_postgresql_db_connection():
    try:
        engine = create_engine(DATABASE_URL)

        # Set up session maker
        Session = sessionmaker(bind=engine)
        session = Session()

        print("postgresql database connection established!")
        return session
    
    except Exception as err:
        print("PostgreSQL connection failed due to error: {}".format(str(err)))

db_conn = create_postgresql_db_connection()
