import os

from app.repositories.common import RecordNotFoundError, compose_bot_id
from app.repositories.custom_bot import (
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


def remove_uploaded_file(user_id: str, bot_id: str, filename: str):
    delete_file_from_s3(
        DOCUMENT_BUCKET, compose_upload_temp_s3_path(user_id, bot_id, filename)
    )
    return
