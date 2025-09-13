from database.connection import get_db_connection

class Producto:
    """
    Clase que representa un producto en el inventario
    """
    
    def __init__(self, id=None, codigo=None, nombre=None, descripcion=None, categoria=None,
                 precio_compra=0, precio_venta=0, stock=0, stock_minimo=10, 
                 unidad_medida='unidad', proveedor_id=None, **kwargs):
        self.id = id
        self.codigo = codigo
        self.nombre = nombre
        self.descripcion = descripcion
        self.categoria = categoria
        self.precio_compra = precio_compra
        self.precio_venta = precio_venta
        self.stock = stock
        self.stock_minimo = stock_minimo
        self.unidad_medida = unidad_medida
        self.proveedor_id = proveedor_id
        
        # Campos adicionales que pueden venir de la base de datos
        # pero que no son esenciales para la creación inicial
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def guardar(self):
        """
        Guarda el producto en la base de datos
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if self.id:  # Actualizar producto existente
            cursor.execute('''
                UPDATE productos 
                SET codigo=?, nombre=?, descripcion=?, categoria=?, precio_compra=?, 
                    precio_venta=?, stock=?, stock_minimo=?, unidad_medida=?, proveedor_id=?, 
                    fecha_actualizacion=CURRENT_TIMESTAMP
                WHERE id=?
            ''', (self.codigo, self.nombre, self.descripcion, self.categoria, 
                  self.precio_compra, self.precio_venta, self.stock, self.stock_minimo, 
                  self.unidad_medida, self.proveedor_id, self.id))
        else:  # Insertar nuevo producto
            cursor.execute('''
                INSERT INTO productos 
                (codigo, nombre, descripcion, categoria, precio_compra, precio_venta, 
                 stock, stock_minimo, unidad_medida, proveedor_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (self.codigo, self.nombre, self.descripcion, self.categoria, 
                  self.precio_compra, self.precio_venta, self.stock, self.stock_minimo, 
                  self.unidad_medida, self.proveedor_id))
            
            self.id = cursor.lastrowid
        
        conn.commit()
        conn.close()
    
    def eliminar(self):
        """
        Elimina el producto de la base de datos
        """
        if self.id:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM productos WHERE id=?', (self.id,))
            conn.commit()
            conn.close()
    
    @staticmethod
    def obtener_por_id(producto_id):
        """
        Obtiene un producto por su ID
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM productos WHERE id=?', (producto_id,))
        producto_data = cursor.fetchone()
        conn.close()
        
        if producto_data:
            return Producto(**dict(producto_data))
        return None
    
    @staticmethod
    def obtener_todos():
        """
        Obtiene todos los productos del inventario
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM productos ORDER BY nombre')
        productos_data = cursor.fetchall()
        conn.close()
        
        return [Producto(**dict(producto)) for producto in productos_data]
    
    @staticmethod
    def buscar_por_nombre(nombre):
        """
        Busca productos por nombre (búsqueda parcial)
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM productos WHERE nombre LIKE ? ORDER BY nombre', 
                      (f'%{nombre}%',))
        productos_data = cursor.fetchall()
        conn.close()
        
        return [Producto(**dict(producto)) for producto in productos_data]
    
    @staticmethod
    def obtener_por_categoria(categoria):
        """
        Obtiene productos por categoría
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM productos WHERE categoria=? ORDER BY nombre', 
                      (categoria,))
        productos_data = cursor.fetchall()
        conn.close()
        
        return [Producto(**dict(producto)) for producto in productos_data]
    
    def __str__(self):
        return f"{self.nombre} - Stock: {self.stock} {self.unidad_medida} - Precio: ${self.precio_venta}"