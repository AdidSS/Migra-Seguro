# mock_database.py

from cosmosdb_client import (
    save_document_entry_cosmos,
    load_all_documents_cosmos,
    find_document_by_id,
    load_signed_documents_cosmos,
    load_pending_documents_cosmos,
    update_document_as_signed_cosmos,
    load_all_users_cosmos
)

# --- Wrappers ---

def save_document_entry(
    document_id,
    document_name,
    document_hash_base64,
    is_signed,
    uploaded_by,
    category,
    visibility,
    blob_name,
    signature_base64=None,
    signed_by_key_id=None,
    signature_algorithm=None,
    key_vault_url=None,
    key_name=None,
    timestamp=None
):
    """Save a document record to Cosmos DB."""
    document_data = {
        "id": document_id,
        "document_id": document_id,
        "document_name": document_name,
        "document_hash_base64": document_hash_base64,
        "is_signed": is_signed,
        "uploaded_by": uploaded_by,
        "category": category,
        "visibility": visibility,
        "blob_name": blob_name,
        "signature_base64": signature_base64,
        "signed_by_key_id": signed_by_key_id,
        "signature_algorithm": signature_algorithm,
        "key_vault_url": key_vault_url,
        "key_name": key_name,
        "timestamp": timestamp
    }
    save_document_entry_cosmos(document_data)


def load_all_entries():
    """Load all documents from Cosmos DB."""
    return load_all_documents_cosmos()

def load_signed_entries():
    """Load only signed documents."""
    return load_signed_documents_cosmos()

def load_pending_entries():
    """Load only unsigned (pending) documents."""
    return load_pending_documents_cosmos()

def update_document_as_signed(document_id, signature_data):
    """Mark a pending document as signed in the database."""
    return update_document_as_signed_cosmos(document_id, signature_data)

def find_entry_by_document_id(document_id):
    """Find a document by its ID."""
    return find_document_by_id(document_id)

def load_all_users():
    """Load all user credentials."""
    return load_all_users_cosmos()