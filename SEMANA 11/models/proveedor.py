from database.connection import get_db_connection

class Proveedor:
    """
    Clase que representa un proveedor en el sistema
    """
    
    def __init__(self, id=None, nombre=None, contacto=None, telefono=None, 
                 email=None, direccion=None, ruc=None):
        self.id = id
        self.nombre = nombre
        self.contacto = contacto
        self.telefono = telefono
        self.email = email
        self.direccion = direccion
        self.ruc = ruc
    
    def guardar(self):
        """
        Guarda el proveedor en la base de datos
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if self.id:  # Actualizar proveedor existente
            cursor.execute('''
                UPDATE proveedores 
                SET nombre=?, contacto=?, telefono=?, email=?, 
                    direccion=?, ruc=?
                WHERE id=?
            ''', (self.nombre, self.contacto, self.telefono, self.email, 
                  self.direccion, self.ruc, self.id))
        else:  # Insertar nuevo proveedor
            cursor.execute('''
                INSERT INTO proveedores 
                (nombre, contacto, telefono, email, direccion, ruc)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (self.nombre, self.contacto, self.telefono, self.email, 
                  self.direccion, self.ruc))
            
            self.id = cursor.lastrowid
        
        conn.commit()
        conn.close()
    
    def eliminar(self):
        """
        Elimina el proveedor de la base de datos
        """
        if self.id:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM proveedores WHERE id=?', (self.id,))
            conn.commit()
            conn.close()
    
    @staticmethod
    def obtener_por_id(proveedor_id):
        """
        Obtiene un proveedor por su ID
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM proveedores WHERE id=?', (proveedor_id,))
        proveedor_data = cursor.fetchone()
        conn.close()
        
        if proveedor_data:
            return Proveedor(**dict(proveedor_data))
        return None
    
    @staticmethod
    def obtener_todos():
        """
        Obtiene todos los proveedores
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM proveedores ORDER BY nombre')
        proveedores_data = cursor.fetchall()
        conn.close()
        
        return [Proveedor(**dict(proveedor)) for proveedor in proveedores_data]
    
    @staticmethod
    def buscar_por_nombre(nombre):
        """
        Busca proveedores por nombre (búsqueda parcial)
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM proveedores WHERE nombre LIKE ? ORDER BY nombre', 
                      (f'%{nombre}%',))
        proveedores_data = cursor.fetchall()
        conn.close()
        
        return [Proveedor(**dict(proveedor)) for proveedor in proveedores_data]
    
    def __str__(self):
        return f"{self.nombre} - {self.contacto}"