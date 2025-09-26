import sqlite3
import os

# Define la ruta de la base de datos
DATABASE = os.path.join(os.path.dirname(__file__), 'pernotodo.db')

def get_db():
    """Establece la conexión a la base de datos y configura row_factory."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row 
    return conn

def init_db():
    """Crea tablas si no existen, añade columnas faltantes (ALTER TABLE) y garantiza la integridad de los datos."""
    db = get_db()
    cursor = db.cursor()
    
    # 1. Asegurar que la tabla de productos existe
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id_producto INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_producto VARCHAR(20) NOT NULL UNIQUE,
            nombre_producto VARCHAR(150) NOT NULL,
            descripcion TEXT,
            material VARCHAR(50) NOT NULL,
            tipo_rosca VARCHAR(30),
            medida VARCHAR(20) NOT NULL,
            unidad_medida VARCHAR(10) DEFAULT 'unidad',
            precio_compra DECIMAL(10,2) NOT NULL,
            precio_venta DECIMAL(10,2) NOT NULL,
            stock_actual INTEGER DEFAULT 0,
            stock_minimo INTEGER DEFAULT 10,
            id_proveedor INTEGER,
            id_categoria INTEGER,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_proveedor) REFERENCES proveedores(id_proveedor),
            FOREIGN KEY (id_categoria) REFERENCES categorias(id_categoria)
        );
    """)
    
    # 2. Inicializar la tabla usuario si NO existe (basado en el error, asumimos que tenía 'password')
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuario (
            id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL -- Asumimos que esta columna es la que causa el error NOT NULL
        );
    """)

    # 3. MIGRACIÓN DE ESQUEMA (Añadir columnas sin perder datos)
    
    try:
        # Añade la columna 'password_hash' (si no existe)
        cursor.execute("ALTER TABLE usuario ADD COLUMN password_hash TEXT")
    except sqlite3.OperationalError:
        pass 
    
    try:
        # Añade la columna 'nombre' (si no existe)
        cursor.execute("ALTER TABLE usuario ADD COLUMN nombre VARCHAR(100) DEFAULT 'Usuario'")
    except sqlite3.OperationalError:
        pass
    
    try:
        # Añade la columna 'role' (si no existe)
        cursor.execute("ALTER TABLE usuario ADD COLUMN role VARCHAR(20) DEFAULT 'Vendedor'")
    except sqlite3.OperationalError:
        pass
    
    db.commit()

    # 4. Insertar usuarios de prueba (SOLUCIÓN AL INTEGRITY ERROR)
    # Ahora el INSERT incluye la columna 'password' (la quinta ?) para cumplir con la restricción NOT NULL.
    
    INSERT_QUERY = "INSERT INTO usuario (email, password_hash, nombre, role, password) VALUES (?, ?, ?, ?, ?)"
    
    # Usuario Administrador
    cursor.execute("SELECT id_usuario FROM usuario WHERE email = 'admin@pernotodo.com'")
    if cursor.fetchone() is None:
        # Usamos '12345' para password_hash Y para la columna antigua 'password'
        cursor.execute(INSERT_QUERY, 
                       ('admin@pernotodo.com', '12345', 'Juan Administrador', 'Administrador', '12345'))
    
    # Usuario Vendedor
    cursor.execute("SELECT id_usuario FROM usuario WHERE email = 'vendedor@pernotodo.com'")
    if cursor.fetchone() is None:
        cursor.execute(INSERT_QUERY, 
                       ('vendedor@pernotodo.com', '12345', 'Maria Vendedora', 'Vendedor', '12345'))
        
    db.commit()
    db.close()

if __name__ == '__main__':
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    init_db()
    print("Base de datos 'pernotodo.db' inicializada y tablas actualizadas.")