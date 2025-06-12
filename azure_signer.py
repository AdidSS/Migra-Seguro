# azure_signer.py

from azure.identity import DefaultAzureCredential
from azure.keyvault.keys import KeyClient
from azure.keyvault.keys.crypto import CryptographyClient, SignatureAlgorithm
import hashlib
import base64

# --- Configuration ---

# Update these values according to your Key Vault and Key names
KEY_VAULT_URL = "https://docsigning-keyv.vault.azure.net/"
KEY_NAME = "docsigning-key"

# --- Initialize Azure clients only once ---

credential = DefaultAzureCredential()
key_client = KeyClient(vault_url=KEY_VAULT_URL, credential=credential)
key = key_client.get_key(KEY_NAME)
crypto_client = CryptographyClient(key, credential=credential)

# --- Functions ---

def calculate_document_hash(document_bytes):
    """Calculate SHA-256 hash of the document."""
    return hashlib.sha256(document_bytes).digest()

def sign_document_with_keyvault(document_bytes):
    """
    Signs a document's SHA-256 hash using Azure Key Vault RSA key.
    
    Args:
        document_bytes (bytes): Content of the document to sign.

    Returns:
        dict: Contains base64 encoded document hash, signature, and signing key ID.
    """
    # Calculate the document hash
    document_hash = calculate_document_hash(document_bytes)

    # Request Azure Key Vault to sign the hash
    sign_result = crypto_client.sign(SignatureAlgorithm.rs256, document_hash)

    # Prepare output
    result = {
        "document_hash_base64": base64.b64encode(document_hash).decode(),
        "signature_base64": base64.b64encode(sign_result.signature).decode(),
        "signed_by_key_id": key.id,  # <-- Aquí ahora incluimos el Key ID real
        "signature_algorithm": "RS256",
        "key_vault_url": KEY_VAULT_URL,
        "key_name": KEY_NAME
    }
    return result
