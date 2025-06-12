# verify_signature_with_keyvault.py

from azure.identity import DefaultAzureCredential
from azure.keyvault.keys import KeyClient
from azure.keyvault.keys.crypto import CryptographyClient, SignatureAlgorithm
import base64
import hashlib

# --- Configuration ---

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

'''
def verify_signature_with_keyvault(document_bytes, signature_base64):
    """
    Verifies a signature against a document using Azure Key Vault RSA key.
    
    Args:
        document_bytes (bytes): Content of the document to verify.
        signature_base64 (str): Signature to verify, in base64 format.

    Returns:
        bool: True if the signature is valid, False otherwise.
    """
    # Calculate the document hash
    document_hash = calculate_document_hash(document_bytes)

    # Decode the signature from base64
    signature_bytes = base64.b64decode(signature_base64)

    # Ask Azure Key Vault to verify the signature
    verify_result = crypto_client.verify(SignatureAlgorithm.rs256, document_hash, signature_bytes)

    return verify_result.is_valid
'''

def verify_signature_with_keyvault(document_bytes, signature_base64):
    try:
        # Calcular el hash del documento
        document_hash = calculate_document_hash(document_bytes)
        
        # Intentar decodificar la firma
        try:
            signature_bytes = base64.b64decode(signature_base64)
        except Exception as e:
            print(f"Error decodificando la firma: {e}")
            return {"is_valid": False, "error": "Formato de firma inválido"}

        print("Debug info:")
        print(f"Hash del documento: {document_hash.hex()}")
        print(f"Longitud de la firma (bytes): {len(signature_bytes)}")
        
        # Verificar la firma
        try:
            verify_result = crypto_client.verify(
                algorithm=SignatureAlgorithm.rs256,
                digest=document_hash,
                signature=signature_bytes
            )
            
            if not verify_result.is_valid:
                print("La verificación falló")
                return {"is_valid": False, "error": "La firma no coincide con el documento"}
                
            return {"is_valid": True, "error": None}
            
        except Exception as e:
            print(f"Error durante la verificación: {e}")
            return {"is_valid": False, "error": str(e)}
            
    except Exception as e:
        print(f"Error general: {e}")
        return {"is_valid": False, "error": str(e)}
