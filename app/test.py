import os
from langchain_community.embeddings import BedrockEmbeddings
from langchain_community.llms.bedrock import Bedrock
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders.s3_directory import S3DirectoryLoader
from langchain_community.vectorstores.pgvector import PGVector

from utils import get_bedrock_client

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
    model_id="cohere.embed-multilingual-v3",
    client=get_bedrock_client(),
)


def test(bot_id, directory):
    # Load text data and split documents
    loader = S3DirectoryLoader(bucket=DOCUMENT_BUCKET, prefix=directory, use_ssl=True)
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    docs = text_splitter.split_documents(documents)

    print(docs)

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
        collection_name=str(bot_id),
        connection_string=connection_string,
        pre_delete_collection=True,
    )

    return 'ok'
