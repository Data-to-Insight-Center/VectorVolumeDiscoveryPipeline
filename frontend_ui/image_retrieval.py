import streamlit as st
import requests
import json
from PIL import Image
from io import BytesIO
from database import init_db, add_user, verify_user
from streamlit_lottie import st_lottie
from concurrent.futures import ThreadPoolExecutor
from anthropic_client   import AnthropicClient
import os

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

st.set_page_config(
        page_title="Document Search System",
        page_icon="🔍",
        layout="wide"
    )

init_db()

# Backend API URL
BACKEND_URL = "http://backend:8000"

def load_lottiefile(filepath: str):
    with open(filepath, "r") as file:
        return json.load(file)

lottie_animation = load_lottiefile("Animation - 1731620804494.json")


st.markdown("""
<style>
    .login-container {
        max-width: 400px;
        padding: 20px;
        margin: auto;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        background-color: white;
    }
    .stTextInput > div > div > input {
        border-radius: 5px;
    }
    .stButton > button {
        width: 100%;
        border-radius: 5px;
        margin-top: 10px;
    }
    .main-header {
        text-align: center;
        padding: 20px;
    }
</style>
""", unsafe_allow_html=True)

def login_page():
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st_lottie(lottie_animation, height=400, key="login_animation")
    
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>Login</h2>", unsafe_allow_html=True)
        
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("Login", key="login_btn"):
                if verify_user(username, password):
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        
        with col_btn2:
            if st.button("Register", key="register_btn"):
                st.session_state['show_register'] = True
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

def register_page():
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st_lottie(lottie_animation, height=400, key="register_animation")
    
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>Register</h2>", unsafe_allow_html=True)
        
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("Register", key="register_submit"):
                if password != confirm_password:
                    st.error("Passwords do not match")
                elif not username or not email or not password:
                    st.error("Please fill all fields")
                else:
                    if add_user(username, password, email):
                        st.success("Registration successful! Please login.")
                        st.session_state['show_register'] = False
                        st.rerun()
                    else:
                        st.error("Username or email already exists")
        
        with col_btn2:
            if st.button("Back to Login"):
                st.session_state['show_register'] = False
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

def main():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    
    if 'show_register' not in st.session_state:
        st.session_state['show_register'] = False
    
    if not st.session_state['logged_in']:
        st.markdown("<h1 class='main-header'>Document Search and Retrieval System</h1>", unsafe_allow_html=True)
        if st.session_state['show_register']:
            register_page()
        else:
            login_page()
        return

    st.title("Document Search and Retrieval System")
    st.sidebar.title("Navigation")
    
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()
    
    st.sidebar.write(f"Welcome, {st.session_state['username']}!")
    
    page = st.sidebar.radio("Choose a page", ["Image Search", "Qdrant Collections", "Index Images"])

    # if page == "Document Upload":
    #     document_upload_page()
    if page == "Image Search":
        image_search_page()
    elif page == "Qdrant Collections":
        qdrant_collections_page()
    elif page == "Index Images":
        document_upload_page()

# Images embed and indexing to Qdrant vector store
def document_upload_page():
    st.header("Document Upload")
    st.write("Upload PDF, ZIP, or image files to index them in the database.")
    
    uploaded_file = st.file_uploader(
        "Choose a file", 
        type=['pdf', 'zip', 'png', 'jpg', 'jpeg'],
        help="Supported formats: PDF, ZIP (containing images), PNG, JPG, JPEG"
    )
    
    if uploaded_file is not None:
        if st.button("Process and Index Document"):
            with st.spinner("Processing and indexing document..."):
                try:
                    files = {"file": uploaded_file}
                    response = requests.post(f"{BACKEND_URL}/document_embed", files=files)
                    
                    if response.status_code == 200:
                        st.success("Document successfully processed and indexed!")
                    else:
                        st.error(f"Error: {response.json()['detail']}")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

# Image Retrieval
def image_search_page():
    st.header("Image Search")
    st.write("Search for relevant images using text queries.")
    
    query = st.text_input("Enter your search query")
    
    if st.button("Search"):
        if query:
            with st.spinner("Searching for relevant images..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/document_retrieval",
                        json={"user_query": query}
                    )
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        image_paths = response_data.get('retrieved_image_paths', [])
                        scores = response_data.get('scores', [])

                        cols = st.columns(3)
                        
                        for idx, (img_path, score) in enumerate(zip(image_paths[:3], scores[:3])):
                            try:
                                with cols[idx]:
                                    image = Image.open(img_path)
                                    
                                    st.image(image, 
                                           caption=f"Similarity Score: {score:.2f}",
                                           use_container_width=True)
                                    
                                    # Add download button for each image
                                    # with open(img_path, "rb") as file:
                                    #     st.download_button(
                                    #         label="Download Image",
                                    #         data=file,
                                    #         file_name=img_path.split('/')[-1],
                                    #         mime="image/jpeg"
                                    #     )

                            except Exception as e:
                                st.error(f"Error loading image {img_path}: {str(e)}")

                         # Start async LLM response generation
                        if image_paths:
                            try:
                                # Create a placeholder for the response
                                llm_response_placeholder = st.empty()
                                llm_response_placeholder.info("Generating response...")

                                # Initialize Anthropic client
                                client = AnthropicClient(api_key=ANTHROPIC_API_KEY)

                                # Prepare the prompt
                                prompt = f"""You are an expert in interpreting and understanding the content in the images. Using the image as a reference, answer then question. Be very straight to the point and do not include additional information. Here is the question: {query}"""

                                def get_llm_response():
                                    return client.send_message(
                                        content=prompt,
                                        image_paths=image_paths,
                                        max_tokens=1000,
                                        temperature=0
                                    )

                                # Use ThreadPoolExecutor for non-blocking execution
                                with ThreadPoolExecutor() as executor:
                                    future = executor.submit(get_llm_response)
                                    
                                    # Get the response
                                    response = future.result()
                                    
                                    if response['status']:
                                        # Update the placeholder with the response
                                        llm_response_placeholder.markdown(
                                            f"""
                                            **Response:**
                                            {response['result']}
                                            """
                                        )
                                    else:
                                        llm_response_placeholder.error(
                                            f"Failed to generate response: {response.get('error', 'Unknown error')}"
                                        )

                            except Exception as e:
                                llm_response_placeholder.error(f"An error occurred: {str(e)}")

                        else:
                            st.warning("No matching images found.")
                    else:
                        st.error(f"Error: {response.json().get('detail', 'Unknown error occurred')}")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
        else:
            st.warning("Please enter a search query")

    # with st.expander("Search Tips"):
    #     st.write("""
    #     - Enter descriptive keywords for better results
    #     - The similarity score indicates how well the image matches your query
    #     """)

def qdrant_collections_page():
    st.header("Qdrant Collections Management")
    
    st.subheader("Create New Collection")
    col1, col2, col3 = st.columns(3)
    with col1:
        collection_name = st.text_input("Collection Name")
    with col2:
        vector_size = st.number_input("Vector Size", min_value=1, value=768)
    with col3:
        indexing_threshold = st.number_input("Indexing Threshold", min_value=1, value=20000)
    
    if st.button("Create Collection"):
        try:
            response = requests.post(
                f"{BACKEND_URL}/create_qdrant_collection",
                json={
                    "collection_name": collection_name,
                    "vector_size": vector_size,
                    "indexing_threshold": indexing_threshold
                }
            )
            if response.status_code == 200:
                st.success("Collection created successfully!")
            else:
                st.error(f"Error: {response.json()['detail']}")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

    st.subheader("Existing Collections")
    if st.button("Refresh Collections List"):
        try:
            response = requests.post(f"{BACKEND_URL}/get_qdrant_collections")
            if response.status_code == 200:
                collections = response.json()
                print(collections)
                if collections:
                    for collection in collections['collections']:
                        st.write(f"- {collection['name']}")
                else:
                    st.info("No collections found")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
    

    st.subheader("Delete Collection")
    collection_to_delete = st.text_input("Enter collection name to delete")
    if st.button("Delete Collection"):
        if collection_to_delete:
            try:
                response = requests.post(
                    f"{BACKEND_URL}/delete_qdrant_collection",
                    json={"collection_name": collection_to_delete}
                )
                if response.status_code == 200:
                    st.success(f"Collection '{collection_to_delete}' deleted successfully!")
                else:
                    st.error(f"Error: {response.json()['detail']}")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
        else:
            st.warning("Please enter a collection name to delete")

if __name__ == "__main__":
    main()