import sqlite3
import os
from pathlib import Path

def get_db_connection():
    """
    Establece y retorna una conexión a la base de datos SQLite
    """
    try:
        # Asegurarnos de que la carpeta database existe
        db_dir = Path(__file__).resolve().parent
        db_path = db_dir / 'inventario.db'

        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row  # Esto permite acceso por nombre de columna
        print("Conexión a SQLite establecida correctamente")
        return connection

    except Exception as e:
        print(f"Error al conectar a SQLite: {e}")
        return None

def init_db():
    """
    Inicializa la base de datos con las tablas necesarias
    """
    connection = get_db_connection()
    if connection is None:
        print("No se pudo conectar a la base de datos")
        return

    try:
        cursor = connection.cursor()

        # Primero crear las tablas básicas
        print("Creando tablas...")
        
        # Tabla de proveedores
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS proveedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre VARCHAR(100) NOT NULL,
                contacto VARCHAR(100),
                telefono VARCHAR(20),
                email VARCHAR(100),
                direccion TEXT,
                ruc VARCHAR(20) UNIQUE,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✓ Tabla 'proveedores' creada")

        # Tabla de productos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo VARCHAR(50) UNIQUE NOT NULL,
                nombre VARCHAR(100) NOT NULL,
                descripcion TEXT,
                categoria VARCHAR(50) NOT NULL,
                precio_compra DECIMAL(10,2) NOT NULL,
                precio_venta DECIMAL(10,2) NOT NULL,
                stock INTEGER NOT NULL DEFAULT 0,
                stock_minimo INTEGER NOT NULL DEFAULT 10,
                unidad_medida VARCHAR(20) NOT NULL DEFAULT 'unidad',
                proveedor_id INTEGER,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (proveedor_id) REFERENCES proveedores(id)
            )
        ''')
        print("✓ Tabla 'productos' creada")

        # Insertar datos de prueba en proveedores
        print("Insertando datos de prueba...")
        cursor.executemany('''
            INSERT OR IGNORE INTO proveedores 
            (nombre, contacto, telefono, email, direccion, ruc) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', [
            ('Pernos Industriales S.A.', 'Juan Pérez', '0987654321', 'ventas@pernosindustriales.com', 'Av. Industrial 123', '1234567890123'),
            ('Tornillería Nacional', 'María García', '0976543210', 'info@tornillerianacional.com', 'Calle Comercial 456', '9876543210987')
        ])
        print("✓ Datos de proveedores insertados")

        # Insertar datos de prueba en productos
        cursor.executemany('''
            INSERT OR IGNORE INTO productos 
            (codigo, nombre, descripcion, categoria, precio_compra, precio_venta, stock, stock_minimo, unidad_medida, proveedor_id) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', [
            ('PER-001', 'Perno hexagonal grado 5', 'Perno hexagonal de 1/2 pulgada, grado 5', 'Pernos', 0.50, 1.20, 100, 20, 'unidad', 1),
            ('PER-002', 'Perno hexagonal grado 8', 'Perno hexagonal de 3/4 pulgada, grado 8', 'Pernos', 0.80, 1.80, 75, 15, 'unidad', 1),
            ('TOR-001', 'Tornillo autorroscante #8', 'Tornillo autorroscante para madera, #8 x 1-1/2"', 'Tornillos', 0.30, 0.75, 200, 50, 'unidad', 2),
            ('TUE-001', 'Tuerca hexagonal grado 5', 'Tuerca hexagonal para perno de 1/2 pulgada', 'Tuercas', 0.15, 0.40, 150, 30, 'unidad', 2),
            ('ARR-001', 'Arandela plana 1/2"', 'Arandela plana para perno de 1/2 pulgada', 'Arandelas', 0.05, 0.15, 300, 100, 'unidad', 1)
        ])
        print("✓ Datos de productos insertados")

        # Crear trigger para actualizar fecha_actualizacion
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS update_productos_timestamp 
            AFTER UPDATE ON productos
            FOR EACH ROW
            BEGIN
                UPDATE productos 
                SET fecha_actualizacion = datetime('now') 
                WHERE id = OLD.id;
            END;
        ''')
        print("✓ Trigger para fecha_actualizacion creado")

        connection.commit()
        print("Base de datos SQLite inicializada correctamente.")

    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")
        if connection:
            connection.rollback()
    finally:
        if connection:
            connection.close()

# Para ejecutar directamente la inicialización
if __name__ == "__main__":
    init_db()