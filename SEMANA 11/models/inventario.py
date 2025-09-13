from models.producto import Producto
from database.connection import get_db_connection

class Inventario:
    """
    Clase que gestiona el inventario de productos utilizando un diccionario en memoria
    para optimizar las operaciones frecuentes, mientras mantiene persistencia en la base de datos
    """
    
    def __init__(self):
        self.productos = {}  # Diccionario para búsquedas rápidas por ID
        self.cargar_inventario()
    
    def cargar_inventario(self):
        """
        Carga todos los productos desde la base de datos al diccionario en memoria
        """
        productos_db = Producto.obtener_todos()
        self.productos = {producto.id: producto for producto in productos_db}
    
    def añadir_producto(self, producto):
        """
        Añade un nuevo producto al inventario
        """
        producto.guardar()  # Guarda en la base de datos
        self.productos[producto.id] = producto  # Actualiza el diccionario en memoria
        return producto.id
    
    def eliminar_producto(self, producto_id):
        """
        Elimina un producto del inventario por ID
        """
        if producto_id in self.productos:
            producto = self.productos[producto_id]
            producto.eliminar()  # Elimina de la base de datos
            del self.productos[producto_id]  # Elimina del diccionario en memoria
            return True
        return False
    
    def actualizar_producto(self, producto_id, **kwargs):
        """
        Actualiza los atributos de un producto
        """
        if producto_id in self.productos:
            producto = self.productos[producto_id]
            
            # Actualizar los atributos proporcionados
            for key, value in kwargs.items():
                if hasattr(producto, key):
                    setattr(producto, key, value)
            
            producto.guardar()  # Guarda los cambios en la base de datos
            return True
        return False
    
    def buscar_por_nombre(self, nombre):
        """
        Busca productos por nombre (usa búsqueda en base de datos para coincidencias parciales)
        """
        return Producto.buscar_por_nombre(nombre)
    
    def obtener_producto(self, producto_id):
        """
        Obtiene un producto por ID
        """
        return self.productos.get(producto_id)
    
    def obtener_todos(self):
        """
        Obtiene todos los productos del inventario
        """
        return list(self.productos.values())
    
    def obtener_productos_bajo_stock(self):
        """
        Obtiene productos con stock por debajo del mínimo
        """
        return [p for p in self.productos.values() if p.stock < p.stock_minimo]
    
    def contar_productos_bajo_stock(self):
        """
        Cuenta los productos con stock por debajo del mínimo
        """
        count = 0
        for producto in self.productos.values():
            if producto.stock < producto.stock_minimo:
                count += 1
        return count
    
    def actualizar_stock(self, producto_id, cantidad):
        """
        Actualiza el stock de un producto
        """
        if producto_id in self.productos:
            producto = self.productos[producto_id]
            producto.stock += cantidad
            producto.guardar()
            return True
        return False