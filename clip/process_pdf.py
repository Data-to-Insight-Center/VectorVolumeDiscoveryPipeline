import os
from pdf2image import convert_from_path
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson.binary import Binary

from mongodb_models import make_mongodb_connection

# If Poppler is in PATH, you can omit this argument
# Otherwise, specify the path to the bin folder
poppler_path = r'C:\Users\manik\Desktop\CIB_LLM_Research\Git_repository\InsightX\poppler-24.07.0\Library\bin'

# Function to upload PDF to MongoDB
def upload_pdf_to_mongo(pdf_path, pdf_collection):
    pdf_name = os.path.basename(pdf_path)
    with open(pdf_path, "rb") as f:
        pdf_data = f.read()
    
    # Insert PDF as binary
    pdf_doc = {
        "pdf_name": pdf_name,
        "pdf_file": Binary(pdf_data)
    }

    pdf_collection.insert_one(pdf_doc)
    print(f"Uploaded PDF '{pdf_name}' to MongoDB.")

# Function to convert PDF to images and upload images to MongoDB
def process_and_upload_images(pdf_path, output_folder, image_collection):
    pdf_name = os.path.basename(pdf_path)
    
    # Convert PDF to images using pdf2image
    images = convert_from_path(pdf_path, dpi=300, poppler_path=poppler_path)
    
    for page_num, image in enumerate(images, start=1):
        image_path = os.path.join(output_folder, f"{pdf_name}_page_{page_num}.png")
        # Save the image as PNG
        image.save(image_path, "PNG")

        print("Image saved: {}".format(image_path))

        # # Open and read the image
        # with open(image_path, "rb") as img_file:
        #     image_binary = Binary(img_file.read())

        # # Insert image as binary in MongoDB
        # image_doc = {
        #     "pdf_name": pdf_name,
        #     "page_number": page_num,
        #     "image_file": image_binary,
        #     "image_path": image_path
        # }
        # image_collection.insert_one(image_doc)
        # print(f"Uploaded image for page {page_num} of '{pdf_name}' to MongoDB.")

# Main processing function
def process_pdfs_in_folder(pdf_folder, output_folder, client):
    # Access the desired database and collections
    db = client["cybersec_db"]
    pdf_collection = db["textbook_pdf_store"]
    image_collection = db["textbook_image_store"]

    for pdf_file in os.listdir(pdf_folder):
        if pdf_file.endswith(".pdf"):
            pdf_path = os.path.join(pdf_folder, pdf_file)
    
            # Upload the PDF to MongoDB
            # upload_pdf_to_mongo(pdf_path, pdf_collection)
            print("Processing pdf file: {}".format(pdf_path))
            # Process and upload images for each page of the PDF
            process_and_upload_images(pdf_path, output_folder, image_collection)

if __name__ == "__main__":
    pdf_folder = "dataset/cybersec_pdf_data"
    output_folder = "dataset/dataset_images"

    # Mongo DB connection
    client = make_mongodb_connection()

    # Ensure the output folder exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Process all PDFs in the given folder
    process_pdfs_in_folder(pdf_folder, output_folder, client)

    # Close MongoDB connection
    client.close()
