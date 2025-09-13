import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
from pathlib import Path

# Cargar variables de entorno
load_dotenv()

def get_db_connection():
    """
    Establece y retorna una conexión a la base de datos MySQL/MariaDB
    """
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'perno_todo_db'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            port=os.getenv('DB_PORT', 3306)
        )
        
        if connection.is_connected():
            print("Conexión a MySQL establecida correctamente")
            return connection
            
    except Error as e:
        print(f"Error al conectar a MySQL: {e}")
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
        
        # Leer el archivo de queries SQL
        base_dir = Path(__file__).resolve().parent
        sql_file = os.path.join(base_dir, 'queries_mysql.sql')
        
        # Verificar si el archivo existe
        if not os.path.exists(sql_file):
            raise FileNotFoundError(f"El archivo {sql_file} no existe.")
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # Ejecutar cada sentencia SQL por separado
        for statement in sql_script.split(';'):
            if statement.strip():
                cursor.execute(statement)
        
        connection.commit()
        print("Base de datos MySQL inicializada correctamente.")
        
    except Error as e:
        print(f"Error al inicializar la base de datos: {e}")
        connection.rollback()
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Para ejecutar directamente la inicialización
if __name__ == "__main__":
    init_db()