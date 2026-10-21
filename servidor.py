from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import crud_usuarios

app = Flask(__name__)
app.secret_key = 'clave_secreta_usss046123'

# --- PUNTO 5: LOGIN COMO PÁGINA PRINCIPAL ---
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        datos = request.get_json()
        usuario = datos.get('usuario')
        clave = datos.get('clave')
        
        user = crud_usuarios.validar_login(usuario, clave)
        if user:
            session['usuario'] = user['usuario']
            return jsonify({"success": True, "redirect": "/sistema"})
        return jsonify({"success": False, "mensaje": "Acceso denegado. Credenciales incorrectas."}), 401
        
    return render_template('índice.html', vista='login')

@app.route('/sistema')
def sistema():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('índice.html', vista='sistema')

# --- RUTAS API PARA EL CRUD ---
@app.route('/api/guardar', methods=['POST'])
def api_guardar():
    if 'usuario' not in session: return jsonify({"error": "No autorizado"}), 403
    datos = request.get_json()
    return jsonify(crud_usuarios.crud_usuarios_usss046123(datos))

@app.route('/api/buscar', methods=['GET'])
def api_buscar():
    if 'usuario' not in session: return jsonify({"error": "No autorizado"}), 403
    termino = request.args.get('q', '')
    return jsonify(crud_usuarios.buscar_usuarios(termino))

@app.route('/api/editar/<int:id>', methods=['PUT'])
def api_editar(id):
    if 'usuario' not in session: return jsonify({"error": "No autorizado"}), 403
    datos = request.get_json()
    return jsonify(crud_usuarios.actualizar_usuario(id, datos))

@app.route('/api/eliminar/<int:id>', methods=['DELETE'])
def api_eliminar(id):
    if 'usuario' not in session: return jsonify({"error": "No autorizado"}), 403
    return jsonify(crud_usuarios.eliminar_usuario(id))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)