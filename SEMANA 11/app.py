import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from functools import wraps
from database.connection import get_db, init_db 

# --- Configuración de Flask ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'una_clave_secreta_muy_larga_y_segura_aqui_va_otra' 

# --- Hook: Cargar Usuario Antes de la Solicitud ---
@app.before_request
def load_logged_in_user():
    """Carga el objeto del usuario en la variable global 'g' si hay una sesión activa."""
    user_email = session.get('email')

    if user_email is None:
        g.user = None
    else:
        db = get_db()
        # Selecciona todos los campos necesarios
        user_data = db.execute("SELECT id_usuario, email, nombre, role FROM usuario WHERE email = ?", (user_email,)).fetchone()
        db.close()
        
        # Convierte sqlite3.Row a un objeto simple si lo deseas, o usa el objeto Row directamente
        if user_data:
            # Creamos un objeto simple (diccionario) para facilidad de uso en plantillas
            g.user = dict(user_data) 
        else:
            g.user = None
            session.pop('email', None) # Limpiar sesión si el usuario no existe

# --- Decorador de Seguridad ---
def login_required(f):
    """Redirige al login si el usuario no tiene una sesión activa."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None: # Usamos g.user para verificar la sesión
            flash('Por favor, inicia sesión para acceder a esta página.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# --- Rutas de Autenticación ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user is not None:
         return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        db = get_db()
        user = db.execute("SELECT email, password_hash FROM usuario WHERE email = ?", (email,)).fetchone()
        db.close()
        
        if user and user['password_hash'] == password: # Validación
            session['email'] = user['email']
            flash(f'¡Bienvenido, {email.split("@")[0].capitalize()}!', 'success')
            
            next_url = request.args.get('next')
            return redirect(next_url or url_for('dashboard'))
        else:
            flash('Email o contraseña incorrectos.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    """Cierra la sesión del usuario."""
    session.pop('email', None) 
    flash('Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('login'))

# --- Rutas Protegidas ---

@app.route('/')
@app.route('/dashboard')
@login_required 
def dashboard():
    # g.user ya tiene la información del usuario cargada
    return render_template('dashboard.html')

@app.route('/productos')
@login_required 
def listar_productos():
    try:
        db = get_db()
        productos = db.execute('SELECT * FROM productos').fetchall()
        db.close()
        return render_template('productos/lista.html', productos=productos)
    except sqlite3.Error as e:
        flash(f'Error al cargar productos: {e}', 'danger')
        return redirect(url_for('dashboard'))

# --- Función Principal ---
if __name__ == '__main__':
    # Inicializa la base de datos al arrancar la app
    init_db()
    app.run(debug=True)