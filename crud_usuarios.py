from conexión import obtener_conexion

TABLA = "usuarios_usss046123"


def crud_usuarios_usss046123(datos):
    conexion = obtener_conexion()
    if not conexion: return {"success": False, "error": "Sin conexión a BD"}
    
    try:
        cursor = conexion.cursor()
        sql = f"INSERT INTO {TABLA} (usuario, clave, nombre, `dirección`, `teléfono`) VALUES (%s, %s, %s, %s, %s)"
        valores = (datos['usuario'], datos['clave'], datos['nombre'], datos['direccion'], datos['telefono'])
        cursor.execute(sql, valores)
        conexion.commit()
        return {"success": True, "mensaje": "Usuario registrado"}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        cursor.close()
        conexion.close()

def buscar_usuarios(termino=""):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    if termino:
        sql = f"SELECT * FROM {TABLA} WHERE nombre LIKE %s OR usuario LIKE %s"
        cursor.execute(sql, (f'%{termino}%', f'%{termino}%'))
    else:
        cursor.execute(f"SELECT * FROM {TABLA}")
    resultados = cursor.fetchall()
    cursor.close()
    conexion.close()
    return resultados


def actualizar_usuario(id, datos):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    sql = f"UPDATE {TABLA} SET usuario=%s, clave=%s, nombre=%s, `dirección`=%s, `teléfono`=%s WHERE idUsuario=%s"
    valores = (datos['usuario'], datos['clave'], datos['nombre'], datos['direccion'], datos['telefono'], id)
    cursor.execute(sql, valores)
    conexion.commit()
    cursor.close()
    conexion.close()
    return {"success": True}

def eliminar_usuario(id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(f"DELETE FROM {TABLA} WHERE idUsuario = %s", (id,))
    conexion.commit()
    cursor.close()
    conexion.close()
    return {"success": True}


def validar_login(usuario, clave):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM {TABLA} WHERE usuario = %s AND clave = %s", (usuario, clave))
    user = cursor.fetchone()
    cursor.close()
    conexion.close()
    return user