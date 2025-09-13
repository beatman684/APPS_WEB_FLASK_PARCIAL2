from database.connection import get_db_connection

class Cliente:
    """
    Clase que representa un cliente en el sistema
    """
    
    def __init__(self, id=None, nombre=None, apellido=None, telefono=None, 
                 email=None, direccion=None, ruc_ci=None, tipo='minorista'):
        self.id = id
        self.nombre = nombre
        self.apellido = apellido
        self.telefono = telefono
        self.email = email
        self.direccion = direccion
        self.ruc_ci = ruc_ci
        self.tipo = tipo  # 'minorista' o 'mayorista'
    
    def guardar(self):
        """
        Guarda el cliente en la base de datos
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if self.id:  # Actualizar cliente existente
            cursor.execute('''
                UPDATE clientes 
                SET nombre=?, apellido=?, telefono=?, email=?, 
                    direccion=?, ruc_ci=?, tipo=?
                WHERE id=?
            ''', (self.nombre, self.apellido, self.telefono, self.email, 
                  self.direccion, self.ruc_ci, self.tipo, self.id))
        else:  # Insertar nuevo cliente
            cursor.execute('''
                INSERT INTO clientes 
                (nombre, apellido, telefono, email, direccion, ruc_ci, tipo)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (self.nombre, self.apellido, self.telefono, self.email, 
                  self.direccion, self.ruc_ci, self.tipo))
            
            self.id = cursor.lastrowid
        
        conn.commit()
        conn.close()
    
    def eliminar(self):
        """
        Elimina el cliente de la base de datos
        """
        if self.id:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM clientes WHERE id=?', (self.id,))
            conn.commit()
            conn.close()
    
    @staticmethod
    def obtener_por_id(cliente_id):
        """
        Obtiene un cliente por su ID
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM clientes WHERE id=?', (cliente_id,))
        cliente_data = cursor.fetchone()
        conn.close()
        
        if cliente_data:
            return Cliente(**dict(cliente_data))
        return None
    
    @staticmethod
    def obtener_todos():
        """
        Obtiene todos los clientes
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM clientes ORDER BY apellido, nombre')
        clientes_data = cursor.fetchall()
        conn.close()
        
        return [Cliente(**dict(cliente)) for cliente in clientes_data]
    
    @staticmethod
    def buscar_por_nombre(nombre):
        """
        Busca clientes por nombre (búsqueda parcial)
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM clientes WHERE nombre LIKE ? OR apellido LIKE ? ORDER BY apellido, nombre', 
                      (f'%{nombre}%', f'%{nombre}%'))
        clientes_data = cursor.fetchall()
        conn.close()
        
        return [Cliente(**dict(cliente)) for cliente in clientes_data]
    
    def __str__(self):
        return f"{self.nombre} {self.apellido} - {self.email}"