class Producto:
    def __init__(self, id_producto, codigo_producto, nombre_producto, descripcion,
                 material, tipo_rosca, medida, unidad_medida, precio_compra,
                 precio_venta, stock_actual, stock_minimo, id_proveedor, id_categoria):
        self.id_producto = id_producto
        self.codigo_producto = codigo_producto
        self.nombre_producto = nombre_producto
        self.descripcion = descripcion
        self.material = material
        self.tipo_rosca = tipo_rosca
        self.medida = medida
        self.unidad_medida = unidad_medida
        self.precio_compra = precio_compra
        self.precio_venta = precio_venta
        self.stock_actual = stock_actual
        self.stock_minimo = stock_minimo
        self.id_proveedor = id_proveedor
        self.id_categoria = id_categoria