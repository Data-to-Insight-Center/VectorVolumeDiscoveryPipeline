from transformers import DonutProcessor, VisionEncoderDecoderModel, CLIPProcessor, CLIPModel
import torch
from PIL import Image
import os
from postgresql_models import ImageTextEmbeddings, create_postgresql_db_connection

# Function to convert embeddings to list (required for ARRAY(Float))
def embeddings_to_list(embeddings_tensor):
    return embeddings_tensor.squeeze().tolist()

def generate_text_embeddings(input_text, model, processor):
    text_tensor = processor(text=input_text, return_tensors="pt")
    with torch.no_grad():
        image_embeddings = model.get_text_features(**text_tensor)

    return embeddings_to_list(image_embeddings)

# Function to generate embeddings
def generate_embeddings(image_path, model, processor):
    image = Image.open(image_path)
    image_tensor = processor(images=image, return_tensors="pt")
    with torch.no_grad():
        image_embeddings = model.get_image_features(**image_tensor)

    return embeddings_to_list(image_embeddings)

def load_embedding_model(model_name, model_params):
    if model_name == "DONUT":
        # Load the Donut model and processor
        processor = DonutProcessor.from_pretrained("naver-clova-ix/donut-base")
        model = VisionEncoderDecoderModel.from_pretrained("naver-clova-ix/donut-base")

    elif model_name == "CLIP":
        model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32",
                                          device_map=model_params["device"], 
                                          torch_dtype=model_params["torch_dtype"]
                                          )     
        processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

    else:
        print("Incorrect model name provided.")

    return model, processor
    

# Main function to process images and upload to PostgreSQL
def process_images_and_upload(image_folder, model_name, session):
    # Example metadata
    meta_data = {
        "textbook_name": "Example Textbook",
        "volume": "Volume I",
        "published_year": 2024,
        "textbook_location_path": "dataset/oldgreeknaturest00farr.pdf"
    }
    # model params
    model_params = {
        "device": "cuda" if torch.cuda.is_available() else "cpu", # Check if cuda is available
        "torch_dtype" : torch.float16
    }
    # Loading model
    model, processor = load_embedding_model(model_name, model_params)

    # Iterate over all files in the image folder
    for filename in os.listdir(image_folder):
        if filename.endswith(".png") or filename.endswith(".jpg"):
            image_path = os.path.join(image_folder, filename)
            page_number = int(filename.split("_")[-1].split(".")[0])  # Assuming image name format contains page number
            
            # Generate image embeddings
            image_embeddings = generate_embeddings(image_path, model, processor)
            
            # Create an instance of ImageTextEmbeddings
            new_entry = ImageTextEmbeddings(
                text_book_name = meta_data["textbook_name"],
                volume = meta_data["volume"],
                published_year = meta_data["published_year"],
                page_number = page_number,
                image_location_path = image_path,
                textbook_location_path = meta_data["textbook_location_path"],
                image_embeddings = image_embeddings
            )
            
            # Add and commit the new entry to the PostgreSQL database
            session.add(new_entry)
            session.commit()
            print("Uploaded embeddings for page {} of {}".format(page_number, meta_data["textbook_name"]))


if __name__ == "__main__":
    session = create_postgresql_db_connection()
    # Folder containing the images
    image_folder = "dataset/sample_images"
    model_name = "CLIP"
    
    # Process images and upload to PostgreSQL
    process_images_and_upload(image_folder, model_name, session)

    # Close the session
    session.close()
