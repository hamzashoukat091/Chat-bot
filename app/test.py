import os
import boto3
from langchain_community.embeddings import BedrockEmbeddings
from langchain_community.llms.bedrock import Bedrock
from langchain.text_splitter import CharacterTextSplitter, RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import S3FileLoader
from langchain.indexes.vectorstore import VectorStoreIndexWrapper
from langchain_community.vectorstores.pgvector import PGVector

from utils import get_bedrock_client
from app.embedding.loaders.base import BaseLoader
from app.utils import compose_upload_document_s3_path

# Set environment variables
DOCUMENT_BUCKET = os.environ.get("DOCUMENT_BUCKET", "bedrock-documents-v1")
region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
profile = os.environ.get("AWS_PROFILE", "default")

# Initialize Bedrock and Embeddings objects
llm = Bedrock(
    credentials_profile_name="default",
    model_id="anthropic.claude-v2:1",
    client=get_bedrock_client(),
    streaming=True,
)

embeddings = BedrockEmbeddings(
    credentials_profile_name="default",
    region_name="us-east-1",
    model_id="cohere.embed-english-v3",
    client=get_bedrock_client(),
)


def test(bot_id, filename):
    # Load text data and split documents
    loader = S3FileLoader(bucket=DOCUMENT_BUCKET, key=f"documents/{filename}")
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    docs = text_splitter.split_documents(documents)

    # Create PGVector instance
    connection_string = PGVector.connection_string_from_db_params(
        driver=os.environ.get("PGVECTOR_DRIVER", "psycopg2"),
        host=os.environ.get("PGVECTOR_HOST", "localhost"),
        port=int(os.environ.get("PGVECTOR_PORT", "5432")),
        database=os.environ.get("PGVECTOR_DATABASE", "chatbot"),
        user=os.environ.get("PGVECTOR_USER", "postgres"),
        password=os.environ.get("PGVECTOR_PASSWORD", "postgres123"),
    )

    PGVector.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name=bot_id,
        connection_string=connection_string,
        pre_delete_collection=True,
    )