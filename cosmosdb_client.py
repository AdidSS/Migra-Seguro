# cosmosdb_client.py

from azure.cosmos import CosmosClient, PartitionKey, exceptions
import os
from datetime import datetime

# --- Azure Cosmos DB configuration ---

COSMOSDB_ENDPOINT = "https://signatures-db.documents.azure.com:443/"
COSMOSDB_KEY = "Q43IfhU8SnPr9eucXvIVYHKN1eoMFKhsdCctL0nX28JOf7M831rBNiZiFSXfDY1FxoDc5h3SxKgyACDbvlF3NQ=="
DATABASE_NAME = "document_signing_db"
CONTAINER_NAME = "signed_documents"

# --- Initialize client ---

client = CosmosClient(COSMOSDB_ENDPOINT, credential=COSMOSDB_KEY)
database = client.create_database_if_not_exists(id=DATABASE_NAME)
container = database.create_container_if_not_exists(
    id=CONTAINER_NAME,
    partition_key=PartitionKey(path="/document_id"),
    offer_throughput=400
)

user_container = client.get_database_client("users").get_container_client("user_credentials")


# --- Functions ---

def save_document_entry_cosmos(document_data):
    """Save or update a document entry into Cosmos DB."""
    try:
        container.upsert_item(body=document_data)  # Cambiado a upsert para permitir actualización también
    except exceptions.CosmosHttpResponseError as e:
        print(f"Error saving document: {e}")

def load_all_documents_cosmos():
    """Load all documents from Cosmos DB."""
    query = "SELECT * FROM c"
    items = list(container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))
    return items

def load_signed_documents_cosmos():
    """Load only documents that have been signed."""
    query = "SELECT * FROM c WHERE c.is_signed = true"
    items = list(container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))
    return items

def load_pending_documents_cosmos():
    """Load only documents that are pending signature."""
    query = "SELECT * FROM c WHERE c.is_signed = false"
    items = list(container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))
    return items

def update_document_as_signed_cosmos(document_id, signature_data):
    """Update a document marking it as signed and saving signature info."""
    try:
        item = container.read_item(item=document_id, partition_key=document_id)

        item["is_signed"] = True
        item["signature_base64"] = signature_data["signature_base64"]
        item["signed_by_key_id"] = signature_data["signed_by_key_id"]
        item["signature_algorithm"] = signature_data["signature_algorithm"]
        item["key_vault_url"] = signature_data["key_vault_url"]
        item["key_name"] = signature_data["key_name"]
        item["timestamp"] = datetime.utcnow().isoformat()

        container.replace_item(item=document_id, body=item)
    except exceptions.CosmosResourceNotFoundError:
        print(f"Document with ID {document_id} not found for updating.")

def find_document_by_id(document_id):
    """Find a document in Cosmos DB by its document_id."""
    try:
        item_response = container.read_item(item=document_id, partition_key=document_id)
        return item_response
    except exceptions.CosmosResourceNotFoundError:
        return None


def load_all_users_cosmos():
    """Load all users from the user_credentials container."""
    user_db = client.get_database_client("users")
    user_container = user_db.get_container_client("user_credentials")
    query = "SELECT * FROM c"
    return list(user_container.query_items(query=query, enable_cross_partition_query=True))

def find_user_by_id(user_id):
    """Find a user by ID from the user_credentials container."""
    try:
        return user_container.read_item(item=user_id, partition_key=user_id)
    except exceptions.CosmosResourceNotFoundError:
        return None