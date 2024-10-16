from typing import List, Dict
import numpy as np
from sqlalchemy import text
import torch
import json

from embedding_models import load_embedding_model, generate_text_embeddings
from postgresql_models import create_postgresql_db_connection
from mongodb_models import make_mongodb_connection

Hugging_face_bearer_token = "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"

# Function to find top relevant trials
def get_relevant_search_entries(query_embedding: List[float], top_k: int = 3) -> List[Dict]:
    try:
        # SQLAlchemy session
        session = create_postgresql_db_connection()

        # Convert query_embedding to a format suitable for SQLAlchemy
        embedding_str = ",".join(map(str, query_embedding))
        
        # Define the SQL query to find similar embeddings using pgvector
        sql = text(f"""
        SELECT text_book_name, volume, page_number, image_location_path, textbook_location_path,
        1 - (image_embeddings <=> '[{embedding_str}]') AS similarity
        FROM image_text_embeddings
        ORDER BY image_embeddings <=> '[{embedding_str}]'
        LIMIT 3;
        """)
        
        results = session.execute(sql).fetchall()

        return results
    except Exception as e:
        raise Exception("Failed to fetch semantic search results from db. Error: {}".format(str(e)))
    


# Function to perform semantic search on PostgreSQL image embeddings
def get_relevant_entries(query_embedding):
    query_embedding = np.array(query_embedding, dtype=np.float32)

    # SQLAlchemy session
    session = create_postgresql_db_connection()

    try:
        # SQL query for semantic search using <-> operator (L2 distance)
        query = """
        SELECT text_book_name, volume, page_number, image_location_path, textbook_location_path,
               (image_embeddings <=> :query_embedding) AS distance
        FROM image_text_embeddings
        ORDER BY distance ASC
        LIMIT 10;
        """

        result = session.execute(text(query), {"query_embedding": list(query_embedding)})
        search_results = result.fetchall()

    except Exception as e:
        session.rollback()
        raise e

    finally:
        session.close()

    return search_results

# # Fetch details from MongoDB using the image and textbook location paths
# def fetch_from_mongo(image_path, textbook_path, client):
#     db = client["cybersec_db"]
#     pdf_collection = db["textbook_pdf_store"]
#     image_collection = db["textbook_image_store"]

#     image_data = image_collection.find_one({"path": image_path})
#     textbook_data = pdf_collection.find_one({"path": textbook_path})

#     return image_data, textbook_data

# Load the JSON data from the file
with open('text_embeddings.json', 'r') as f:
    text_embed_data = json.load(f)
# Load CLIP model
# model params
def run_semantic_search(text_embed_data):
    
    # get text embeddings
    query_embedding = text_embed_data["text_embeddings"]

    # Perform semantic search on PostgreSQL image embeddings
    search_results = get_relevant_search_entries(query_embedding)

    if not search_results:
        raise print("No relevant results found")
    
    results_list = []
    for row in search_results:
        result_dict = {
            "text_book_name": row.text_book_name,
            "volume": row.volume,
            "page_number": row.page_number,
            "image_location_path": row.image_location_path,
            "textbook_location_path": row.textbook_location_path,
            "similarity": row.similarity
        }
        results_list.append(result_dict)

    return results_list

    
results = run_semantic_search(text_embed_data)
print(results)