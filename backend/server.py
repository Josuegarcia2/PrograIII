import os
import re
import time
import uuid
from functools import wraps

from flask import Flask, jsonify, request, render_template, session, redirect, url_for
from werkzeug.utils import secure_filename

from modulos.crud_productos import CRUDProductos
from modulos.crud_usuarios import CRUDUsuarios
from modulos.crud_pedidos import CRUDPedidos
from modulos.abuelita_ia import AbuelitaIA, guardar_historial

app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static', static_url_path='/static')

app.secret_key = os.environ.get('SECRET_KEY', 'clave_secreta_pastelitos_abuela')

app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

UPLOAD_FOLDER = os.path.join(app.static_folder, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
EXTENSIONES_PERMITIDAS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

crud_prod = CRUDProductos()
crud_user = CRUDUsuarios()
crud_ped = CRUDPedidos()
chatbot = AbuelitaIA()

METODOS_PAGO = {'Transferencia bancaria', 'Contra entrega'}


def error_json(mensaje, codigo=400):
    return jsonify({"ok": False, "mensaje": mensaje}), codigo


def login_requerido(f):
    @wraps(f)
    def envoltura(*args, **kwargs):
        if 'usuario_id' not in session:
            return error_json("Inicia sesión para continuar.", 401)
        return f(*args, **kwargs)
    return envoltura


def admin_requerido(f):
    @wraps(f)
    def envoltura(*args, **kwargs):
        if session.get('usuario_rol') != 1:
            return error_json("Acceso denegado", 403)
        return f(*args, **kwargs)
    return envoltura


def password_valida(password):
    return bool(
        password and len(password) >= 8
        and re.search(r'[A-Z]', password) and re.search(r'[a-z]', password)
        and re.search(r'[0-9]', password) and re.search(r'[^A-Za-z0-9]', password)
    )


def guardar_imagen(archivo):
    if not archivo or archivo.filename == '':
        return None, None
    nombre = secure_filename(archivo.filename)
    ext = nombre.rsplit('.', 1)[-1].lower() if '.' in nombre else ''
    if ext not in EXTENSIONES_PERMITIDAS:
        return None, "Formato de imagen no permitido (usa PNG, JPG, GIF o WEBP)."
    base = nombre.rsplit('.', 1)[0] or 'producto'
    final = f"{uuid.uuid4().hex[:10]}_{base}.{ext}"
    archivo.save(os.path.join(app.config['UPLOAD_FOLDER'], final))
    return f"uploads/{final}", None


def leer_datos_producto(form):
    nombre = (form.get('nombre') or '').strip()
    if not nombre:
        return None, "El nombre es obligatorio."
    try:
        precio = round(float(form.get('precio', '')), 2)
        stock = int(form.get('stock') or 0)
        id_categoria = int(form.get('id_categoria') or 1)
    except ValueError:
        return None, "Precio, stock y categoría deben ser números."
    if precio <= 0:
        return None, "El precio debe ser mayor que 0."
    if stock < 0:
        return None, "El stock no puede ser negativo."
    return {
        "nombre": nombre,
        "descripcion": (form.get('descripcion') or '').strip(),
        "precio": precio,
        "stock": stock,
        "id_categoria": id_categoria,
        "ingredientes": (form.get('ingredientes') or '').strip(),
    }, None


_intentos = {}
_MAX_INTENTOS = 5
_BLOQUEO_SEG = 300


def _clave_intento(correo):
    return f"{request.remote_addr}|{(correo or '').strip().lower()}"


def _bloqueado(clave):
    dato = _intentos.get(clave)
    if not dato:
        return False
    cuenta, desde = dato
    if time.time() - desde > _BLOQUEO_SEG:
        _intentos.pop(clave, None)
        return False
    return cuenta >= _MAX_INTENTOS


def _registrar_fallo(clave):
    cuenta, desde = _intentos.get(clave, (0, time.time()))
    _intentos[clave] = (cuenta + 1, desde)


def iniciar_sesion(usuario, nombre_por_defecto):
    session.clear()
    session['usuario_id'] = usuario.get('id_usuario')
    nombre_u = usuario.get('nombre', '') or ''
    apellido_u = usuario.get('apellido', '') or ''
    session['usuario_nombre'] = f"{nombre_u} {apellido_u}".strip() or nombre_u or nombre_por_defecto
    session['usuario_rol'] = usuario.get('id_rol', 2)


@app.route('/')
def inicio():
    if 'usuario_id' in session:
        if session.get('usuario_rol') == 1:
            return redirect(url_for('admin_page'))
        return redirect(url_for('cliente_page'))
    return render_template('index.html')


@app.route('/login')
def login_page():
    if 'usuario_id' in session:
        if session.get('usuario_rol') == 1:
            return redirect(url_for('admin_page'))
        return redirect(url_for('cliente_page'))
    return render_template('login.html')


@app.route('/cliente.html')
def cliente_page():
    if 'usuario_id' not in session:
        return redirect('/login')
    return render_template('cliente.html',
                           usuario_nombre=session.get('usuario_nombre', 'Cliente'),
                           usuario_id=session.get('usuario_id', 0))


@app.route('/admin.html')
def admin_page():
    if 'usuario_id' not in session or session.get('usuario_rol') != 1:
        return redirect('/login')
    return render_template('admin.html',
                           usuario_nombre=session.get('usuario_nombre', 'Administrador'),
                           usuario_id=session.get('usuario_id', 0))


@app.route('/api/registro', methods=['POST'])
def api_registro():
    try:
        datos = request.get_json(silent=True) or request.form
        nombre = (datos.get('nombre') or '').strip()
        correo = (datos.get('correo') or '').strip().lower()
        telefono = (datos.get('telefono') or '').strip()
        password = datos.get('password') or ''

        if not nombre or not correo or not password or not telefono:
            if request.is_json:
                return error_json("Por favor completa todos los campos obligatorios.")
            return redirect('/login')

        if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', correo):
            if request.is_json:
                return error_json("El correo no tiene un formato válido.")
            return redirect('/login')

        # Registro directo en la Base de Datos usando tu módulo CRUD (hashea la contraseña de forma segura)
        exito, mensaje = crud_user.registrar_usuario(nombre, correo, telefono, password, id_rol=2)
        
        if exito:
            usuario, _ = crud_user.autenticar_usuario(correo, password)
            if usuario:
                iniciar_sesion(usuario, 'Cliente')
                if request.is_json:
                    return jsonify({"ok": True, "redirect": "/cliente.html"}), 200
                return redirect('/cliente.html')

        if request.is_json:
            return error_json(mensaje)
        return redirect('/login')
    except Exception as e:
        print(f"Error en registro: {e}")
        if request.is_json:
            return error_json("Error interno del servidor.", 500)
        return redirect('/login')


@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        datos = request.get_json(silent=True) or request.form
        correo = (datos.get('correo') or '').strip()
        password = datos.get('password') or ''

        if not correo or not password:
            if request.is_json:
                return error_json("Ingresa correo y contraseña.")
            return redirect('/login')

        clave = _clave_intento(correo)
        if _bloqueado(clave):
            if request.is_json:
                return error_json("Demasiados intentos. Espera unos minutos.", 429)
            return redirect('/login')

        usuario, mensaje = crud_user.autenticar_usuario(correo, password)
        if not usuario:
            _registrar_fallo(clave)
            if request.is_json:
                return error_json(mensaje, 401)
            return redirect('/login')

        _intentos.pop(clave, None)
        iniciar_sesion(usuario, 'Usuario')
        redirect_url = '/admin.html' if usuario.get('id_rol') == 1 else '/cliente.html'
        
        if request.is_json:
            return jsonify({"ok": True, "mensaje": "Sesión iniciada", "redirect": redirect_url}), 200
        return redirect(redirect_url)
    except Exception as e:
        if request.is_json:
            return error_json("Error interno del servidor.", 500)
        return redirect('/login')


@app.route('/api/logout', methods=['POST', 'GET'])
def api_logout():
    session.clear()
    if request.is_json:
        return jsonify({"ok": True, "redirect": "/"}), 200
    return redirect('/')


@app.route('/api/usuarios', methods=['GET'])
@admin_requerido
def api_listar_usuarios():
    return jsonify({"ok": True, "usuarios": crud_user.obtener_todos_usuarios()}), 200


@app.route('/api/usuarios/cambiar_rol', methods=['POST'])
@admin_requerido
def api_cambiar_rol():
    datos = request.get_json(silent=True) or {}
    try:
        id_usuario = int(datos.get('id_usuario'))
        nuevo_rol = int(datos.get('nuevo_rol'))
    except (TypeError, ValueError):
        return error_json("Datos no válidos.")
    if id_usuario == session.get('usuario_id'):
        return error_json("No puedes cambiar tu propio rol.")
    exito, msj = crud_user.actualizar_rol_usuario(id_usuario, nuevo_rol)
    return jsonify({"ok": exito, "mensaje": msj})


@app.route('/api/usuarios/cambiar_estado', methods=['POST'])
@admin_requerido
def api_cambiar_estado_usuario():
    datos = request.get_json(silent=True) or {}
    try:
        id_usuario = int(datos.get('id_usuario'))
        estado = int(datos.get('estado'))
    except (TypeError, ValueError):
        return error_json("Datos no válidos.")
    if id_usuario == session.get('usuario_id'):
        return error_json("No puedes desactivar tu propia cuenta.")
    exito, msj = crud_user.cambiar_estado_usuario(id_usuario, estado)
    return jsonify({"ok": exito, "mensaje": msj})


@app.route('/api/productos', methods=['GET'])
def listar_productos():
    return jsonify({"ok": True, "productos": crud_prod.obtener_productos()}), 200


@app.route('/api/categorias', methods=['GET'])
def listar_categorias():
    return jsonify({"ok": True, "categorias": crud_prod.obtener_categorias()}), 200


@app.route('/api/productos', methods=['POST'])
@admin_requerido
def crear_producto():
    try:
        datos, error = leer_datos_producto(request.form)
        if error:
            return error_json(error)

        ruta_imagen, error = guardar_imagen(request.files.get('imagen'))
        if error:
            return error_json(error)

        exito, msj = crud_prod.agregar_producto(
            nombre=datos["nombre"], descripcion=datos["descripcion"], precio=datos["precio"],
            imagen=ruta_imagen or '', stock=datos["stock"],
            id_categoria=datos["id_categoria"], ingredientes=datos["ingredientes"],
        )
        if exito:
            return jsonify({"ok": True, "mensaje": "Producto guardado con éxito"}), 201
        return error_json(msj)
    except Exception as e:
        return error_json("Error interno del servidor.", 500)


@app.route('/api/productos/<int:id_producto>', methods=['PUT'])
@admin_requerido
def editar_producto(id_producto):
    try:
        datos, error = leer_datos_producto(request.form)
        if error:
            return error_json(error)

        ruta_imagen, error = guardar_imagen(request.files.get('imagen'))
        if error:
            return error_json(error)

        exito, msj = crud_prod.actualizar_producto(
            id_producto, datos["nombre"], datos["descripcion"], datos["precio"],
            datos["stock"], datos["id_categoria"], datos["ingredientes"], imagen=ruta_imagen,
        )
        return jsonify({"ok": exito, "mensaje": msj}), (200 if exito else 400)
    except Exception as e:
        return error_json("Error interno del servidor.", 500)


@app.route('/api/productos/<int:id_producto>', methods=['DELETE'])
@admin_requerido
def quitar_producto(id_producto):
    exito, msj = crud_prod.desactivar_producto(id_producto)
    return jsonify({"ok": exito, "mensaje": msj}), (200 if exito else 400)


@app.route('/api/pedidos', methods=['POST'])
@login_requerido
def api_crear_pedido():
    datos = request.get_json(silent=True) or {}
    items = datos.get('items')
    direccion = (datos.get('direccion') or '').strip()
    ciudad = (datos.get('ciudad') or '').strip()
    telefono = (datos.get('telefono') or '').strip()
    metodo = datos.get('metodo_pago')

    if not isinstance(items, list) or not items:
        return error_json("Tu carrito está vacío.")
    if not direccion or not ciudad:
        return error_json("Escribe tu dirección y ciudad.")
    if len(direccion) > 255 or len(ciudad) > 100:
        return error_json("La dirección o ciudad es demasiado larga.")
    if metodo not in METODOS_PAGO:
        return error_json("Elige un método de pago válido.")

    referencia = f"Tel: {telefono}" if telefono else ''
    exito, resultado = crud_ped.crear_pedido(
        session['usuario_id'], items, direccion, ciudad, referencia, metodo
    )
    if exito:
        return jsonify({"ok": True, "pedido": resultado}), 201
    return error_json(resultado)


@app.route('/api/mis_pedidos', methods=['GET'])
@login_requerido
def api_mis_pedidos():
    return jsonify({"ok": True, "pedidos": crud_ped.obtener_pedidos_usuario(session['usuario_id'])})


@app.route('/api/pedidos', methods=['GET'])
@admin_requerido
def api_listar_pedidos():
    return jsonify({"ok": True, "pedidos": crud_ped.obtener_todos_pedidos()})


@app.route('/api/estados', methods=['GET'])
@admin_requerido
def api_estados():
    return jsonify({"ok": True, "estados": crud_ped.obtener_estados()})


@app.route('/api/pedidos/<int:id_pedido>/estado', methods=['POST'])
@admin_requerido
def api_estado_pedido(id_pedido):
    datos = request.get_json(silent=True) or {}
    try:
        id_estado = int(datos.get('id_estado'))
    except (TypeError, ValueError):
        return error_json("Estado no válido.")
    exito, msj = crud_ped.cambiar_estado(id_pedido, id_estado)
    return jsonify({"ok": exito, "mensaje": msj}), (200 if exito else 400)


@app.route('/api/admin/estadisticas', methods=['GET'])
@admin_requerido
def api_estadisticas():
    return jsonify({"ok": True, **crud_ped.estadisticas()})


@app.route('/api/chat', methods=['POST'])
def api_chat():
    try:
        data = request.get_json(silent=True) or {}
        mensaje = (data.get('mensaje') or '').strip()[:300]

        if not mensaje:
            return jsonify({
                "ok": False,
                "respuesta": "¡Hola, mi corazón! Escribe o selecciona una pregunta para poder ayudarte 👵🏼"
            }), 200

        respuesta = chatbot.responder(mensaje, crud_prod.obtener_productos())
        guardar_historial(session.get('usuario_id'), mensaje, respuesta)
        return jsonify({"ok": True, "respuesta": respuesta}), 200
    except Exception as e:
        return jsonify({"ok": False, "respuesta": "Ups, ocurrió un error. Intenta de nuevo."}), 500


@app.errorhandler(413)
def archivo_muy_grande(_e):
    return error_json("El archivo es demasiado grande (máximo 5 MB).", 413)

@app.route('/api/pedidos/<int:id_pedido>', methods=['PUT'])
@admin_requerido
def api_actualizar_pedido(id_pedido):
    datos = request.get_json(silent=True) or {}
    id_estado = datos.get('id_estado')
    
   
    exito, mensaje = crud_ped.cambiar_estado(id_pedido, id_estado)
    return jsonify({"ok": exito, "mensaje": mensaje}), (200 if exito else 400)

@app.route('/api/pedidos/<int:id_pedido>', methods=['DELETE'])
@admin_requerido
def api_eliminar_pedido(id_pedido):
   
    exito, mensaje = crud_ped.eliminar_pedido(id_pedido) if hasattr(crud_ped, 'eliminar_pedido') else (True, "Pedido eliminado")
    return jsonify({"ok": exito, "mensaje": mensaje}), (200 if exito else 400)


if __name__ == '__main__':
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug, port=5000)