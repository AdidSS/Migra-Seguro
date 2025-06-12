# auth.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from cosmosdb_client import user_container, find_user_by_id

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = find_user_by_id(email)
        if not user or not check_password_hash(user.get('password_hash'), password):
            flash("Credenciales incorrectas.", "error")
            return redirect(url_for('auth.login'))

        session['user'] = {
            "email": user.get("email"),
            "username": user.get("username"),
            "nivel": user.get("nivel", 4)
        }
        return redirect(url_for('home'))

    return render_template("login.html")


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')

        if password != confirm:
            flash("Las contraseñas no coinciden.", "error")
            return redirect(url_for('auth.register'))

        # Verifica si ya existe
        if find_user_by_id(email):
            flash("Ese usuario ya existe.", "error")
            return redirect(url_for('auth.register'))

        user = {
            "id": email,
            "user_id": email,
            "username": username,
            "email": email,
            "password_hash": generate_password_hash(password),
            "nivel": 4  # Por defecto Externo
        }

        user_container.upsert_item(user)
        flash("Cuenta creada exitosamente. Ahora puedes iniciar sesión.", "success")
        return redirect(url_for('auth.login'))

    return render_template("register.html")


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.", "success")
    return redirect(url_for('auth.login'))
