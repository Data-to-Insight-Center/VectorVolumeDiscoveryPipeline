import base64
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from PIL import Image, UnidentifiedImageError
from io import BytesIO
import torch
from colpali_engine.models import ColPali, ColPaliProcessor
from huggingface_hub import HfFolder

# Hugging Face token login function
def login_to_hf(token):
    HfFolder.save_token(token)

# Request body schema
class QueryEmbeddingRequest(BaseModel):
    user_query: str

# Initialize the FastAPI app
app = FastAPI()

# Load the model and processor when the app starts
@app.on_event("startup")
async def load_model():
    global model, processor

    # model_id = "google/paligemma-3b-mix-224"
    model_id = "vidore/colpali-v1.2"
    device = "cuda:0"
    dtype = torch.bfloat16
    
    try:
        model = ColPali.from_pretrained(
            model_id,
            torch_dtype=dtype,
            device_map=device,
        ).eval()

        processor = ColPaliProcessor.from_pretrained(model_id)

        return model, processor
    except Exception as e:
        raise RuntimeError(f"Error loading model or processor: {str(e)}")
        
# Endpoint to fetch text embeddings
@app.post("/get_text_embedding")
async def text_embeddings(request: QueryEmbeddingRequest):
    try:
        # Process and encode the text query
        with torch.no_grad():
            batch_query = processor.process_queries([request.query_text]).to(
                model.device
            )
            query_embedding = model(**batch_query)

        # Convert the query embedding to a list of vectors
        multivector_query = query_embedding[0].cpu().float().numpy().tolist()

        return multivector_query
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during text embedding: {str(e)}")  

# Example for Hugging Face token login
HF_TOKEN = "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"
login_to_hf(HF_TOKEN)
