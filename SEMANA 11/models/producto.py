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

        for key, value in kwargs.items():
            setattr(self, key, value)

    def guardar(self):
        """
        Guarda el producto en la base de datos
        """
        conn = get_db_connection()
        if conn is None:
            return False

        cursor = conn.cursor()

        try:
            if self.id:  # Actualizar producto existente
                cursor.execute('''
                    UPDATE productos 
                    SET codigo=?, nombre=?, descripcion=?, categoria=?, precio_compra=?, 
                        precio_venta=?, stock=?, stock_minimo=?, unidad_medida=?, proveedor_id=?, 
                        fecha_actualizacion=datetime('now')
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
            return True

        except Exception as e:
            print(f"Error al guardar producto: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def eliminar(self):
        """
        Elimina el producto de la base de datos
        """
        if self.id:
            conn = get_db_connection()
            if conn is None:
                return False

            cursor = conn.cursor()
            try:
                cursor.execute('DELETE FROM productos WHERE id=?', (self.id,))
                conn.commit()
                return True
            except Exception as e:
                print(f"Error al eliminar producto: {e}")
                conn.rollback()
                return False
            finally:
                conn.close()
        return False

    @staticmethod
    def obtener_por_id(producto_id):
        """
        Obtiene un producto por su ID
        """
        conn = get_db_connection()
        if conn is None:
            return None

        cursor = conn.cursor()
        try:
            cursor.execute('SELECT * FROM productos WHERE id=?', (producto_id,))
            producto_data = cursor.fetchone()

            if producto_data:
                return Producto(**dict(producto_data))
            return None
        except Exception as e:
            print(f"Error al obtener producto: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def obtener_todos():
        """
        Obtiene todos los productos del inventario
        """
        conn = get_db_connection()
        if conn is None:
            return []

        cursor = conn.cursor()
        try:
            cursor.execute('SELECT * FROM productos ORDER BY nombre')
            productos_data = cursor.fetchall()
            return [Producto(**dict(producto)) for producto in productos_data]
        except Exception as e:
            print(f"Error al obtener productos: {e}")
            return []
        finally:
            conn.close()

    # Los demás métodos se mantienen igual...
    # ... (buscar_por_nombre, obtener_por_categoria, etc.)

    def __str__(self):
        return f"{self.nombre} - Stock: {self.stock} {self.unidad_medida} - Precio: ${self.precio_venta}"
