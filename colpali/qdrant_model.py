from qdrant_client import QdrantClient, models
import stamina
from tqdm import tqdm
import os
import torch

from helper_functions import image_to_base64, load_images, encode_image

# qdrant_url = os.getenv("QDRANT_ACCESS_URL")
# qdrant_api = os.getenv("QDRANT_API_KEY")

qdrant_url = "https://5655a152-5dfa-4807-9700-f8976170b86f.europe-west3-0.gcp.cloud.qdrant.io:6333"
qdrant_api = "ehg5LrM1GG9BLJ9ShL6hBWH5IGxsD7RJHXNogiJQfiYD-5gONEN5CQ"


def create_qdrant_client():
    qdrant_client = QdrantClient(
        url=qdrant_url,
        api_key=qdrant_api,
    )
    return qdrant_client


def delete_qdrant_collection(collection_name):
   # qdrant client connect
   qdrant_client = create_qdrant_client()
   return qdrant_client.delete_collection(collection_name=collection_name)


def list_qdrant_collections():
    # qdrant client connect
    qdrant_client = create_qdrant_client()
    
    return qdrant_client.get_collections()


def create_qdrant_collection(collection_name, vector_size, indexing_threshold):
    try:
        # qdrant client connect
        qdrant_client = create_qdrant_client()


        qdrant_client.create_collection(
            collection_name=collection_name,
            on_disk_payload=True,
            optimizers_config=models.OptimizersConfigDiff(
                indexing_threshold=indexing_threshold
            ),
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE,
                multivector_config=models.MultiVectorConfig(
                    comparator=models.MultiVectorComparator.MAX_SIM
                ),
                quantization_config=models.ScalarQuantization(
                    scalar=models.ScalarQuantizationConfig(
                        type=models.ScalarType.INT8,
                        quantile=0.99,
                        always_ram=True,
                    ),
                ),
            ),
        )

        return True
    except Exception as e:
        print("Error creating collection in qdrant. {}".format(str(e)))
        raise False
    

@stamina.retry(on=Exception, attempts=3)
def upsert_to_qdrant(points, collection_name, qdrant_client):
    try:
        qdrant_client.upsert(
            collection_name=collection_name,
            points=points,
            wait=False,
        )
        return True
    except Exception as e:
        print(f"Error during upsert: {e}")
        return False


def index_images_to_qdrant(images_paths, model, processor, batch_size, collection_name, starting_id=0):
    global_id = starting_id

    # qdrant client connect
    qdrant_client = create_qdrant_client()

    with tqdm(total=len(images_paths), desc="Indexing Progress") as pbar:
        for i in range(0, len(images_paths), batch_size):
            print("Processing batch")

            batch = images_paths[i : i + batch_size]
            batch_images = load_images(batch)

            with torch.no_grad():
                batch_images_tensor = processor.process_images(batch_images).to(model.device)
                image_embeddings = model(**batch_images_tensor)

            # prepare points for Qdrant
            points = []
            print("Creating points")
            for j, embedding in enumerate(image_embeddings):
                multivector = embedding.cpu().float().numpy().tolist()

                # convert the image to base64 for storage in Qdrant
                # image_base64 = image_to_base64(batch_images[j])
                # image_base64 = encode_image(batch[j])

                points.append(
                    models.PointStruct(
                        id=global_id,
                        vector=multivector,
                        payload={
                            "image": batch[j]
                        },
                    )
                )

                global_id += 1

            try:
                upsert_to_qdrant(points, collection_name, qdrant_client)
                print("Upsert done for batch")
            except Exception as e:
                print(f"Error during upsert: {e}")
                continue
            pbar.update(batch_size)
    print("Indexing complete!")


def search_qdrant(collection_name, query_embedding, top_k=3):
    try:
        # qdrant client connect
        qdrant_client = create_qdrant_client()

        # Perform the query on Qdrant, searching for the most similar points (multivector query)
        search_result = qdrant_client.query_points(
            collection_name=collection_name, 
            query=query_embedding, 
            with_payload=["image"],
            limit=top_k
        )
        
        return search_result
    
    except Exception as e:
        raise RuntimeError(f"Error during Qdrant search: {str(e)}")

