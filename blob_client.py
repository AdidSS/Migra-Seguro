# blob_client.py

from azure.storage.blob import BlobServiceClient
import uuid

# ⚠️ Reemplaza esta cadena por la que copiaste del portal de Azure
AZURE_CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=casamonarcaeastus;AccountKey=dRMSnuLkktVwwziFE9VrqNTQ/yxmXfEOEDWhyAIgLOCbV5/WmepiBQxVH+kgRMMKU+YM1pPLzWuv+AStTvctmQ==;EndpointSuffix=core.windows.net"
AZURE_CONTAINER_NAME = "documentos"

'''
def upload_file_to_blob(file_stream, filename, content_type):
    blob_service = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
    container_client = blob_service.get_container_client(AZURE_CONTAINER_NAME)

    # Verifica si el contenedor existe
    if not container_client.exists():
        container_client.create_container()

    blob_name = f"{filename}"
    container_client.upload_blob(
        name=blob_name,
        data=file_stream,
        content_type=content_type,
        overwrite=True  # Permite sobrescribir si el archivo ya existe
    )

    return blob_name
'''

# --------------------------

import os
import uuid
from werkzeug.utils import secure_filename

# Configuración
# Cambiar esta línea:
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}

# Crear carpeta si no existe
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_unique_filename(original_filename):
    """Genera un nombre de archivo único manteniendo la extensión original."""
    ext = os.path.splitext(original_filename)[1]
    return f"{uuid.uuid4()}{ext}"

def upload_file_to_blob(file_stream, filename, content_type):
    """
    Guarda el archivo con un nombre único pero mantiene el original para referencia.
    
    Returns:
        tuple: (nombre_unico, nombre_original)
    """
    if not allowed_file(filename):
        raise ValueError("Tipo de archivo no permitido")

    # Genera un nombre único para el archivo
    unique_filename = generate_unique_filename(filename)
    secure_name = secure_filename(unique_filename)
    
    # Construye la ruta completa
    file_path = os.path.join(UPLOAD_FOLDER, secure_name)
    
    try:
        # Guarda el archivo
        file_stream.seek(0)
        with open(file_path, 'wb') as f:
            f.write(file_stream.read())
        
        return {
            'stored_name': secure_name,
            'original_name': filename,
            'file_path': file_path
        }
        
    except Exception as e:
        print(f"Error guardando el archivo: {str(e)}")
        raise

def get_file_path(stored_name):
    """Obtiene la ruta completa de un archivo almacenado."""
    return os.path.join(UPLOAD_FOLDER, stored_name)