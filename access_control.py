# access_control.py

from functools import wraps
from flask import session, redirect, url_for, flash

# Niveles de acceso
ADMIN = 1
COORDINADOR = 2
OPERATIVO = 3
EXTERNO = 4

def requires_level(min_level):
    """
    Decorador que restringe el acceso a usuarios con un nivel igual o menor al requerido.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = session.get('user')
            if not user:
                flash("Debes iniciar sesión.", "error")
                return redirect(url_for('auth.login'))

            user_level = user.get('nivel', EXTERNO)
            if user_level > min_level:
                flash("No tienes permisos para acceder a esta sección.", "error")
                return redirect(url_for('home'))

            return f(*args, **kwargs)
        return wrapper
    return decorator
