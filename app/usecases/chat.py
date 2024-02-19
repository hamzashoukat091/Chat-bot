import json
import os
import logging
from copy import deepcopy
from datetime import datetime
from typing import Literal

from langchain.docstore.document import Document
from langchain_community.vectorstores.pgvector import PGVector
from langchain_community.embeddings import BedrockEmbeddings
from langchain_community.llms.bedrock import Bedrock
from app.utils import get_bedrock_client
from langchain.indexes.vectorstore import VectorStoreIndexWrapper
from langchain.chains import RetrievalQA
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import StrOutputParser
from langchain.chains import create_sql_query_chain
from langchain import hub

from bedrock import _create_body, get_model_id, invoke
from app.config import SEARCH_CONFIG
from app.repositories.conversation import (
    store_conversation,
    find_conversation_by_id,
    RecordNotFoundError
)
# from app.repositories.custom_bot import find_alias_by_id, store_alias
from app.usecases.bot import fetch_bot
from utils import get_current_time, is_running_on_lambda
# from app.vector_search import SearchResult, search_related_docs
# from ulid import ULID

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


connection_string = PGVector.connection_string_from_db_params(
        driver=os.environ.get("PGVECTOR_DRIVER", "psycopg2"),
        host=os.environ.get("PGVECTOR_HOST", "localhost"),
        port=int(os.environ.get("PGVECTOR_PORT", "5432")),
        database=os.environ.get("PGVECTOR_DATABASE", "chatbot"),
        user=os.environ.get("PGVECTOR_USER", "postgres"),
        password=os.environ.get("PGVECTOR_PASSWORD", "postgres123"))


def prepare_conversation(user_id: str, chat_input):
    current_time = get_current_time()

    logger.info("Bot id is provided. Fetching bot.")
    owned, bot = fetch_bot(user_id, chat_input.bot_id)

    return bot


def get_invoke_payload(message_map, chat_input):
    messages = trace_to_root(
        node_id=chat_input.message.parent_message_id,
        message_map=message_map,
    )
    messages.append(chat_input.message)  # type: ignore
    prompt = get_buffer_string(messages)
    body = _create_body(chat_input.message.model, prompt)
    model_id = get_model_id(chat_input.message.model)
    accept = "application/json"
    content_type = "application/json"
    return {
        "body": body,
        "model_id": model_id,
        "accept": accept,
        "content_type": content_type,
    }


def trace_to_root(node_id: str | None, message_map):
    """Trace message map from leaf node to root node."""
    result = []
    if not node_id or node_id == "system":
        node_id = "instruction" if "instruction" in message_map else "system"

    current_node = message_map.get(node_id)
    while current_node:
        result.append(current_node)
        parent_id = current_node.parent
        if parent_id is None:
            break
        current_node = message_map.get(parent_id)

    return result[::-1]


# def compress_knowledge(query: str, results: list[SearchResult]) -> tuple[bool, str]:
#     """Compress knowledge to avoid token limit. Extract only related parts from the search results."""
#     contexts_prompt = ""
#     for result in results:
#         contexts_prompt += f"<context>\n{result.content}</context>\n"
#     NO_RELEVANT_DOC = "THERE_IS_NO_RELEVANT_DOC"
#     PROMPT = """Human: Given the following question and contexts, extract any part of the context *AS IS* that is relevant to answer the question.
# Remember, *DO NOT* edit the extracted parts of the context.
# <question>
# {}
# </question>
# <contexts>
# {}
# </contexts>
# If none of the context is relevant, just say {}.

# Assistant:
# """.format(
#         query, contexts_prompt, NO_RELEVANT_DOC
#     )
#     reply_txt = invoke(prompt=PROMPT, model="claude-instant-v1")
#     print(reply_txt)

#     if reply_txt.find(NO_RELEVANT_DOC) != -1:
#         return False, ""

#     return reply_txt


def insert_knowledge(wrapper, conversation, search_results):
    """Insert knowledge to the conversation."""

    llm = Bedrock(
        credentials_profile_name="default",
        model_id="anthropic.claude-v2:1",
        client=get_bedrock_client(),
        streaming=True,
    )

    if len(search_results) == 0:
        return conversation

    context_prompt = ""
    for result in search_results:
        context_prompt += f"<context>\n{result}</context>\n"
    instruction_prompt = conversation.message_map["instruction"].content.body
    inserted_prompt = """You must respond based on given contexts.
    The contexts are as follows:
    <contexts>
    {}
    </contexts>
    Remember, *RESPOND BASED ON THE GIVEN CONTEXTS. YOU MUST NEVER GUESS*. If you cannot find source from the contexts, just say "I don't know".
    In addition, *YOU MUST OBEY THE FOLLOWING RULE*:
    <rule>
    Write only SQL query for PostgreSQL
    </rule>
    """.format(
            search_results
        )

    logger.info(f"Inserted prompt: {inserted_prompt}")

    conversation_with_context = deepcopy(conversation)
    conversation_with_context.message_map["instruction"].content.body = inserted_prompt

    return wrapper.query(inserted_prompt, llm=llm)

# def insert_knowledge(
#     conversation: ConversationModel, search_results: list[SearchResult]
# ) -> ConversationModel:
#     """Insert knowledge to the conversation."""
#     if len(search_results) == 0:
#         return conversation
#
#     context_prompt = ""
#     for result in search_results:
#         context_prompt += f"<context>\n{result.content}</context>\n"
#
#     instruction_prompt = conversation.message_map["instruction"].content.body
#     inserted_prompt = """You must respond based on given contexts.
# The contexts are as follows:
# <contexts>
# {}
# </contexts>
# Remember, *RESPOND BASED ON THE GIVEN CONTEXTS. YOU MUST NEVER GUESS*. If you cannot find source from the contexts, just say "I don't know".
# In addition, *YOU MUST OBEY THE FOLLOWING RULE*:
# <rule>
# {}
# </rule>
# """.format(
#         context_prompt, instruction_prompt
#     )
#     logger.info(f"Inserted prompt: {inserted_prompt}")
#
#     conversation_with_context = deepcopy(conversation)
#     conversation_with_context.message_map["instruction"].content.body = inserted_prompt
#
#     return conversation_with_context


def chat(user_id: str, chat_input):
    bot = prepare_conversation(user_id, chat_input)

    if bot:

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

        db = PGVector(
            collection_name=bot.id,
            connection_string=connection_string,
            embedding_function=embeddings,
        )

        retriever = db.as_retriever()

        qa = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=retriever,
            chain_type="stuff"
        )

        query = conversation.message_map[user_msg_id].content.body

        # Retrieve and generate using the relevant snippets of the blog.
        prompt = hub.pull("rlm/rag-prompt")

        def format_docs(docs):
            return "\n\n".join(docc.page_content for docc in docs)

        rag_chain_from_docs = (
                RunnablePassthrough.assign(context=(lambda x: format_docs(x["context"])))
                | prompt
                | llm
                | StrOutputParser()
        )

        rag_chain_with_source = RunnableParallel(
            {"context": retriever, "question": RunnablePassthrough()}
        ).assign(answer=rag_chain_from_docs)

        return rag_chain_with_source.invoke(query)
        # results = search_related_docs(
        #     bot_id=bot.id, limit=SEARCH_CONFIG["max_results"], query=query
        # )

        # Search in pgvector
        # results = db.max_marginal_relevance_search_with_score(query)

        # logger.info(f"Search results from vector store: {results}")

        # Extract relevant information
        # arr = []
        # for doc, score in results:
        #     arr.append(doc.page_content)

        # wrapper = VectorStoreIndexWrapper(
        #     vectorstore=db
        # )

        # Insert contexts to instruction
        # conversation_with_context = insert_knowledge(conversation, results)

        # Insert contexts to instruction
        # conversation_with_context = insert_knowledge(wrapper, conversation, arr)
        # message_map = conversation_with_context.message_map

        # return conversation_with_context
    return output