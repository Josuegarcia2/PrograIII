import os
from flask import Flask, jsonify, request, render_template, session, redirect, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename
from modulos.crud_productos import CRUDProductos
from modulos.crud_usuarios import CRUDUsuarios

app = Flask(__name__, template_folder='templates', static_folder='static', static_url_path='/static')
app.secret_key = 'clave_secreta_pastelitos_abuela'
CORS(app)


UPLOAD_FOLDER = os.path.join(app.static_folder, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

crud_prod = CRUDProductos()
crud_user = CRUDUsuarios()


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
    if 'usuario_id' not in session or session.get('usuario_rol') != 1:
        return redirect('/')
    return render_template('admin.html', usuario_nombre=session.get('usuario_nombre', 'Administrador'))


@app.route('/api/registro', methods=['POST'])
def api_registro():
    try:
        datos = request.get_json() or {}
        nombre = datos.get('nombre') or datos.get('nombre_completo')
        correo = datos.get('email') or datos.get('correo')
        telefono = datos.get('telefono', '')
        password = datos.get('password')

        print(f"📥 Registro: nombre={nombre}, correo={correo}")

        if not nombre or not correo or not password:
            return jsonify({"ok": False, "mensaje": "Completa todos los campos obligatorios."}), 400

        exito, mensaje = crud_user.registrar_usuario(nombre, correo, telefono, password, id_rol=2)

        if exito:
            usuario, _ = crud_user.autenticar_usuario(correo, password)
            if usuario:
                session['usuario_id'] = usuario.get('id_usuario')
                nombre_u   = usuario.get('nombre', '') or ''
                apellido_u = usuario.get('apellido', '') or ''
                session['usuario_nombre'] = f"{nombre_u} {apellido_u}".strip() or nombre_u or 'Cliente'
                session['usuario_rol'] = usuario.get('id_rol', 2)
                return jsonify({"ok": True, "redirect": "/cliente.html"}), 200

        return jsonify({"ok": False, "mensaje": mensaje}), 400

    except Exception as e:
        print(f"❌ Error en /api/registro: {e}")
        return jsonify({"ok": False, "mensaje": str(e)}), 500

@app.route('/api/login', methods=['POST'])
def api_login():
    print("\n" + "="*55)
    print("🔑 /api/login invocado")
    try:
        datos = request.get_json() or {}
        correo = datos.get('email') or datos.get('correo')
        password = datos.get('password')
        print(f"   correo: {correo!r}")

        if not correo or not password:
            print("   ❌ Faltan credenciales")
            return jsonify({"ok": False, "mensaje": "Ingresa correo y contraseña."}), 400

        usuario, mensaje = crud_user.autenticar_usuario(correo, password)

        if not usuario:
            print(f"   ❌ Credenciales inválidas: {mensaje!r}")
            return jsonify({"ok": False, "mensaje": mensaje}), 401

        session['usuario_id'] = usuario.get('id_usuario')
        nombre_u   = usuario.get('nombre', '') or ''
        apellido_u = usuario.get('apellido', '') or ''
        session['usuario_nombre'] = f"{nombre_u} {apellido_u}".strip() or nombre_u or 'Usuario'
        session['usuario_rol'] = usuario.get('id_rol', 2)

        rol = usuario.get('id_rol')
        redirect_url = '/admin.html' if rol == 1 else '/cliente.html'

        print(f"   ✅ Login OK → {redirect_url} (rol={rol})")
        print("="*55 + "\n")
        return jsonify({"ok": True, "mensaje": "Sesión iniciada", "redirect": redirect_url}), 200

    except Exception as e:
        print(f"   💥 EXCEPCIÓN: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "mensaje": f"Error interno: {e}"}), 500

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({"ok": True, "redirect": "/"}), 200


@app.route('/api/usuarios', methods=['GET'])
def api_listar_usuarios():
    if session.get('usuario_rol') != 1:
        return jsonify({"ok": False, "mensaje": "Acceso denegado"}), 403
    usuarios = crud_user.obtener_todos_usuarios()
    return jsonify({"ok": True, "usuarios": usuarios}), 200

@app.route('/api/usuarios/cambiar_rol', methods=['POST'])
def api_cambiar_rol():
    if session.get('usuario_rol') != 1:
        return jsonify({"ok": False, "mensaje": "Acceso denegado"}), 403
    datos = request.get_json() or {}
    exito, msj = crud_user.actualizar_rol_usuario(datos.get('id_usuario'), datos.get('nuevo_rol'))
    return jsonify({"ok": exito, "mensaje": msj})


@app.route('/api/productos', methods=['GET'])
def listar_productos():
    try:
        productos = crud_prod.obtener_productos()
        return jsonify({"ok": True, "productos": productos}), 200
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

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

        ruta_imagen = ''
        if 'imagen' in request.files:
            file = request.files['imagen']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                ruta_imagen = f'uploads/{filename}'

        exito, msj = crud_prod.agregar_producto(
            nombre=nombre, descripcion=descripcion, precio=precio,
            imagen=ruta_imagen, stock=stock, id_categoria=id_categoria
        )

        if exito:
            return jsonify({"ok": True, "mensaje": "Producto guardado con éxito"}), 201
        return jsonify({"ok": False, "mensaje": msj}), 400

    except Exception as e:
        return jsonify({"ok": False, "mensaje": str(e)}), 500


@app.route('/api/chat', methods=['POST'])
def api_chat():
    try:
        data = request.get_json() or {}
        mensaje = (data.get('mensaje') or '').lower().strip()

        if not mensaje:
            return jsonify({
                "ok": False,
                "respuesta": "¡Hola, mi corazón! Escribe o selecciona una pregunta para poder ayudarte 👵🏼"
            }), 200

       
        if any(p in mensaje for p in ['menu', 'menú', 'producto', 'tienen', 'venden', 'catalogo']):
            respuesta = (
                "Nuestro menú incluye:\n"
                "• Pastelitos de queso ($0.50)\n"
                "• Pastelitos de pollo ($0.50)\n"
                "• Calzone ($3.50)\n"
                "• Pizza artesanal ($7.00)\n"
                "• Budín casero\n\n"
                "¡Todo hecho con receta de la abuela! 🧡"
            )

      
        elif any(p in mensaje for p in ['sabor', 'sabores', 'relleno', 'variedad']):
            respuesta = (
                "Sabores de pastelitos disponibles:\n"
                "• Queso 🧀\n"
                "• Pollo 🍗\n"
                "• Leche 🥛 (el clásico de la abuela)\n\n"
                "También tenemos calzone, pizza y budín casero."
            )

      
        elif 'budin' in mensaje or 'budín' in mensaje:
            respuesta = (
                "Nuestro budín es casero, esponjoso y hecho con receta de la abuela. "
                "Pregúntanos por los sabores disponibles del día 🍞"
            )

        
        elif any(p in mensaje for p in ['precio', 'cuanto', 'cuánto', 'cuesta', 'vale', 'costo']):
            respuesta = (
                "Nuestros precios:\n"
                "• Pastelitos: $0.50 c/u\n"
                "• Calzone: $3.50\n"
                "• Pizza: $7.00\n\n"
                "¡Siempre con ingredientes frescos! 🥰"
            )

        
        elif any(p in mensaje for p in ['pedido', 'pedir', 'comprar', 'compra', 'ordenar', 'carrito']):
            respuesta = (
                "¡Hacer tu pedido es muy fácil!\n"
                "1️⃣ Elige tus productos del catálogo\n"
                "2️⃣ Agrégalos al carrito\n"
                "3️⃣ Regístrate o inicia sesión\n"
                "4️⃣ Confirma tu pedido y nosotros lo preparamos 🧡"
            )

       
        elif any(p in mensaje for p in ['ingrediente', 'hecho', 'hechos', 'preparan', 'masa', 'relleno']):
            respuesta = (
                "Nuestros pastelitos se preparan con masa artesanal y "
                "queso fresco de la casa. ¡Receta original de la abuela, "
                "sin conservantes! 🌾"
            )

        
        elif any(p in mensaje for p in ['combo', 'promo', 'promoción', 'descuento', 'oferta']):
            respuesta = (
                "🎁 Promociones especiales:\n"
                "• Docena de pastelitos con precio especial\n"
                "• Combos familiares (pizza + pastelitos)\n\n"
                "Escríbenos por WhatsApp para ver las promos vigentes."
            )

       
        elif any(p in mensaje for p in ['recomiend', 'mas vendido', 'más vendido', 'favorito', 'popular']):
            respuesta = (
                "⭐ Lo más pedido:\n"
                "1. Pastelito de queso (el clásico)\n"
                "2. Pastelito de pollo\n"
                "3. Pizza artesanal\n\n"
                "¡No te vas a arrepentir! 😋"
            )

        
        elif any(p in mensaje for p in ['gluten', 'celiac', 'vegetarian', 'vegan', 'sin carne']):
            respuesta = (
                "Por ahora no tenemos línea sin gluten certificada, pero sí "
                "opciones vegetarianas (queso, pizza de vegetales). "
                "Consúltanos por WhatsApp para detalles 🌱"
            )

        
        elif any(p in mensaje for p in ['pago', 'pagar', 'tarjeta', 'efectivo', 'transferencia']):
            respuesta = (
                "Formas de pago aceptadas:\n"
                "💵 Efectivo\n"
                "💳 Tarjeta (débito/crédito)\n"
                "🏦 Transferencia bancaria\n"
                "📱 Pago coordinado por WhatsApp"
            )

        elif any(p in mensaje for p in ['delivery', 'domicilio', 'envio', 'envío', 'entrega', 'reparto']):
            respuesta = (
                "🛵 Sí, hacemos entregas a domicilio.\n"
                "Zonas y costos se confirman por WhatsApp según tu ubicación.\n"
                "También puedes retirar en tienda sin costo."
            )

       
        elif any(p in mensaje for p in ['zona', 'zonas', 'cobertura', 'llegan', 'sector']):
            respuesta = (
                "📍 Cubrimos la zona central y alrededores. "
                "Escríbenos por WhatsApp con tu dirección para confirmar cobertura."
            )

        
        elif any(p in mensaje for p in ['costo envio', 'costo envío', 'cuanto envio', 'cuánto envío', 'cobran envio']):
            respuesta = (
                "El costo de envío depende de tu zona. "
                "Escríbenos por WhatsApp y te lo confirmamos al instante 🛵"
            )

       
        elif any(p in mensaje for p in ['retiro', 'recoger', 'tienda', 'local', 'sucursal']):
            respuesta = (
                "🏪 Puedes retirar en tienda sin costo. "
                "Te avisamos por WhatsApp cuando tu pedido esté listo."
            )

        
        elif any(p in mensaje for p in ['horario', 'hora', 'abren', 'cierran', 'atienden', 'domingo']):
            respuesta = (
                "🕘 Nuestro horario:\n"
                "• Lunes a viernes: 9:00 AM – 8:00 PM\n"
                "• Sábados: 10:00 AM – 6:00 PM\n"
                "• Domingos: cerrado"
            )

        
        elif any(p in mensaje for p in ['stock', 'disponible', 'hay hoy', 'queda']):
            respuesta = (
                "Para confirmar disponibilidad del día, "
                "escríbenos por WhatsApp y te decimos al instante ✅"
            )

        
        elif any(p in mensaje for p in ['tarda', 'demora', 'tiempo', 'cuanto tarda', 'cuánto tarda']):
            respuesta = (
                "⏱️ Tiempo aproximado:\n"
                "• Retiro en tienda: 15–20 min\n"
                "• Delivery: 30–45 min según zona"
            )

        
        elif any(p in mensaje for p in ['minimo', 'mínimo', 'pedido minimo']):
            respuesta = "No tenemos pedido mínimo, ¡puedes ordenar desde 1 pastelito! 🥟"

        
        elif any(p in mensaje for p in ['modificar', 'cambiar pedido', 'cancelar']):
            respuesta = (
                "Si tu pedido aún no está en preparación, sí podemos modificarlo o cancelarlo. "
                "Escríbenos por WhatsApp lo antes posible 📱"
            )

       
        elif any(p in mensaje for p in ['registrar', 'registro', 'cuenta', 'crear cuenta']):
            respuesta = (
                "Registrarte es gratis y rápido:\n"
                "1️⃣ Haz clic en 'iniciar sesión'\n"
                "2️⃣ Pestaña 'Registrarse'\n"
                "3️⃣ Llena tus datos y listo ✅"
            )

       
        elif any(p in mensaje for p in ['contraseña', 'password', 'olvide', 'olvidé']):
            respuesta = (
                "Si olvidaste tu contraseña, escríbenos por WhatsApp "
                "y te ayudamos a recuperar tu cuenta 🔑"
            )

        
        elif any(p in mensaje for p in ['historial', 'mis pedidos', 'pedidos anteriores']):
            respuesta = (
                "Puedes ver tu historial de pedidos iniciando sesión "
                "en tu cuenta de cliente 📜"
            )

        
        elif any(p in mensaje for p in ['whatsapp', 'numero', 'número', 'telefono', 'teléfono', 'contacto']):
            respuesta = (
                "📱 Contáctanos:\n"
                "• WhatsApp: 7000-0000\n"
                "• Email: pastelitosdelaabuela@gmail.com"
            )

        
        elif any(p in mensaje for p in ['facebook', 'instagram', 'redes', 'tiktok']):
            respuesta = (
                "Síguenos en Facebook e Instagram como "
                "'Pastelitos de la Abuela' 🧡"
            )

       
        elif any(p in mensaje for p in ['humano', 'persona', 'agente', 'asesor', 'hablar con alguien']):
            respuesta = (
                "¡Claro! Escríbenos por WhatsApp al 7000-0000 "
                "y te atenderá una persona del equipo 👵🏼"
            )

        
        elif any(p in mensaje for p in ['queja', 'reclamo', 'problema', 'error']):
            respuesta = (
                "Lamentamos el inconveniente 🙏. "
                "Escríbenos por WhatsApp al 7000-0000 y lo resolvemos enseguida."
            )

        
        elif any(p in mensaje for p in ['punto', 'fidelidad', 'premio', 'tarjeta']):
            respuesta = (
                "Estamos preparando un programa de puntos 🎯. "
                "¡Muy pronto podrás acumular y canjear premios!"
            )

        
        elif any(p in mensaje for p in ['evento', 'cumpleaño', 'cumpleaños', 'fiesta', 'encargo']):
            respuesta = (
                "¡Sí! Hacemos pedidos especiales para eventos y cumpleaños 🎉. "
                "Escríbenos con anticipación por WhatsApp para cotizar."
            )

        
        elif any(p in mensaje for p in ['gracias', 'grax', 'thanks']):
            respuesta = "¡De nada, mi corazón! Que disfrutes tus pastelitos 🧡👵🏼"

       
        elif any(p in mensaje for p in ['hola', 'buenas', 'buenos', 'hey', 'saludo']):
            respuesta = (
                "¡Hola, mi corazón! 👵🏼 ¿En qué te puedo ayudar?\n"
                "Puedes preguntarme por el menú, precios, cómo comprar o ingredientes."
            )

        
        else:
            respuesta = (
                "Mmm, no estoy segura de eso, pero puedo ayudarte con:\n"
                "• 📋 Menú y productos\n"
                "• 💲 Precios\n"
                "• 🛒 Cómo hacer tu pedido\n"
                "• 🌾 Ingredientes\n"
                "• 🛵 Delivery\n"
                "• 💳 Formas de pago\n\n"
                "Prueba con una de esas opciones 😊"
            )

        return jsonify({"ok": True, "respuesta": respuesta}), 200

    except Exception as e:
        print(f"❌ Error en /api/chat: {e}")
        return jsonify({
            "ok": False,
            "respuesta": "Ups, ocurrió un error. Intenta de nuevo."
        }), 500

# -------------------------------------------------------------
# INICIO DEL SERVIDOR
# -------------------------------------------------------------
if __name__ == '__main__':
    print("--------------------------------------------------")
    print("🚀 Servidor iniciado con éxito")
    print("📍 Tienda: http://localhost:5000/")
    print("📍 Admin:  http://localhost:5000/admin.html")
    print("📂 Uploads: " + UPLOAD_FOLDER)
    print("💬 Chat (reglas): http://localhost:5000/api/chat  (POST)")
    print("--------------------------------------------------")
    app.run(debug=True, port=5000)