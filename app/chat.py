import os
import logging
import json
import textwrap
from typing import Dict
from utils import get_bedrock_client

from langchain_community.vectorstores.pgvector import PGVector
from langchain_community.embeddings import BedrockEmbeddings
from langchain_community.llms.bedrock import Bedrock
from langchain.chains import RetrievalQA, ConversationalRetrievalChain
from langchain.chains.llm import LLMChain
from langchain.chains.conversational_retrieval.prompts import CONDENSE_QUESTION_PROMPT, QA_PROMPT
from langchain.chains.question_answering import load_qa_chain
from langchain.memory import ConversationBufferMemory
from langchain_community.llms import SagemakerEndpoint
from langchain_community.llms.sagemaker_endpoint import LLMContentHandler
from langchain.docstore.document import Document

from langchain.embeddings import HuggingFaceEmbeddings
from langchain import HuggingFaceHub

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


connection_string = PGVector.connection_string_from_db_params(
        driver=os.environ.get("PGVECTOR_DRIVER", "psycopg2"),
        host=os.environ.get("PGVECTOR_HOST", "llm-chatbot.callkltzuxly.ap-southeast-1.rds.amazonaws.com"),
        port=int(os.environ.get("PGVECTOR_PORT", "5432")),
        database=os.environ.get("PGVECTOR_DATABASE", "chatbot"),
        user=os.environ.get("PGVECTOR_USER", "postgres"),
        password=os.environ.get("PGVECTOR_PASSWORD", "postgres123"))


chat_history = []


class ContentHandler(LLMContentHandler):
    content_type = "application/json"
    accepts = "application/json"

    def transform_input(self, prompt: str, model_kwargs: Dict) -> bytes:
        input_str = json.dumps({"inputs": prompt, "parameters": model_kwargs})
        return input_str.encode("utf-8")

    def transform_output(self, output: bytes) -> str:
        response_json = json.loads(output.read().decode("utf-8"))
        return response_json[0]["generated_text"]


def print_response(llm_response):
    temp = [textwrap.fill(line, width=100) for line in llm_response['result'].split('\n')]
    response = '\n'.join(temp)
    print(f"{llm_response['query']}\n \n{response}'\n \n Source Documents:")
    for source in llm_response["source_documents"]:
        print(source.metadata)


def claude(chat_input):
    llm = Bedrock(
        credentials_profile_name="default",
        model_id="anthropic.claude-v2:1",
        client=get_bedrock_client(),
    )

    streaming_llm = Bedrock(
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

    db = PGVector(
        collection_name=str(chat_input.bot_id),
        connection_string=connection_string,
        embedding_function=embeddings,
    )

    retriever = db.as_retriever()
    query = chat_input.message.question

    question_generator = LLMChain(llm=llm, prompt=CONDENSE_QUESTION_PROMPT)
    doc_chain = load_qa_chain(streaming_llm, chain_type="stuff", prompt=QA_PROMPT)

    bot = ConversationalRetrievalChain(
        retriever=retriever,
        combine_docs_chain=doc_chain,
        question_generator=question_generator,

    )

    result = bot.invoke({"question": query, "chat_history": chat_history})
    chat_history.append((query, result["answer"]))

    return result


def t5(chat_input):
    embeddings = HuggingFaceEmbeddings()
    db = PGVector(
        collection_name=str(chat_input.bot_id),
        connection_string=connection_string,
        embedding_function=embeddings,
    )

    retriever = db.as_retriever()
    query = chat_input.message.question

    content_handler = ContentHandler()
    llm = SagemakerEndpoint(
        endpoint_name='t5-large-demo',
        region_name='us-east-1',
        model_kwargs={"max_new_tokens": 500, "top_p": 0.9, "temperature": 0.6},
        endpoint_kwargs={"CustomAttributes": 'accept_eula=true'},
        content_handler=content_handler,
    )

    llm_qa_smep_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type='stuff',
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": QA_PROMPT}
    )

    r = print_response(llm_qa_smep_chain(query))

    # chain = load_qa_chain(llm=llm, prompt=QA_PROMPT)
    # chain({"input_documents": docs, "question": query}, return_only_outputs=True)
    # llm = HuggingFacePipeline.from_model_id(model_id="google/flan-t5-large", task="text2text-generation", model_kwargs={"temperature": 0,})
    # memory = ConversationBufferMemory(llm=llm, memory_key="chat_history", output_key='answer', return_messages=True)
    # chain = ConversationalRetrievalChain.from_llm(llm, retriever=retriever, return_source_documents=True, return_generated_question=True)
    # result = chain({"question": query})

    # question_generator = LLMChain(llm=llm, verbose=True, prompt=CONDENSE_QUESTION_PROMPT)
    # doc_chain = load_qa_chain(llm, chain_type="stuff", prompt=QA_PROMPT)
    #
    # bot = ConversationalRetrievalChain(
    #     retriever=retriever,
    #     combine_docs_chain=doc_chain,
    #     question_generator=question_generator,
    #     return_source_documents=True,
    # )
    #
    # result = bot.invoke({"question": query, "chat_history": chat_history})
    # chat_history.append((query, result["answer"]))

    return result
