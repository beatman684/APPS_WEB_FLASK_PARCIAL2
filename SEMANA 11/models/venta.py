from database.connection import get_db_connection
from datetime import datetime

class Venta:
    """
    Clase que representa una venta en el sistema
    """
    
    def __init__(self, id=None, cliente_id=None, fecha=None, total=0, 
                 estado='completada', tipo_pago='efectivo', detalles=None):
        self.id = id
        self.cliente_id = cliente_id
        self.fecha = fecha
        self.total = total
        self.estado = estado  # 'completada', 'cancelada', 'pendiente'
        self.tipo_pago = tipo_pago  # 'efectivo', 'tarjeta', 'transferencia'
        self.detalles = detalles or []
    
    def guardar(self):
        """
        Guarda la venta y sus detalles en la base de datos
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            if self.id:  # Actualizar venta existente
                cursor.execute('''
                    UPDATE ventas 
                    SET cliente_id=?, total=?, estado=?, tipo_pago=?
                    WHERE id=?
                ''', (self.cliente_id, self.total, self.estado, self.tipo_pago, self.id))
                
                # Eliminar detalles existentes
                cursor.execute('DELETE FROM detalle_venta WHERE venta_id=?', (self.id,))
            else:  # Insertar nueva venta
                cursor.execute('''
                    INSERT INTO ventas 
                    (cliente_id, total, estado, tipo_pago)
                    VALUES (?, ?, ?, ?)
                ''', (self.cliente_id, self.total, self.estado, self.tipo_pago))
                
                self.id = cursor.lastrowid
            
            # Insertar detalles de venta
            for detalle in self.detalles:
                cursor.execute('''
                    INSERT INTO detalle_venta 
                    (venta_id, producto_id, cantidad, precio_unitario, subtotal)
                    VALUES (?, ?, ?, ?, ?)
                ''', (self.id, detalle['producto_id'], detalle['cantidad'], 
                      detalle['precio_unitario'], detalle['subtotal']))
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            raise e
            
        finally:
            conn.close()
    
    def agregar_detalle(self, producto_id, cantidad, precio_unitario):
        """
        Agrega un detalle a la venta
        """
        subtotal = cantidad * precio_unitario
        self.detalles.append({
            'producto_id': producto_id,
            'cantidad': cantidad,
            'precio_unitario': precio_unitario,
            'subtotal': subtotal
        })
        self.total += subtotal
    
    @staticmethod
    def obtener_por_id(venta_id):
        """
        Obtiene una venta por su ID con todos sus detalles
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener datos de la venta
        cursor.execute('SELECT * FROM ventas WHERE id=?', (venta_id,))
        venta_data = cursor.fetchone()
        
        if not venta_data:
            conn.close()
            return None
        
        # Obtener detalles de la venta
        cursor.execute('''
            SELECT dv.*, p.nombre as producto_nombre 
            FROM detalle_venta dv 
            JOIN productos p ON dv.producto_id = p.id 
            WHERE dv.venta_id=?
        ''', (venta_id,))
        detalles_data = cursor.fetchall()
        
        conn.close()
        
        # Crear objeto Venta
        venta = Venta(**dict(venta_data))
        venta.detalles = [dict(detalle) for detalle in detalles_data]
        
        return venta
    
    @staticmethod
    def obtener_todos():
        """
        Obtiene todas las ventas
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT v.*, c.nombre as cliente_nombre, c.apellido as cliente_apellido 
            FROM ventas v 
            JOIN clientes c ON v.cliente_id = c.id 
            ORDER BY v.fecha DESC
        ''')
        ventas_data = cursor.fetchall()
        
        conn.close()
        
        ventas = []
        for venta_data in ventas_data:
            venta_dict = dict(venta_data)
            # Crear un campo nombre_completo para el cliente
            venta_dict['cliente_nombre_completo'] = f"{venta_dict['cliente_nombre']} {venta_dict['cliente_apellido']}"
            ventas.append(venta_dict)
        
        return ventas
    
    def __str__(self):
        return f"Venta #{self.id} - Total: ${self.total}"