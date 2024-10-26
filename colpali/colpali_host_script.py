import torch
import os
import uuid
import shutil
from io import BytesIO
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from PIL import Image
from colpali_engine.models import ColPali, ColPaliProcessor
from huggingface_hub import HfFolder
from pathlib import Path

from helper_functions import convert_pdf_to_images, extract_images_and_names_from_zip, load_images, encode_image
from qdrant_model import create_qdrant_collection, delete_qdrant_collection, list_qdrant_collections, index_images_to_qdrant, search_qdrant

# Define a directory to save files
BASE_UPLOAD_DIRECTORY = "./uploaded_files"

# Ensure the directory exists
Path(BASE_UPLOAD_DIRECTORY).mkdir(parents=True, exist_ok=True)

# Hugging Face token login function
def login_to_hf(token):
    HfFolder.save_token(token)


class QueryEmbeddingRequest(BaseModel):
    user_query: str

class QdrantCollectionCreate(BaseModel):
    collection_name: str
    vector_size: int
    indexing_threshold: int

class QdrantCollectionDelete(BaseModel):
    collection_name: str

# Initialize the FastAPI app
app = FastAPI()

# Load the model and processor when the app starts
@app.on_event("startup")
async def load_model():
    global colpali_model, colpali_processor

    model_id = "vidore/colpali-v1.2"
    device = "cuda:0"
    dtype = torch.float32
    
    try:
        colpali_model = ColPali.from_pretrained(
            model_id,
            torch_dtype=dtype,
            device_map=device,
        ).eval()

        colpali_processor = ColPaliProcessor.from_pretrained(model_id)

    except Exception as e:
        raise RuntimeError(f"Error loading model or processor: {str(e)}")
    

# Helper function to create unique folder name based on UUID
def create_hash_folder():
    unique_id = uuid.uuid4().hex
    folder_path = os.path.join(BASE_UPLOAD_DIRECTORY, unique_id)
    Path(folder_path).mkdir(parents=True, exist_ok=True)
    images_folder = os.path.join(folder_path, "images_to_process")
    Path(images_folder).mkdir(parents=True, exist_ok=True)
    return folder_path, images_folder

# Endpoint to create collection in qdrant
@app.post("/create_qdrant_collection")
async def qdrant_create_collection(request: QdrantCollectionCreate):
    return create_qdrant_collection(request.collection_name, request.vector_size, request.indexing_threshold)

# Endpoint to delete collection in qdrant
@app.post("/delete_qdrant_collection")
async def qdrant_delete_collection(request: QdrantCollectionDelete):
    return delete_qdrant_collection(request.collection_name)

# Endpoint to delete collection in qdrant
@app.post("/get_qdrant_collections")
async def qdrant_list_collections():
    return list_qdrant_collections()


@app.post("/document_embed")
async def embed_index_documents(file: UploadFile = File(...)):
    try:
        global colpali_model, colpali_processor
        if colpali_model is None or colpali_processor is None:
            raise HTTPException(status_code=500, detail="Model is not loaded")
        
        # Create a unique hash-based folder
        hash_folder, images_folder = create_hash_folder()
        filename = file.filename

        # Save the uploaded file in the hash folder
        file_location = os.path.join(hash_folder, filename)
        with open(file_location, "wb") as f:
            content = await file.read()
            f.write(content)

        if filename.endswith(".pdf"):
            images = convert_pdf_to_images(file_location)
            pdf_filename = filename.rsplit(".", 1)[0]
            for idx, image in enumerate(images):
                image_path = os.path.join(images_folder, f"{pdf_filename}_page_{idx + 1}.png")
                image.save(image_path)
        
        elif filename.endswith(".zip"):
            images, image_names = extract_images_and_names_from_zip(file_location)
            for image, name in zip(images, image_names):
                image_path = os.path.join(images_folder, name)
                image.save(image_path)
        
        elif filename.endswith(('.png', '.jpg', '.jpeg')):            
            image_path = os.path.join(images_folder, filename)
            with open(image_path, "wb") as f:
                f.write(content)
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        
        image_files = [os.path.join(images_folder, img) for img in os.listdir(images_folder)]
        print("Input file processed. Calling Embedding function Now!")
        print("Number of images:{}".format(len(image_files)))
        index_images_to_qdrant(image_files, colpali_model, colpali_processor, batch_size=10, collection_name=sample_collection_name)
        return {"status": "Document embedded successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error embedding documents: {str(e)}")
    
    # finally:
    #     if os.path.exists(hash_folder):
    #         shutil.rmtree(hash_folder)



# Endpoint to fetch text embeddings
@app.post("/document_retrieval")
async def get_relevant_documents(request: QueryEmbeddingRequest):
    try:
        # Process and encode the text query
        with torch.no_grad():
            batch_query = colpali_processor.process_queries([request.user_query]).to(
                colpali_model.device
            )
            query_embedding = colpali_model(**batch_query)

        # Convert the query embedding to a list of vectors
        multivector_query = query_embedding[0].cpu().float().numpy().tolist()

        search_result = search_qdrant(sample_collection_name, multivector_query, 3)
    
        if not search_result.points:
            raise HTTPException(status_code=404, detail="No matching images found")
        
        row_image_paths = [r.payload["image"] for r in search_result.points]

        return FileResponse(row_image_paths[0])

        

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during text embedding: {str(e)}")  

# hf_token = os.getenv("HF_TOKEN")
hf_token = "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"
# sample_collection_name = os.getenv("QDRANT_COLLECTION_NAME")
sample_collection_name = "textbook_image_embeddings_v1"
embed_collection_name = "cybersec_image_embeddings_v1"
login_to_hf(hf_token)
