import os

from app.repositories.common import RecordNotFoundError, compose_bot_id
from app.repositories.custom_bot import (
    find_public_bot_by_id,
    store_bot,
    update_bot,
)
from app.utils import (
    check_if_file_exists_in_s3,
    compose_upload_document_s3_path,
    compose_upload_temp_s3_path,
    compose_upload_temp_s3_prefix,
    delete_file_from_s3,
    delete_files_with_prefix_from_s3,
    generate_presigned_url,
    get_current_time,
    move_file_in_s3,
)

DOCUMENT_BUCKET = os.environ.get("DOCUMENT_BUCKET", "bedrock-documents-v1")


def _update_s3_documents_by_diff(
    user_id: str,
    bot_id: str,
    added_filenames: list[str],
    # updated_filenames: list[str],
    deleted_filenames: list[str],
):
    for filename in added_filenames:
        tmp_path = compose_upload_temp_s3_path(user_id, bot_id, filename)
        document_path = compose_upload_document_s3_path(user_id, bot_id, filename)
        # move_file_in_s3(DOCUMENT_BUCKET, tmp_path, document_path)

        # for filename in updated_filenames:
        #     tmp_path = compose_upload_temp_s3_path(user_id, bot_id, filename)
        #     document_path = compose_upload_document_s3_path(user_id, bot_id, filename)

        #     if not check_if_file_exists_in_s3(DOCUMENT_BUCKET, document_path):
        #         # Check the original file which will be replaced exists or not.
        #         raise FileNotFoundError(f"File {document_path} does not exist.")

        # move_file_in_s3(DOCUMENT_BUCKET, tmp_path, document_path)

    # for filename in deleted_filenames:
    #     document_path = compose_upload_document_s3_path(user_id, bot_id, filename)
    #     delete_file_from_s3(DOCUMENT_BUCKET, document_path)


def create_new_bot(user_id: str, bot_input):
    """Create a new bot.
    Bot is created as private and not pinned.
    """
    current_time = get_current_time()
    has_knowledge = bot_input.knowledge and (
        len(bot_input.knowledge.source_urls) > 0
        or len(bot_input.knowledge.sitemap_urls) > 0
        or len(bot_input.knowledge.filenames) > 0
    )
    sync_status = "QUEUED" if has_knowledge else "SUCCEEDED"

    source_urls = []
    sitemap_urls = []
    filenames = []
    if bot_input.knowledge:
        source_urls = bot_input.knowledge.source_urls
        sitemap_urls = bot_input.knowledge.sitemap_urls

        # Commit changes to S3
        _update_s3_documents_by_diff(
            user_id, bot_input.id, bot_input.knowledge.filenames, []
        )
        # Delete files from upload temp directory
        delete_files_with_prefix_from_s3(
            DOCUMENT_BUCKET, compose_upload_temp_s3_prefix(user_id, bot_input.id)
        )
        filenames = bot_input.knowledge.filenames

    store_bot(user_id, '')

    return 'ok'


def fetch_bot(user_id: str, bot_id: str):
    """Fetch bot by id.
    The first element of the returned tuple is whether the bot is owned or not.
    `True` means the bot is owned by the user.
    `False` means the bot is shared by another user.
    """

    try:
        return False, find_public_bot_by_id(bot_id)
    except RecordNotFoundError:
        raise RecordNotFoundError(
            f"Bot with ID {bot_id} not found in both private (for user {user_id}) and public items."
        )


def remove_uploaded_file(user_id: str, bot_id: str, filename: str):
    delete_file_from_s3(
        DOCUMENT_BUCKET, compose_upload_temp_s3_path(user_id, bot_id, filename)
    )
    return
