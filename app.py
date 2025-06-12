# app.py

from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from mock_database import (
    save_document_entry, load_all_entries,
    load_signed_entries, load_pending_entries,
    update_document_as_signed, load_all_users
)
from azure_signer import sign_document_with_keyvault, calculate_document_hash
from verify_signature_with_keyvault import verify_signature_with_keyvault
from access_control import requires_level, ADMIN, COORDINADOR, OPERATIVO, EXTERNO
from blob_client import upload_file_to_blob
from cosmosdb_client import user_container, find_user_by_id
from azure.cosmos.exceptions import CosmosHttpResponseError
import base64
import datetime
import os
from auth import auth_bp



app = Flask(__name__)
app.secret_key = "clave_secreta"

app.register_blueprint(auth_bp)

# ----------------------------
# RUTAS PRINCIPALES
# ----------------------------

@app.route('/')
def home():
    return render_template("home.html")


@app.route('/subir', endpoint='index')
@requires_level(EXTERNO)
def subir():
    documents = load_all_entries()
    return render_template("index.html", documents=documents)


@app.route('/upload', methods=['POST'])
@requires_level(OPERATIVO)
def upload():
    file = request.files['document']
    action = request.form['action']
    category = request.form.get('category')
    visibility = request.form.get('visibility')

    if not file or not category or not visibility:
        flash("All fields are required.", "error")
        return redirect(url_for('index'))

    content = file.read()
    name = file.filename
    document_hash = calculate_document_hash(content)
    document_id = base64.urlsafe_b64encode(document_hash).decode()
    hash_b64 = base64.b64encode(document_hash).decode()

    # Subir a Azure Blob Storage
    file_info = upload_file_to_blob(file.stream, name, file.content_type)
    blob_name = file_info['stored_name'] 


    user = session.get('user')
    uploaded_by = user['email'] if user else 'anon'

    if action == "sign":
        result = sign_document_with_keyvault(content)
        save_document_entry(
            document_id=document_id,
            document_name=name,
            document_hash_base64=hash_b64,
            is_signed=True,
            uploaded_by=uploaded_by,
            blob_name=blob_name,
            signature_base64=result["signature_base64"],
            signed_by_key_id=result["signed_by_key_id"],
            signature_algorithm=result["signature_algorithm"],
            key_vault_url=result["key_vault_url"],
            key_name=result["key_name"],
            timestamp=datetime.datetime.utcnow().isoformat(),
            category=category,
            visibility=visibility,
            
        )
        flash("Document signed successfully.", "success")
    else:
        save_document_entry(
            document_id=document_id,
            document_name=name,
            document_hash_base64=hash_b64,
            is_signed=False,
            blob_name=blob_name,
            uploaded_by=uploaded_by,
            category=category,
            visibility=visibility,
            
        )
        flash("Document saved for later signing.", 'success')

    return redirect(url_for('index'))


@app.route('/verify', methods=['GET', 'POST'])
def verify():
    result = None
    error = None
    
    if request.method == 'POST':
        uploaded_file = request.files.get('document')
        signature_base64 = request.form.get('signature')

        if not uploaded_file:
            flash("No se ha subido ningún documento", "error")
            return render_template("verify.html", result=False)
            
        if not signature_base64:
            flash("No se ha proporcionado ninguna firma", "error")
            return render_template("verify.html", result=False)

        try:
            document_bytes = uploaded_file.read()
            # Limpiar la firma de posibles espacios o caracteres extra
            signature_base64 = signature_base64.strip()
            
            # Imprimir información de debug
            print(f"Longitud de la firma: {len(signature_base64)}")
            print(f"Primeros 50 caracteres de la firma: {signature_base64[:50]}")
            
            verification_result = verify_signature_with_keyvault(document_bytes, signature_base64)
            
            #if verification_result["is_valid"]:
            #    flash("¡La firma es válida!", "success")
            #else:
            #    flash(f"La firma no es válida: {verification_result.get('error', 'Error desconocido')}", "error")
                
            result = verification_result["is_valid"]
            
        except Exception as e:
            flash(f"Error al verificar la firma: {str(e)}", "error")
            result = False
            
    return render_template("verify.html", result=result)


@app.route('/signed')
def signed():
    user = session.get('user')
    all_documents = load_signed_entries()

    if user:
        nivel = user.get('nivel')
        email = user.get('email')

        if nivel in [3, 4]:
            documents = [doc for doc in all_documents if doc.get('visibility') != 'private']
        else:
            documents = all_documents
    else:
        # Usuario no autenticado: solo ver documentos públicos
        documents = [doc for doc in all_documents if doc.get('visibility') != 'private']

    return render_template("signed.html", documents=documents)


@app.route('/pending', methods=['GET', 'POST'])
@requires_level(OPERATIVO)
def pending():
    user = session.get('user')
    documents = load_pending_entries()

    if user['nivel'] == OPERATIVO:
        documents = [doc for doc in documents if doc.get('uploaded_by') == user['email']]

    if request.method == 'POST':
        selected_id = request.form['document_id']
        selected_doc = next((doc for doc in documents if doc['document_id'] == selected_id), None)
        if selected_doc:
            document_hash_bytes = base64.b64decode(selected_doc["document_hash_base64"])
            result = sign_document_with_keyvault(document_hash_bytes)
            update_document_as_signed(document_id=selected_id, signature_data=result)
            flash(f"Document {selected_id} signed successfully!")
            return redirect(url_for('pending'))

    return render_template("pending.html", documents=documents)


@app.route('/admin/update_user_level', methods=['POST'])
@requires_level(ADMIN)
def admin_update_user_level():
    try:
        user_id = request.form.get('user_id', '').strip()
        new_level_raw = int(request.form.get('new_level'))

        if not user_id or new_level_raw is None:
            flash("Datos incompletos en el formulario.", "error")
            return redirect(url_for('admin_users'))

        user = user_container.read_item(item=user_id, partition_key=user_id)

        current_email = session['user'].get('email')
        if current_email == user.get('email'):
            flash("No puedes modificar tu propio nivel de acceso.", "error")
            return redirect(url_for('admin_users'))

        user['nivel'] = new_level_raw
        user['id'] = user_id
        user['user_id'] = user_id

        user_container.upsert_item(user)
        flash("Nivel de acceso actualizado correctamente.", "success")

    except CosmosHttpResponseError as ce:
        flash(f"Error de Cosmos DB: {ce.message}", "error")

    except Exception as e:
        flash(f"Error inesperado: {str(e)}", "error")

    return redirect(url_for('admin_users'))


@app.route('/admin/users', endpoint='admin_users')
@requires_level(ADMIN)
def admin_users():
    users = load_all_users()
    return render_template("admin_users.html", users=users)

@app.route('/admin/delete_user', methods=['POST'])
@requires_level(ADMIN)
def admin_delete_user():
    user_id = request.form.get('user_id')

    if not user_id:
        flash("ID de usuario no válido.", "error")
        return redirect(url_for('admin_users'))

    try:
        user = user_container.read_item(item=user_id, partition_key=user_id)

        # Prevenir que el administrador se elimine a sí mismo
        if session['user'].get('email') == user.get('email'):
            flash("No puedes eliminar tu propia cuenta.", "error")
            return redirect(url_for('admin_users'))

        user_container.delete_item(item=user_id, partition_key=user_id)
        flash("Usuario eliminado exitosamente.", "success")

    except CosmosHttpResponseError as ce:
        flash(f"Error al eliminar: {ce.message}", "error")
    except Exception as e:
        flash(f"Ocurrió un error inesperado: {str(e)}", "error")

    return redirect(url_for('admin_users'))

@app.route('/download/<blob_name>')
@requires_level(EXTERNO)  # O el nivel que consideres apropiado
def download_file(blob_name):
    try:
        # Construir la ruta al archivo
        uploads_dir = os.path.join(app.root_path, 'static', 'uploads')
        return send_from_directory(
            uploads_dir,
            blob_name,
            as_attachment=True
        )
    except Exception as e:
        flash(f"Error al descargar el archivo: {str(e)}", "error")
        return redirect(url_for('signed'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
