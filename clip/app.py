from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import numpy as np
from sqlalchemy import text
import torch

from embedding_models import load_embedding_model, generate_text_embeddings
from postgresql_models import create_postgresql_db_connection
from mongodb_models import make_mongodb_connection

Hugging_face_bearer_token = "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"

# FastAPI initialization
app = FastAPI()

# Pydantic model for user input
class QueryModel(BaseModel):
    query: str


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

# Fetch details from MongoDB using the image and textbook location paths
def fetch_from_mongo(image_path, textbook_path, client):
    db = client["cybersec_db"]
    pdf_collection = db["textbook_pdf_store"]
    image_collection = db["textbook_image_store"]

    image_data = image_collection.find_one({"path": image_path})
    textbook_data = pdf_collection.find_one({"path": textbook_path})

    return image_data, textbook_data

# Load CLIP model
# model params
model_params = {
    "device": "cuda" if torch.cuda.is_available() else "cpu", # Check if cuda is available
    "torch_dtype" : torch.float16
}
# Loading model
model, processor = load_embedding_model("CLIP", model_params)

# API endpoint for semantic search
@app.post("/search/")
async def search(query: QueryModel):
    try:
        # Generate text embeddings for the query
        query_embedding = generate_text_embeddings(query.query, model, processor)

        # Perform semantic search on PostgreSQL image embeddings
        search_results = get_relevant_entries(query_embedding)

        if not search_results:
            raise HTTPException(status_code=404, detail="No relevant results found")

        # Mongo DB connection
        client = make_mongodb_connection()

        # Prepare response
        response = []
        for result in search_results:
            text_book_name, volume, page_number, image_location_path, textbook_location_path, distance = result

            # Fetch image and textbook data from MongoDB
            image_data, textbook_data = fetch_from_mongo(image_location_path, textbook_location_path, client)

            response.append({
                "text_book_name": text_book_name,
                "volume": volume,
                "page_number": page_number,
                "image_location": image_data.get("content", "Image not found"),
                "textbook_location": textbook_data.get("content", "Textbook not found"),
                "distance": distance
            })

        return {"results": response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Close MongoDB connection
        client.close()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
