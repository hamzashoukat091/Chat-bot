import json
import logging
import os
from datetime import datetime
from decimal import Decimal as decimal

import boto3
from app.repositories.common import (
    RecordAccessNotAllowedError,
    RecordNotFoundError,
    _get_table_client,
    _get_table_public_client,
    compose_bot_alias_id,
    compose_bot_id,
    decompose_bot_alias_id,
    decompose_bot_id,
)
from app.utils import get_current_time
from boto3.dynamodb.conditions import Attr, Key
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
sts_client = boto3.client("sts")


def store_bot(user_id: str, custom_bot):
    table = _get_table_client(user_id)
    logger.info(f"Storing bot: {custom_bot}")

    item = {
        "PK": user_id,
        "SK": compose_bot_id(user_id, custom_bot.id),
        "Title": custom_bot.title,
        "Description": custom_bot.description,
        "Instruction": custom_bot.instruction,
        "CreateTime": decimal(custom_bot.create_time),
        "LastBotUsed": decimal(custom_bot.last_used_time),
        "IsPinned": custom_bot.is_pinned,
        "Knowledge": custom_bot.knowledge.model_dump(),
        "SyncStatus": custom_bot.sync_status,
        "SyncStatusReason": custom_bot.sync_status_reason,
        "LastExecId": custom_bot.sync_last_exec_id,
    }

    response = table.put_item(Item=item)
    return response


def update_bot(
    user_id: str,
    bot_id: str,
    title: str,
    description: str,
    instruction: str,
    directory: list[str],
    sync_status: str,
    sync_status_reason: str,
):
    """Update bot title, description, and instruction.
    NOTE: Use `update_bot_visibility` to update visibility.
    """
    table = _get_table_client(user_id)
    logger.info(f"Updating bot: {bot_id}")

    try:
        response = table.update_item(
            Key={"PK": user_id, "SK": compose_bot_id(user_id, bot_id)},
            UpdateExpression="SET Title = :title, Description = :description, Instruction = :instruction, Knowledge = :knowledge, SyncStatus = :sync_status, SyncStatusReason = :sync_status_reason",
            ExpressionAttributeValues={
                ":title": title,
                ":description": description,
                ":instruction": instruction,
                ":sync_status": sync_status,
                ":sync_status_reason": sync_status_reason,
            },
            ReturnValues="ALL_NEW",
            ConditionExpression="attribute_exists(PK) AND attribute_exists(SK)",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise RecordNotFoundError(f"Bot with id {bot_id} not found")
        else:
            raise e

    return response