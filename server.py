from flask import Flask, jsonify, request, render_template, session, redirect, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename
from modulos.crud_productos import CRUDProductos
from modulos.crud_usuarios import CRUDUsuarios
import os

app = Flask(__name__, template_folder='templates', static_folder='static', static_url_path='/static')
app.secret_key = 'clave_secreta_pastelitos_abuela'
CORS(app)

# Carpeta física para las imágenes subidas
UPLOAD_FOLDER = os.path.join(app.static_folder, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

crud_prod = CRUDProductos()
crud_user = CRUDUsuarios()

# -------------------------------------------------------------
# RUTAS DE VISTAS (HTML)
# -------------------------------------------------------------
@app.route('/')
def inicio():
    if 'usuario_id' in session:
        if session.get('usuario_rol') == 1:
            return redirect(url_for('admin_page'))
        return redirect(url_for('cliente_page'))
    return render_template('index.html')

@app.route('/cliente.html')
def cliente_page():
    if 'usuario_id' not in session:
        return redirect('/')
    return render_template('cliente.html', usuario_nombre=session.get('usuario_nombre', 'Cliente'))

@app.route('/admin.html')
def admin_page():
    # Solo accesible si es Administrador (id_rol == 1)
    if 'usuario_id' not in session or session.get('usuario_rol') != 1:
        return redirect('/')
    return render_template('admin.html', usuario_nombre=session.get('usuario_nombre', 'Administrador'))

# -------------------------------------------------------------
# RUTAS API DE AUTENTICACIÓN
# -------------------------------------------------------------
# API REGISTRO
@app.route('/api/registro', methods=['POST'])
def api_registro():
    try:
        datos = request.get_json() or {}
        nombre = datos.get('nombre') or datos.get('nombre_completo')
        correo = datos.get('email') or datos.get('correo')
        telefono = datos.get('telefono', '')
        password = datos.get('password')

        # Log para depuración en la consola
        print(f"📥 Datos de registro recibidos: nombre={nombre}, correo={correo}, pass={'***' if password else None}")

        if not nombre or not correo or not password:
            return jsonify({"ok": False, "mensaje": "Completa todos los campos obligatorios."}), 400

        # Por defecto registra como cliente (id_rol = 2)
        exito, mensaje = crud_user.registrar_usuario(nombre, correo, telefono, password, id_rol=2)

        if exito:
            usuario, _ = crud_user.autenticar_usuario(correo, password)
            if usuario:
                session['usuario_id'] = usuario['id_usuario']
                session['usuario_nombre'] = usuario['nombre']
                session['usuario_rol'] = usuario['id_rol']
                return jsonify({"ok": True, "redirect": "/cliente.html"}), 200

        return jsonify({"ok": False, "mensaje": mensaje}), 400

    except Exception as e:
        print(f"❌ Error en /api/registro: {e}")
        return jsonify({"ok": False, "mensaje": str(e)}), 500

# API LOGIN
@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        datos = request.get_json() or {}
        correo = datos.get('email') or datos.get('correo')
        password = datos.get('password')

        print(f"🔑 Intento de login: correo={correo}")

        if not correo or not password:
            return jsonify({"ok": False, "mensaje": "Ingresa correo y contraseña."}), 400

        usuario, mensaje = crud_user.autenticar_usuario(correo, password)

        if usuario:
            session['usuario_id'] = usuario['id_usuario']
            session['usuario_nombre'] = f"{usuario['nombre']} {usuario['apellido']}".strip()
            session['usuario_rol'] = usuario['id_rol']

            # Redirección por rol: 1 = Admin, 2 = Cliente
            redirect_url = '/admin.html' if usuario['id_rol'] == 1 else '/cliente.html'
            return jsonify({"ok": True, "mensaje": "Sesión iniciada", "redirect": redirect_url}), 200
        else:
            return jsonify({"ok": False, "mensaje": mensaje}), 401

    except Exception as e:
        print(f"❌ Error en /api/login: {e}")
        return jsonify({"ok": False, "mensaje": str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({"ok": True, "redirect": "/"}), 200

# -------------------------------------------------------------
# RUTAS API DE USUARIOS (ADMIN)
# -------------------------------------------------------------
# API para obtener lista de usuarios (Solo Admin)
@app.route('/api/usuarios', methods=['GET'])
def api_listar_usuarios():
    if session.get('usuario_rol') != 1:
        return jsonify({"ok": False, "mensaje": "Acceso denegado"}), 403
    usuarios = crud_user.obtener_todos_usuarios()
    return jsonify({"ok": True, "usuarios": usuarios}), 200

# API para actualizar rol de usuario desde admin.html
@app.route('/api/usuarios/cambiar_rol', methods=['POST'])
def api_cambiar_rol():
    if session.get('usuario_rol') != 1:
        return jsonify({"ok": False, "mensaje": "Acceso denegado"}), 403
    datos = request.get_json() or {}
    id_usuario = datos.get('id_usuario')
    nuevo_rol = datos.get('nuevo_rol')
    
    exito, msj = crud_user.actualizar_rol_usuario(id_usuario, nuevo_rol)
    return jsonify({"ok": exito, "mensaje": msj})

# -------------------------------------------------------------
# RUTAS API DE PRODUCTOS
# -------------------------------------------------------------
# Listar productos (público)
@app.route('/api/productos', methods=['GET'])
def listar_productos():
    try:
        productos = crud_prod.obtener_productos()
        return jsonify({"ok": True, "productos": productos}), 200
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# Crear producto (solo Admin, con subida de imagen)
@app.route('/api/productos', methods=['POST'])
def crear_producto():
    if session.get('usuario_rol') != 1:
        return jsonify({"ok": False, "mensaje": "Acceso denegado"}), 403

    try:
        nombre = request.form.get('nombre')
        precio = request.form.get('precio')
        descripcion = request.form.get('descripcion', '')
        stock = request.form.get('stock', 10)
        id_categoria = request.form.get('id_categoria', 1)

        if not nombre or not precio:
            return jsonify({"ok": False, "mensaje": "El nombre y el precio son obligatorios"}), 400

        # Guardar imagen local subida desde el dispositivo
        ruta_imagen = ''
        if 'imagen' in request.files:
            file = request.files['imagen']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                ruta_imagen = f'uploads/{filename}'

        exito, msj = crud_prod.agregar_producto(
            nombre=nombre,
            descripcion=descripcion,
            precio=precio,
            imagen=ruta_imagen,
            stock=stock,
            id_categoria=id_categoria
        )

        if exito:
            return jsonify({"ok": True, "mensaje": "Producto guardado con éxito"}), 201
        return jsonify({"ok": False, "mensaje": msj}), 400

    except Exception as e:
        return jsonify({"ok": False, "mensaje": str(e)}), 500

if __name__ == '__main__':
    print("--------------------------------------------------")
    print("🚀 Servidor iniciado con éxito")
    print("📍 Tienda: http://localhost:5000/")
    print("--------------------------------------------------")
    app.run(debug=True, port=5000)