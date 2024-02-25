import json
import logging
from decimal import Decimal as decimal

import boto3
from common import (
    TRANSACTION_BATCH_SIZE,
    RecordNotFoundError,
    _get_table_client,
    compose_conv_id,
)

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
sts_client = boto3.client("sts")


def store_conversation(user_id: str, conversation):
    logger.info(f"Storing conversation: {conversation.model_dump_json()}")
    table = _get_table_client(user_id)

    item_params = {
        "PK": user_id,
        "SK": compose_conv_id(user_id, conversation.id),
        "Title": conversation.title,
        "CreateTime": decimal(conversation.create_time),
        "MessageMap": json.dumps(
            {k: v.model_dump() for k, v in conversation.message_map.items()}
        ),
        "LastMessageId": conversation.last_message_id,
    }
    if conversation.bot_id:
        item_params["BotId"] = conversation.bot_id

    response = table.put_item(
        Item=item_params,
    )
    return response

def find_conversation_by_id(user_id: str, conversation_id: str):
    logger.info(f"Finding conversation: {conversation_id}")
    table = _get_table_client(user_id)
    response = table.query(
        IndexName="SKIndex",
        KeyConditionExpression=Key("SK").eq(compose_conv_id(user_id, conversation_id)),
    )
    if len(response["Items"]) == 0:
        raise RecordNotFoundError(f"No conversation found with id: {conversation_id}")

    # NOTE: conversation is unique
    item = response["Items"][0]

    return item


def delete_conversation_by_id(user_id: str, conversation_id: str):
    logger.info(f"Deleting conversation: {conversation_id}")
    table = _get_table_client(user_id)

    try:
        response = table.delete_item(
            Key={"PK": user_id, "SK": compose_conv_id(user_id, conversation_id)},
            ConditionExpression="attribute_exists(PK) AND attribute_exists(SK)",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise RecordNotFoundError(
                f"Conversation with id {conversation_id} not found"
            )
        else:
            raise e

    return response


def delete_conversation_by_user_id(user_id: str):
    logger.info(f"Deleting ALL conversations for user: {user_id}")
    table = _get_table_client(user_id)

    query_params = {
        "KeyConditionExpression": Key("PK").eq(user_id)
        # NOTE: Need SK to fetch only conversations
        & Key("SK").begins_with(f"{user_id}#CONV#"),
        "ProjectionExpression": "SK",  # Only SK is needed to delete
    }

    def delete_batch(batch):
        with table.batch_writer() as writer:
            for item in batch:
                writer.delete_item(Key={"PK": user_id, "SK": item["SK"]})

    try:
        response = table.query(
            **query_params,
        )

        while True:
            items = response.get("Items", [])
            for i in range(0, len(items), TRANSACTION_BATCH_SIZE):
                batch = items[i : i + TRANSACTION_BATCH_SIZE]
                delete_batch(batch)

            # Check if next page exists
            if "LastEvaluatedKey" not in response:
                break

            # Load next page
            query_params["ExclusiveStartKey"] = response["LastEvaluatedKey"]
            response = table.query(
                **query_params,
            )

    except ClientError as e:
        logger.error(f"An error occurred: {e.response['Error']['Message']}")


def change_conversation_title(user_id: str, conversation_id: str, new_title: str):
    logger.info(f"Updating conversation title: {conversation_id} to {new_title}")
    table = _get_table_client(user_id)

    try:
        response = table.update_item(
            Key={
                "PK": user_id,
                "SK": compose_conv_id(user_id, conversation_id),
            },
            UpdateExpression="set Title=:t",
            ExpressionAttributeValues={":t": new_title},
            ReturnValues="UPDATED_NEW",
            ConditionExpression="attribute_exists(PK) AND attribute_exists(SK)",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise RecordNotFoundError(
                f"Conversation with id {conversation_id} not found"
            )
        else:
            raise e

    logger.info(f"Updated conversation title response: {response}")

    return response
