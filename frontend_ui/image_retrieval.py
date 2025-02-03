import streamlit as st
import requests
import json
from PIL import Image
from io import BytesIO
from database import init_db, add_user, verify_user, get_textbook_metadata
from streamlit_lottie import st_lottie
from concurrent.futures import ThreadPoolExecutor
from anthropic_client   import AnthropicClient
import os
from pathlib import Path
from streamlit_modal import Modal

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
SOURCE_DATA_DIRECTORY = ''
SOURCE_THUMBNAIL_DIRECTORY = ''

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
    .search-title {
        font-size: 24px !important;
        font-weight: bold !important;
        color: #1E3D59 !important;
        margin-bottom: 10px !important;
    }
    .search-container {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        margin: 15px 0;
        border: 1px solid #e9ecef;
    }
    .metadata-modal {
        background-color: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .modal-backdrop {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.5);
        z-index: 1000;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    
    .modal-content {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        max-width: 800px;
        width: 90%;
        max-height: 90vh;
        overflow-y: auto;
        position: relative;
    }
    
    .modal-close {
        position: absolute;
        top: 10px;
        right: 10px;
        font-size: 24px;
        cursor: pointer;
        color: #666;
    }
    
    .modal-header {
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 2px solid #eee;
    }
    .section-header {
        font-size: 28px !important;
        font-weight: bold !important;
        color: #1E3D59 !important;
        margin: 30px 0 20px 0 !important;
        padding-bottom: 10px !important;
        border-bottom: 2px solid #1E3D59;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .search-metadata {
        font-size: 16px !important;
        color: #666666 !important;
        margin: 5px 0 !important;
        line-height: 1.5 !important;
    }
    .page-info {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 5px;
        margin-top: 10px;
        font-size: 14px;
        text-align: center;
    }
    .score-badge {
        background-color: #1E3D59;
        color: white;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 12px;
        margin-top: 5px;
        display: inline-block;
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
    
    page = st.sidebar.radio("Choose a page", ["Index Images", "Smart Search", "Qdrant Collections Management"])

    # if page == "Document Upload":
    #     document_upload_page()
    if page == "Smart Search":
        image_search_page()
    elif page == "Qdrant Collections Management":
        qdrant_collections_page()
    elif page == "Index Images":
        document_upload_page()

# Images embed and indexing to Qdrant vector store
def document_upload_page():
    st.header("Document Upload")
    st.write("Upload image file to index in the database")
    
    uploaded_file = st.file_uploader(
        "Choose a file", 
        type=['pdf', 'zip', 'png', 'jpg', 'jpeg'],
        # type=['png', 'jpg', 'jpeg'],
        # help="Supported formats: PDF, ZIP (containing images), PNG, JPG, JPEG"
        help="Supported formats: ZIP (containing images), PNG, JPG, JPEG"
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


# def show_metadata_modal(metadata):
#     """Display metadata in a modal dialog"""
#     with st.container():
#         # Create a semi-transparent overlay
#         st.markdown("""
#             <div style="
#                 position: fixed;
#                 top: 0;
#                 left: 0;
#                 width: 100%;
#                 height: 100%;
#                 background-color: rgba(0, 0, 0, 0.5);
#                 z-index: 1000;
#             "></div>
#         """, unsafe_allow_html=True)
        
#         # Create the modal content
#         st.markdown("""
#             <div style="
#                 position: fixed;
#                 top: 50%;
#                 left: 50%;
#                 transform: translate(-50%, -50%);
#                 background-color: white;
#                 padding: 20px;
#                 border-radius: 10px;
#                 width: 80%;
#                 max-height: 80vh;
#                 overflow-y: auto;
#                 z-index: 1001;
#             ">
#         """, unsafe_allow_html=True)
        
#         # Modal content
#         st.markdown("### Textbook Metadata")
#         st.markdown("---")
        
#         col_img, col_info = st.columns([1, 2])
#         with col_img:
#             if os.path.exists(metadata['thumbnail_location']):
#                 st.image(metadata['thumbnail_location'], width=200)
#             else:
#                 st.write("Thumbnail not available")
        
#         with col_info:
#             st.markdown(f"**Title:** {metadata['title']}")
#             st.markdown(f"**Authors:** {', '.join(metadata['main_authors'])}")
#             st.markdown(f"**Publisher:** {metadata['publisher']}")
#             st.markdown(f"**Year:** {metadata['published_year']}")
#             st.markdown(f"**Edition:** {metadata['edition']}")
        
#         st.markdown("### Additional Information")
#         st.markdown(f"**Related Authors:** {', '.join(metadata['related_authors'])}")
#         st.markdown(f"**Languages:** {', '.join(metadata['languages'])}")
#         st.markdown(f"**Subjects:** {', '.join(metadata['subjects'])}")
        
#         st.markdown("### Summary")
#         st.write(metadata['summary'])
        
#         if st.button("Close", key="close_modal"):
#             st.session_state.show_modal = False
#             st.rerun()
        
#         st.markdown("</div>", unsafe_allow_html=True)

def display_search_results(results, query):

    # Initialize modal
    modal = Modal(key="metadata_modal", title="Metadata")

    # Initialize session state for modal control if not exists
    if 'show_modal' not in st.session_state:
        st.session_state.show_modal = False
        st.session_state.current_metadata = None

    # Group results by ISBN
    grouped_results = {}
    retrieved_points = results.get('retrieved_image_points', [])
    for item in retrieved_points:
        isbn = item['ISBN']
        if isbn not in grouped_results:
            metadata = get_textbook_metadata(isbn)
            grouped_results[isbn] = {
                'metadata': metadata,
                'pages': []
            }

        if not item['image'].startswith("/home"):
            image_path = SOURCE_DATA_DIRECTORY + item['image'].split('/')[-1]
        else:
            image_path = SOURCE_DATA_DIRECTORY + item['image'].split('/')[-1]

        grouped_results[isbn]['pages'].append({'path': image_path, 'score': item['score'],'page_number': item['page_number']})

    # Display textbook results
    st.markdown('<h2 class="section-header">Search Results</h2>', unsafe_allow_html=True)
    
    for isbn, data in grouped_results.items():
        metadata = data['metadata']
        metadata['thumbnail_location'] = SOURCE_THUMBNAIL_DIRECTORY + metadata['thumbnail_location'].split('/')[-1]
        
        with st.container():
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col1:
                if os.path.exists(metadata['thumbnail_location']):
                    st.image(metadata['thumbnail_location'], width=150)
            
            with col2:
                st.markdown(f'<div class="search-title">{metadata["title"]}</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="search-metadata">'
                    f'<strong>Authors:</strong> {", ".join(metadata["main_authors"] + metadata["related_authors"])}<br>'
                    f'<strong>Publisher:</strong> {metadata["published_year"]}<br>'
                    f'<strong>Edition:</strong> {metadata["edition"]}'
                    f'</div>',
                    unsafe_allow_html=True
                )

            with col3:
                open_modal = st.button(label='View Metadata')
                if open_modal:
                # if st.button("View Metadata", key=f"view_metadata_{isbn}"):
                    print("View metadata button called!")
                    with modal.container():
                        col_img, col_info = st.columns([1, 2])
                        
                        with col_img:
                            if os.path.exists(metadata['thumbnail_location']):
                                st.image(metadata['thumbnail_location'], width=200)
                            else:
                                st.write("Thumbnail not available")
                        
                        with col_info:
                            st.markdown(f"**Title:** {metadata['title']}")
                            st.markdown(f"**Authors:** {', '.join(metadata['main_authors'])}")
                            st.markdown(f"**Publisher:** {metadata['publisher']}")
                            st.markdown(f"**Year:** {metadata['published_year']}")
                            st.markdown(f"**Edition:** {metadata['edition']}")
                        
                        st.markdown("### Additional Information")
                        st.markdown(f"**Related Authors:** {', '.join(metadata['related_authors'])}")
                        st.markdown(f"**Languages:** {', '.join(metadata['languages'])}")
                        st.markdown(f"**Subjects:** {', '.join(metadata['subjects'])}")
                        
                        st.markdown("### Summary")
                        st.write(metadata['summary'])

            # ------
            # with col3:
            #     if st.button("View Metadata", key=f"view_metadata_{isbn}"):
            #         print("view metadata button pressed!")
            #         show_metadata_modal(metadata)
            # with col3:
            #     button_key = f"view_metadata_{isbn}"  # Create unique key
            #     print(f"Creating button with key: {button_key}")  # Debug print
                
            #     if st.button("View Metadata"):
            #         print(f"Button clicked for ISBN: {isbn}")  # Debug print
            #         st.session_state.show_modal = True
            #         st.session_state.current_metadata = metadata
            #         st.rerun()

    # Show modal if triggered
    # if st.session_state.show_modal and st.session_state.current_metadata:
    #     show_metadata_modal(st.session_state.current_metadata)

    # Display top 3 relevant pages across all books
    if grouped_results:
        st.markdown('<h2 class="section-header">Retrieved Pages</h2>', unsafe_allow_html=True)
        
        # Flatten and sort all pages by score
        all_pages = []
        for isbn, data in grouped_results.items():
            for page in data['pages']:
                all_pages.append({
                    'isbn': isbn,
                    'metadata': data['metadata'],
                    'path': page['path'],
                    'score': page['score'],
                    'page_number': page['page_number']
                })
        
        # Sort by score in descending order and take top 3
        all_pages.sort(key=lambda x: x['score'], reverse=True)
        top_3_pages = all_pages[:3]

        # Display in columns
        cols = st.columns(3)
        for idx, page_data in enumerate(top_3_pages):
            with cols[idx]:
                try:
                    image = Image.open(page_data['path'])
                    st.image(image, use_container_width=True)
                    
                    # Display metadata for the page
                    st.markdown(
                        f'<div class="search-metadata" style="text-align: center;">'
                        f'<strong>From:</strong> {page_data["metadata"]["title"]}<br>'
                        f'<strong>Page:</strong> {page_data["page_number"]}<br>'
                        f'<strong>Relevance Score:</strong> {page_data["score"]:.2f}'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                except Exception as e:
                    st.error(f"Error loading image: {str(e)}")


# Main Image search Page
def image_search_page():
    st.header("Smart Search")
    st.write("AI-powered image search for text queries and Answer generation")
    
    query = st.text_input("Enter your search query")
    
    if st.button("Search"):
        if query:
            with st.spinner("Searching..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/document_retrieval",
                        json={"user_query": query}
                    )
                    
                    if response.status_code == 200:
                        results = response.json()
                        if results:
                            # Generate and display AI response
                            with st.container():
                                st.markdown('<h2 class="section-header">AI Generated Response</h2>', unsafe_allow_html=True)
                                with st.spinner("Generating answer..."):
                                    # Your existing AI response generation code here
                                    pass

                            
                            # Display search results
                            display_search_results(results, query)
                            
                        else:
                            st.warning("No results found.")
                    else:
                        st.error("Error in search request")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
        else:
            st.warning("Please enter a search query")

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

    # st.subheader("Delete Collection")
    # collection_to_delete = st.text_input("Enter collection name to delete")
    # if st.button("Delete Collection"):
    #     if collection_to_delete:
    #         try:
    #             response = requests.post(
    #                 f"{BACKEND_URL}/delete_qdrant_collection",
    #                 json={"collection_name": collection_to_delete}
    #             )
    #             if response.status_code == 200:
    #                 st.success(f"Collection '{collection_to_delete}' deleted successfully!")
    #             else:
    #                 st.error(f"Error: {response.json()['detail']}")
    #         except Exception as e:
    #             st.error(f"An error occurred: {str(e)}")
    #     else:
    #         st.warning("Please enter a collection name to delete")

if __name__ == "__main__":
    main()