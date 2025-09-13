from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from models.inventario import Inventario
from models.producto import Producto
# Comenta estas líneas temporalmente hasta que crees los archivos
# from models.cliente import Cliente
# from models.proveedor import Proveedor
# from models.venta import Venta
from database.connection import init_db
import json

app = Flask(__name__)
app.secret_key = 'clave_secreta_perno_todo'  # Cambia esto en producción

# Inicializar el inventario
inventario = Inventario()

@app.route('/')
def index():
    """
    Página principal del sistema de gestión
    """
    return render_template('index.html')

# Rutas para gestión de productos
@app.route('/productos')
def listar_productos():
    """
    Muestra todos los productos del inventario
    """
    productos = inventario.obtener_todos()
    productos_bajo_stock = inventario.contar_productos_bajo_stock()
    return render_template('productos/lista.html', 
                         productos=productos, 
                         productos_bajo_stock=productos_bajo_stock)

@app.route('/productos/agregar', methods=['GET', 'POST'])
def agregar_producto():
    """
    Agrega un nuevo producto al inventario
    """
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            codigo = request.form['codigo']
            nombre = request.form['nombre']
            descripcion = request.form['descripcion']
            categoria = request.form['categoria']
            precio_compra = float(request.form['precio_compra'])
            precio_venta = float(request.form['precio_venta'])
            stock = int(request.form['stock'])
            stock_minimo = int(request.form['stock_minimo'])
            unidad_medida = request.form['unidad_medida']
            proveedor_id = request.form.get('proveedor_id') or None
            
            # Crear nuevo producto
            nuevo_producto = Producto(
                codigo=codigo,
                nombre=nombre,
                descripcion=descripcion,
                categoria=categoria,
                precio_compra=precio_compra,
                precio_venta=precio_venta,
                stock=stock,
                stock_minimo=stock_minimo,
                unidad_medida=unidad_medida,
                proveedor_id=proveedor_id
            )
            
            # Añadir al inventario
            inventario.añadir_producto(nuevo_producto)
            
            flash('Producto agregado correctamente', 'success')
            return redirect(url_for('listar_productos'))
            
        except Exception as e:
            flash(f'Error al agregar producto: {str(e)}', 'error')
    
    # Si es GET, mostrar formulario
    return render_template('productos/agregar.html')

@app.route('/productos/editar/<int:producto_id>', methods=['GET', 'POST'])
def editar_producto(producto_id):
    """
    Edita un producto existente
    """
    producto = inventario.obtener_producto(producto_id)
    
    if not producto:
        flash('Producto no encontrado', 'error')
        return redirect(url_for('listar_productos'))
    
    if request.method == 'POST':
        try:
            # Actualizar producto con los datos del formulario
            producto.codigo = request.form['codigo']
            producto.nombre = request.form['nombre']
            producto.descripcion = request.form['descripcion']
            producto.categoria = request.form['categoria']
            producto.precio_compra = float(request.form['precio_compra'])
            producto.precio_venta = float(request.form['precio_venta'])
            producto.stock = int(request.form['stock'])
            producto.stock_minimo = int(request.form['stock_minimo'])
            producto.unidad_medida = request.form['unidad_medida']
            producto.proveedor_id = request.form.get('proveedor_id') or None
            
            # Guardar cambios
            inventario.actualizar_producto(producto_id)
            
            flash('Producto actualizado correctamente', 'success')
            return redirect(url_for('listar_productos'))
            
        except Exception as e:
            flash(f'Error al actualizar producto: {str(e)}', 'error')
    
    # Si es GET, mostrar formulario con datos actuales
    return render_template('productos/editar.html', producto=producto)

@app.route('/productos/eliminar/<int:producto_id>')
def eliminar_producto(producto_id):
    """
    Elimina un producto del inventario
    """
    if inventario.eliminar_producto(producto_id):
        flash('Producto eliminado correctamente', 'success')
    else:
        flash('Error al eliminar producto', 'error')
    
    return redirect(url_for('listar_productos'))

@app.route('/api/productos')
def api_productos():
    """
    API para obtener productos (para AJAX)
    """
    productos = inventario.obtener_todos()
    return jsonify([{
        'id': p.id,
        'nombre': p.nombre,
        'precio_venta': p.precio_venta,
        'stock': p.stock
    } for p in productos])

if __name__ == '__main__':
    # Inicializar la base de datos si no existe
    init_db()
    
    # Ejecutar la aplicación
    app.run(debug=True)