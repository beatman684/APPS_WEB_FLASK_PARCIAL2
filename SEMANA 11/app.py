import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session, g, jsonify
from functools import wraps
from datetime import datetime
import hashlib 
# IMPORTANTE: Asegúrate de que 'database.connection' y sus funciones (get_db, init_db) sean accesibles
from database.connection import get_db, init_db 

# --- Configuración de Flask ---
app = Flask(__name__)
# Usar una clave secreta segura es crucial en producción
app.config['SECRET_KEY'] = 'una_clave_secreta_muy_larga_y_segura_aqui_va_otra' 

# --------------------------------------------------------------------------
# --- FUNCIONES DE SEGURIDAD Y PERMISOS ---
# --------------------------------------------------------------------------

def hash_password_sha256(password, length=24):
    """Encripta la contraseña usando SHA256 y recorta el resultado a 24 caracteres."""
    hashed = hashlib.sha256(password.encode('utf-8')).hexdigest()
    return hashed[:length]

@app.before_request
def load_logged_in_user():
    """Carga el objeto del usuario en la variable global 'g' si hay una sesión activa."""
    user_email = session.get('email')

    if user_email is None:
        g.user = None
    else:
        db = get_db()
        # Nota: Asumo que la tabla se llama 'usuario'
        user_data = db.execute("SELECT id_usuario, email, nombre, role FROM usuario WHERE email = ?", (user_email,)).fetchone()
        db.close()
        
        if user_data:
            g.user = dict(user_data) 
        else:
            g.user = None
            session.pop('email', None)

def role_required(allowed_roles):
    """Restringe el acceso a una lista de roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if g.user is None:
                flash('Por favor, inicia sesión para acceder a esta página.', 'warning')
                return redirect(url_for('login', next=request.url))
                
            if g.user.get('role') not in allowed_roles:
                flash(f'Acceso denegado. Se requiere uno de los siguientes roles: {", ".join(allowed_roles)}', 'danger')
                return redirect(url_for('dashboard')) 
            return f(*args, **kwargs)
        return decorated_function
    return decorator

admin_required = role_required(['Administrador'])

def login_required(f):
    """Redirige al login si el usuario no tiene una sesión activa. (CORREGIDO)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            flash('Por favor, inicia sesión para acceder a esta página.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function # <-- CORRECCIÓN: DEBE DEVOLVER decorated_function

# --------------------------------------------------------------------------
# --- Rutas de Autenticación y Generales ---
# --------------------------------------------------------------------------

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
        
        password_attempt_hash = hash_password_sha256(password) 
        
        if user and user['password_hash'] == password_attempt_hash: 
            session['email'] = user['email']
            flash(f'¡Bienvenido, {email.split("@")[0].capitalize()}!', 'success')
            
            next_url = request.args.get('next')
            return redirect(next_url or url_for('dashboard'))
        else:
            flash('Email o contraseña incorrectos.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('email', None) 
    flash('Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('login'))

@app.route('/')
@app.route('/dashboard')
@login_required 
def dashboard():
    return render_template('dashboard.html')

# --------------------------------------------------------------------------
# --- MÓDULO: REALIZAR VENTA (PUNTO DE VENTA) ---
# --------------------------------------------------------------------------

@app.route('/punto_de_venta')
@role_required(['Administrador', 'Vendedor']) 
def punto_de_venta():
    """Ruta principal para la interfaz de Punto de Venta (POS)."""
    return render_template('ventas/punto_de_venta.html') 

@app.route('/api/buscar_productos', methods=['GET'])
@role_required(['Administrador', 'Vendedor']) 
def buscar_productos_api():
    """API que busca productos por código o nombre y devuelve los resultados en JSON."""
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify([])

    search_term = '%' + query + '%'
    
    try:
        db = get_db()
        productos = db.execute(
            """
            SELECT 
                id_producto, codigo_producto, nombre_producto, precio_venta, stock_actual
            FROM productos 
            WHERE codigo_producto LIKE ? OR nombre_producto LIKE ? 
            LIMIT 10
            """,
            (search_term, search_term)
        ).fetchall()
        
        db.close()
        
        resultados = [
            {
                'id': p['id_producto'],
                'codigo': p['codigo_producto'],
                'nombre': p['nombre_producto'],
                'precio': p['precio_venta'],
                'stock': p['stock_actual']
            } 
            for p in productos
        ]
        
        return jsonify(resultados)
        
    except sqlite3.Error as e:
        print(f"Error de base de datos en búsqueda: {e}")
        return jsonify([]), 500

@app.route('/api/finalizar_venta', methods=['POST'])
@role_required(['Administrador', 'Vendedor']) 
def finalizar_venta():
    """Recibe los datos del carrito, registra la venta, el detalle y actualiza el stock."""
    db = None
    try:
        data = request.get_json()
        carrito = data.get('carrito')
        total_venta_str = data.get('total') 
        cedula_cliente = data.get('cedula_cliente', '9999999999') 
        
        if not carrito or not total_venta_str:
            return jsonify({'success': False, 'message': 'Datos de venta incompletos.'}), 400

        # CRÍTICO: Conversión de string a float (Soluciona el error de formato)
        try:
            total_venta = float(total_venta_str)
        except ValueError:
            return jsonify({'success': False, 'message': 'El total de la venta no es un número válido.'}), 400

        db = get_db()
        
        # 1. Registrar la Venta Maestra (Tabla 'ventas')
        id_empleado = g.user['id_usuario']
        id_local = 1 # Asumo un valor por defecto o base
        estado_venta = 'completada'

        result = db.execute(
            """
            INSERT INTO ventas (
                cedula_cliente, id_empleado, id_local, fecha_venta, total, estado,
                periodo_pago, metodo_pago
            )
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?, ?, 'Contado', 'Efectivo')
            """,
            (cedula_cliente, id_empleado, id_local, total_venta, estado_venta)
        )
        id_venta = result.lastrowid
        
        # 2. Registrar el Detalle de Venta y Actualizar Stock
        for item in carrito:
            id_producto = item['id']
            cantidad = item['cantidad']
            precio_unitario = item['precio']
            subtotal_item = item['subtotal']
            
            try:
                cantidad = int(cantidad)
                precio_unitario = float(precio_unitario)
                subtotal_item = float(subtotal_item)
            except ValueError:
                raise Exception("Error en el formato numérico de los ítems del carrito.")
            
            db.execute(
                """
                INSERT INTO detalle_venta (id_venta, id_producto, cantidad, precio_unitario, subtotal)
                VALUES (?, ?, ?, ?, ?)
                """,
                (id_venta, id_producto, cantidad, precio_unitario, subtotal_item)
            )
            
            # CRÍTICO: Descontar stock
            db.execute(
                """
                UPDATE productos SET stock_actual = stock_actual - ? WHERE id_producto = ?
                """,
                (cantidad, id_producto)
            )

        db.commit()
        
        # CRÍTICO: Usamos el total_venta (float) en el mensaje flash
        flash(f'Nota de Venta #{id_venta} registrada exitosamente. Total: ${total_venta:.2f}', 'success')
        return jsonify({'success': True, 'id_venta': id_venta})

    except sqlite3.Error as e:
        if db: db.rollback() 
        print(f"Error de base de datos en finalizar_venta: {e}")
        return jsonify({'success': False, 'message': f'Error de base de datos: {e}'}), 500
    except Exception as e:
        if db: db.rollback()
        print(f"Error desconocido al finalizar la venta: {e}")
        return jsonify({'success': False, 'message': f'Error desconocido: {e}'}), 500
    finally:
        if db: db.close()

# --------------------------------------------------------------------------
# --- MÓDULO: VER HISTORIAL DE VENTAS ---
# --------------------------------------------------------------------------

@app.route('/historial_ventas')
@role_required(['Administrador', 'Vendedor']) 
def ver_historial_ventas():
    ventas = []
    try:
        db = get_db()
        ventas = db.execute(
            """
            SELECT 
                v.id_venta, v.fecha_venta, v.total, v.estado, 
                COALESCE(c.nombres || ' ' || c.apellidos, 'Público General') AS nombre_cliente,
                u.nombre AS nombre_empleado
            FROM ventas v
            LEFT JOIN clientes c ON v.cedula_cliente = c.cedula
            JOIN usuario u ON v.id_empleado = u.id_usuario
            ORDER BY v.fecha_venta DESC
            """
        ).fetchall()
        db.close()
    except sqlite3.Error as e:
        flash(f'Error al cargar el historial de ventas: {e}', 'danger')

    return render_template('ventas/historial.html', ventas=ventas, user_role=g.user.get('role'))

@app.route('/ventas/detalle/<int:id_venta>')
@role_required(['Administrador', 'Vendedor']) 
def ver_detalle_venta(id_venta):
    # Lógica para cargar el detalle de la venta (pendiente de implementar)
    flash("Esta ruta requiere la lógica para cargar el detalle de la venta #{}".format(id_venta), 'info')
    return redirect(url_for('ver_historial_ventas')) 
    
# --------------------------------------------------------------------------
# --- MÓDULO: ADMINISTRAR PRODUCTOS (CRUD COMPLETO Y CORREGIDO) ---
# --------------------------------------------------------------------------

@app.route('/productos')
@role_required(['Administrador', 'Vendedor']) 
def listar_productos():
    """Ruta unificada que funciona como Catálogo (Vendedor) y Listado (Admin)."""
    
    PRODUCTO_COLUMNS_SQL_ADMIN = """
        p.id_producto, p.codigo_producto, p.nombre_producto, p.descripcion, p.precio_compra,
        p.precio_venta, p.stock_actual, p.stock_minimo, p.material, p.tipo_rosca, p.medida,
        p.unidad_medida,
        prov.nombre_empresa AS nombre_proveedor, c.nombre_categoria
    """
    
    PRODUCTO_COLUMNS_SQL_VENDEDOR = """
        p.id_producto, p.codigo_producto, p.nombre_producto, 
        p.precio_venta, p.stock_actual
    """

    user_role = g.user.get('role', 'Vendedor') 
    
    if user_role == 'Administrador':
        select_cols = PRODUCTO_COLUMNS_SQL_ADMIN
        from_table = "productos p LEFT JOIN proveedores prov ON p.id_proveedor = prov.id_proveedor LEFT JOIN categorias c ON p.id_categoria = c.id_categoria"
    else: # Vendedor
        select_cols = PRODUCTO_COLUMNS_SQL_VENDEDOR
        from_table = "productos p"
    
    query = request.args.get('q', '').strip() 
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
    per_page = 10
    offset = (page - 1) * per_page
    
    productos = []
    total_productos = 0
    
    try:
        db = get_db()
        params = []
        if query:
            search_pattern = f'%{query}%'
            sql_productos = f"""
                SELECT {select_cols} FROM {from_table}
                WHERE p.nombre_producto LIKE ? OR p.codigo_producto LIKE ? 
                LIMIT ? OFFSET ?
            """
            params = (search_pattern, search_pattern, per_page, offset)
            
            sql_count = "SELECT COUNT(*) FROM productos WHERE nombre_producto LIKE ? OR codigo_producto LIKE ?"
            total_productos = db.execute(sql_count, (search_pattern, search_pattern)).fetchone()[0]
        else:
            sql_productos = f"SELECT {select_cols} FROM {from_table} LIMIT ? OFFSET ?"
            params = (per_page, offset)
            
            sql_count = "SELECT COUNT(*) FROM productos"
            total_productos = db.execute(sql_count).fetchone()[0]
            
        productos = db.execute(sql_productos, params).fetchall()
        db.close()
        
        total_pages = (total_productos + per_page - 1) // per_page 

        return render_template('productos/lista.html', 
                               productos=productos,
                               query=query,
                               page=page,
                               total_pages=total_pages,
                               total_productos=total_productos,
                               user_role=user_role)
                               
    except sqlite3.Error as e:
        flash(f'Error al cargar productos: {e}', 'danger')
        print(f"DEBUG SQLITE ERROR: {e}") 
        return redirect(url_for('dashboard'))


@app.route('/productos/agregar', methods=['GET', 'POST'])
@admin_required 
def agregar_producto():
    db = None
    categorias = []
    proveedores = []
    
    try:
        db = get_db()
        categorias = db.execute("SELECT id_categoria, nombre_categoria FROM categorias").fetchall()
        proveedores = db.execute("SELECT id_proveedor, nombre_empresa FROM proveedores").fetchall()
    except sqlite3.Error as e:
        flash(f'Error al cargar datos auxiliares (Categorías/Proveedores): {e}', 'danger')
        return redirect(url_for('listar_productos'))
    finally:
        if db: db.close()


    if request.method == 'POST':
        # 1. OBTENER Y SANEAR DATOS
        codigo = request.form.get('codigo_producto', '').strip().upper() 
        nombre = request.form.get('nombre_producto')
        descripcion = request.form.get('descripcion', '') 
        precio_compra = request.form.get('precio_compra')
        precio_venta = request.form.get('precio_venta')
        stock_actual = request.form.get('stock_actual')
        stock_minimo = request.form.get('stock_minimo', 10)
        id_categoria = request.form.get('id_categoria')
        id_proveedor = request.form.get('id_proveedor')
        
        # --- CAMPOS ESPECÍFICOS REQUERIDOS POR TU DB ---
        material = request.form.get('material', '').strip() 
        tipo_rosca = request.form.get('tipo_rosca', '').strip()
        medida = request.form.get('medida', '').strip()
        unidad_medida = request.form.get('unidad_medida', '').strip()
        # --- FIN CAMPOS ESPECÍFICOS ---

        
        # 2. VALIDACIÓN DE CAMPOS OBLIGATORIOS (TODOS)
        campos_obligatorios = [
            codigo, nombre, precio_venta, stock_actual, id_categoria, id_proveedor, 
            material, tipo_rosca, medida, unidad_medida, precio_compra
        ]
        
        if not all(campos_obligatorios):
            flash('Faltan datos obligatorios para el producto. (Asegúrese de rellenar Código, Nombre, Precios, Stock, Categoría, Proveedor, Material, Tipo de Rosca, Medida y Unidad Base)', 'danger')
            return render_template('productos/agregar.html', 
                                   categorias=categorias, 
                                   proveedores=proveedores,
                                   form_data=request.form)

        # 3. VERIFICACIÓN EXPLÍCITA DE CÓDIGO ÚNICO
        try:
            db = get_db()
            
            producto_existente = db.execute(
                "SELECT id_producto FROM productos WHERE codigo_producto = ?", 
                (codigo,)
            ).fetchone()

            if producto_existente:
                flash(f'Error: El código de producto "{codigo}" ya existe.', 'danger')
                return render_template('productos/agregar.html', 
                                       categorias=categorias, 
                                       proveedores=proveedores,
                                       form_data=request.form) 

            # 4. INSERCIÓN DEL PRODUCTO
            db.execute(
                """
                INSERT INTO productos (
                    codigo_producto, nombre_producto, descripcion, material, tipo_rosca, medida,
                    unidad_medida, precio_compra, precio_venta, stock_actual, stock_minimo, 
                    id_proveedor, id_categoria)  
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (codigo, nombre, descripcion, material, tipo_rosca, medida,
                 unidad_medida, precio_compra, precio_venta, stock_actual, stock_minimo, 
                 id_proveedor, id_categoria)
            )
            db.commit()
            flash(f'Producto {nombre} agregado exitosamente.', 'success')
            return redirect(url_for('listar_productos'))
        
        except sqlite3.Error as e:
            flash(f'Error al guardar el producto: {e}', 'danger')
            return render_template('productos/agregar.html', 
                                   categorias=categorias, 
                                   proveedores=proveedores,
                                   form_data=request.form)
        finally:
             if db: db.close()
        
    # --- RENDERIZACIÓN (Método GET) ---
    return render_template('productos/agregar.html', categorias=categorias, proveedores=proveedores)


@app.route('/productos/editar/<int:id_producto>', methods=['GET', 'POST'])
@admin_required 
def editar_producto(id_producto):
    db = None
    producto = None
    categorias = []
    proveedores = []
    
    # Intenta obtener la conexión y los datos iniciales
    try:
        db = get_db()
        categorias = db.execute("SELECT id_categoria, nombre_categoria FROM categorias").fetchall()
        proveedores = db.execute("SELECT id_proveedor, nombre_empresa FROM proveedores").fetchall()

        producto = db.execute(
            """
            SELECT id_producto, codigo_producto, nombre_producto, descripcion, precio_compra,
                   precio_venta, stock_actual, stock_minimo, id_categoria, id_proveedor, 
                   unidad_medida, material, medida, tipo_rosca
            FROM productos 
            WHERE id_producto = ?
            """,
            (id_producto,)
        ).fetchone()

        if producto is None:
            flash(f'Producto con ID {id_producto} no encontrado.', 'danger')
            return redirect(url_for('listar_productos'))
            
    except sqlite3.Error as e:
        flash(f'Error al cargar datos para edición: {e}', 'danger')
        return redirect(url_for('listar_productos'))
    finally:
         if db: db.close() # Cierra después de la carga inicial

    # --- PROCESAMIENTO POST (Guardar Cambios) ---
    if request.method == 'POST':
        # 1. OBTENER Y SANEAR DATOS
        codigo = request.form.get('codigo_producto', '').strip().upper()
        nombre = request.form.get('nombre_producto')
        descripcion = request.form.get('descripcion', '')
        precio_compra = request.form.get('precio_compra')
        precio_venta = request.form.get('precio_venta')
        stock_actual = request.form.get('stock_actual')
        stock_minimo = request.form.get('stock_minimo', 10)
        id_categoria = request.form.get('id_categoria')
        id_proveedor = request.form.get('id_proveedor')
        
        # --- CAMPOS ESPECÍFICOS REQUERIDOS POR TU DB ---
        material = request.form.get('material', '').strip() 
        tipo_rosca = request.form.get('tipo_rosca', '').strip()
        medida = request.form.get('medida', '').strip()
        unidad_medida = request.form.get('unidad_medida', '').strip()
        # --- FIN CAMPOS ESPECÍFICOS ---

        # 2. VALIDACIÓN DE CAMPOS OBLIGATORIOS (TODOS)
        campos_obligatorios = [
            codigo, nombre, precio_venta, stock_actual, id_categoria, id_proveedor, 
            material, tipo_rosca, medida, unidad_medida, precio_compra
        ]

        if not all(campos_obligatorios):
            flash('Faltan datos obligatorios para el producto. (Asegúrese de rellenar Material, Tipo de Rosca, Medida y Unidad Base)', 'danger')
            return render_template('productos/editar.html', 
                                   producto=producto, 
                                   categorias=categorias, 
                                   proveedores=proveedores, 
                                   form_data=request.form)

        try:
            db = get_db()
            # 3. VERIFICAR UNICIDAD DEL CÓDIGO
            producto_existente = db.execute(
                "SELECT id_producto FROM productos WHERE codigo_producto = ? AND id_producto != ?",
                (codigo, id_producto)
            ).fetchone()

            if producto_existente:
                flash(f'Error: El código de producto "{codigo}" ya existe en otro producto.', 'danger')
            else:
                # 4. Actualizar la base de datos (TODOS LOS CAMPOS DE LA TABLA)
                db.execute(
                    """
                    UPDATE productos 
                    SET codigo_producto=?, nombre_producto=?, descripcion=?, material=?, 
                        tipo_rosca=?, medida=?, unidad_medida=?, precio_compra=?, 
                        precio_venta=?, stock_actual=?, stock_minimo=?, id_proveedor=?, 
                        id_categoria=?
                    WHERE id_producto=?
                    """,
                    (codigo, nombre, descripcion, material, tipo_rosca, medida, 
                     unidad_medida, precio_compra, precio_venta, stock_actual, stock_minimo, 
                     id_proveedor, id_categoria, id_producto)
                )
                db.commit()
                flash(f'Producto "{nombre}" actualizado exitosamente.', 'success')
                return redirect(url_for('listar_productos'))
            
        except sqlite3.Error as e:
            flash(f'Error al guardar el producto: {e}', 'danger')
        finally:
            if db: db.close()
            
    # --- RENDERIZACIÓN (GET o POST fallido) ---
    return render_template('productos/editar.html', 
                           producto=producto, 
                           categorias=categorias, 
                           proveedores=proveedores,
                           form_data=request.form if request.method == 'POST' else None)


@app.route('/productos/eliminar/<int:id_producto>', methods=['POST'])
@admin_required 
def eliminar_producto(id_producto):
    try:
        db = get_db()
        db.execute("DELETE FROM productos WHERE id_producto = ?", (id_producto,))
        db.commit()
        db.close()
        flash('Producto eliminado correctamente.', 'info')
    except sqlite3.IntegrityError:
        flash('Error: No se puede eliminar el producto porque tiene ventas o registros asociados.', 'danger')
    except sqlite3.Error as e:
        flash(f'Error al eliminar el producto: {e}.', 'danger')
        
    return redirect(url_for('listar_productos'))

# --------------------------------------------------------------------------
# --- MÓDULO: ADMINISTRAR USUARIOS Y PERMISOS (ADMIN ONLY) ---
# --------------------------------------------------------------------------

@app.route('/usuarios')
@admin_required 
def listar_usuarios():
    usuarios = []
    try:
        db = get_db()
        usuarios = db.execute("SELECT id_usuario, email, nombre, role FROM usuario").fetchall()
        db.close()
    except sqlite3.Error as e:
        flash(f'Error al cargar usuarios: {e}', 'danger')
        
    return render_template('usuarios/lista.html', usuarios=usuarios, user_role=g.user.get('role'))

@app.route('/usuarios/agregar', methods=['GET', 'POST'])
@admin_required
def agregar_usuario():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        nombre = request.form['nombre']
        role = request.form['role']
        
        if not all([email, password, nombre, role]):
            flash('Todos los campos son obligatorios.', 'danger')
            return render_template('usuarios/agregar.html')
            
        db = None 
        try:
            db = get_db()
            existing_user = db.execute("SELECT id_usuario FROM usuario WHERE email = ?", (email,)).fetchone()
            if existing_user:
                flash('El email ya está registrado.', 'warning')
                return render_template('usuarios/agregar.html')

            password_hash = hash_password_sha256(password)
            
            db.execute(
                "INSERT INTO usuario (email, password_hash, nombre, role) VALUES (?, ?, ?, ?)",
                (email, password_hash, nombre, role)
            )
            db.commit()
            flash(f'Usuario {nombre} ({role}) agregado exitosamente. Contraseña encriptada.', 'success')
            return redirect(url_for('listar_usuarios'))
            
        except sqlite3.Error as e:
            flash(f'Error al agregar usuario: {e}', 'danger')
            return render_template('usuarios/agregar.html')
        finally:
            if db:
                db.close()
            
    roles = ['Administrador', 'Vendedor']
    return render_template('usuarios/agregar.html', roles=roles)


@app.route('/usuarios/eliminar/<int:id_usuario>', methods=['POST'])
@admin_required
def eliminar_usuario(id_usuario):
    if g.user['id_usuario'] == id_usuario:
        flash('No puedes eliminar tu propia cuenta de Administrador mientras está activa.', 'danger')
        return redirect(url_for('listar_usuarios'))
        
    try:
        db = get_db()
        db.execute("DELETE FROM usuario WHERE id_usuario = ?", (id_usuario,))
        db.commit()
        db.close()
        flash('Usuario eliminado correctamente.', 'info')
            
    except sqlite3.Error as e:
        flash(f'Error al eliminar el usuario: {e}.', 'danger')
        
    return redirect(url_for('listar_usuarios'))

# --------------------------------------------------------------------------
# --- MÓDULO: GENERAR REPORTES Y ANÁLISIS (ADMIN ONLY) ---
# --------------------------------------------------------------------------

@app.route('/reportes')
@admin_required
def generar_reportes():
    flash("Módulo de Reportes. Implementar lógica de extracción de datos y gráficos aquí.", 'info')
    return render_template('reportes/index.html')

# --------------------------------------------------------------------------
# --- MÓDULO: PROVEEDORES (COMPLETO) ---
# --------------------------------------------------------------------------

@app.route('/proveedores')
@role_required(['Administrador', 'Vendedor']) 
def listar_proveedores():
    """Muestra la lista de proveedores con paginación."""
    
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
        
    per_page = 10
    offset = (page - 1) * per_page
    
    proveedores = []
    total_proveedores = 0
    total_pages = 0
    
    try:
        db = get_db()
        
        sql_count = "SELECT COUNT(*) FROM proveedores"
        total_proveedores = db.execute(sql_count).fetchone()[0]
        
        total_pages = (total_proveedores + per_page - 1) // per_page 

        sql_proveedores = "SELECT * FROM proveedores LIMIT ? OFFSET ?"
        proveedores = db.execute(sql_proveedores, (per_page, offset)).fetchall()
        
        db.close()
        
    except sqlite3.Error as e:
        flash(f'Error al cargar proveedores: {e}', 'danger')
        return redirect(url_for('dashboard')) 
        
    return render_template('proveedores/lista.html', 
                           proveedores=proveedores, 
                           user_role=g.user.get('role'),
                           page=page,  
                           total_pages=total_pages, 
                           total_proveedores=total_proveedores)


@app.route('/proveedores/agregar', methods=['GET', 'POST'])
@admin_required 
def agregar_proveedor():
    if request.method == 'POST':
        ruc = request.form.get('ruc')
        nombre_empresa = request.form.get('nombre_empresa')
        contacto = request.form.get('contacto')
        telefono = request.form.get('telefono')
        email = request.form.get('email')
        direccion = request.form.get('direccion')
        
        if not all([ruc, nombre_empresa, contacto, telefono]):
            flash('RUC, Nombre, Contacto y Teléfono de la empresa son obligatorios.', 'danger')
            return render_template('proveedores/agregar.html', form_data=request.form) 
            
        db = None
        try:
            db = get_db()
            db.execute(
                """
                INSERT INTO proveedores (ruc, nombre_empresa, contacto, telefono, email, direccion, fecha_registro)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (ruc, nombre_empresa, contacto, telefono, email, direccion)
            )
            db.commit()
            flash(f'Proveedor "{nombre_empresa}" agregado exitosamente.', 'success')
            return redirect(url_for('listar_proveedores'))
            
        except sqlite3.IntegrityError:
            flash(f'Error: El RUC "{ruc}" ya existe.', 'danger')
            return render_template('proveedores/agregar.html', form_data=request.form)
        except sqlite3.Error as e:
            flash(f'Error al guardar el proveedor: {e}', 'danger')
            return render_template('proveedores/agregar.html', form_data=request.form) 
        finally:
            if db:
                db.close()

    return render_template('proveedores/agregar.html')


@app.route('/proveedores/editar/<int:id_proveedor>', methods=['GET', 'POST'])
@admin_required 
def editar_proveedor(id_proveedor):
    flash(f"Ruta de Edición de Proveedor ID: {id_proveedor}. Requiere la lógica de carga y guardado.", 'warning')
    return redirect(url_for('listar_proveedores'))

@app.route('/proveedores/eliminar/<int:id_proveedor>', methods=['POST'])
@admin_required 
def eliminar_proveedor(id_proveedor):
    """Elimina un proveedor de la base de datos."""
    try:
        db = get_db()
        db.execute("DELETE FROM proveedores WHERE id_proveedor = ?", (id_proveedor,))
        db.commit()
        db.close()
        flash('Proveedor eliminado correctamente.', 'info')
    except sqlite3.IntegrityError:
        flash('Error: No se puede eliminar el proveedor porque tiene productos asociados.', 'danger')
    except sqlite3.Error as e:
        flash(f'Error al eliminar el proveedor: {e}.', 'danger')
        
    return redirect(url_for('listar_proveedores'))

# --------------------------------------------------------------------------
# --- INICIALIZACIÓN DE LA APLICACIÓN (CORREGIDO) ---
# --------------------------------------------------------------------------

if __name__ == '__main__':
    # Si quieres inicializar la base de datos al inicio, puedes descomentar la línea de abajo.
    # init_db() 
    
    # Inicia el servidor Flask
    app.run(debug=True)