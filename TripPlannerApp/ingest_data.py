import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

load_dotenv()

def create_vector_db():
    # 1. Load the FAQ file
    loader = TextLoader("travel_agent_faq.txt")
    documents = loader.load()

    # 2. Split text into chunks (so the AI can find specific answers easily)
    text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = text_splitter.split_documents(documents)

    # 3. Create Embeddings and Save to a local folder named 'db'
    print("Creating vector database... this may take a moment.")
    vector_db = Chroma.from_documents(
        documents=chunks,
        embedding=OpenAIEmbeddings(),
        persist_directory="./chroma_db"
    )
    print("Database created and saved to ./chroma_db")

if __name__ == "__main__":
    create_vector_db()