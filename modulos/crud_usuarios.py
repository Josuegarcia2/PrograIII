from modulos.conexion import Conexion
import hashlib

class CRUDUsuarios:
    def __init__(self):
        pass

    def hash_password(self, password):
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def registrar_usuario(self, nombre_completo, correo, telefono, password, id_rol=2):
        instancia_conexion = Conexion()
        conn = instancia_conexion.conectar()
        if not conn:
            return False, "Error de conexión a MySQL."

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id_usuario FROM usuarios WHERE correo = %s", (correo,))
            if cursor.fetchone():
                return False, "El correo electrónico ya está registrado."

            partes = nombre_completo.strip().split(" ", 1)
            nombre = partes[0]
            apellido = partes[1] if len(partes) > 1 else ""
            password_hashed = self.hash_password(password)

            sql = """
                INSERT INTO usuarios (nombre, apellido, correo, telefono, password, id_rol, estado)
                VALUES (%s, %s, %s, %s, %s, %s, 1)
            """
            cursor.execute(sql, (nombre, apellido, correo, telefono, password_hashed, id_rol))
            conn.commit()
            return True, "Registro exitoso"
        except Exception as e:
            conn.rollback()
            return False, f"Error SQL: {str(e)}"
        finally:
            cursor.close()
            instancia_conexion.desconectar()

    def autenticar_usuario(self, correo, password):
        instancia_conexion = Conexion()
        conn = instancia_conexion.conectar()
        if not conn:
            return None, "Error de conexión."

        try:
            cursor = conn.cursor(dictionary=True)
            password_hashed = self.hash_password(password)
            sql = "SELECT id_usuario, nombre, apellido, correo, id_rol, estado FROM usuarios WHERE correo = %s AND password = %s"
            cursor.execute(sql, (correo, password_hashed))
            usuario = cursor.fetchone()

            if usuario:
                if usuario['estado'] == 0:
                    return None, "Tu cuenta está inactiva."
                return usuario, "OK"
            return None, "Correo o contraseña incorrectos."
        except Exception as e:
            return None, f"Error SQL: {str(e)}"
        finally:
            cursor.close()
            instancia_conexion.desconectar()

    def obtener_todos_usuarios(self):
        instancia_conexion = Conexion()
        conn = instancia_conexion.conectar()
        if not conn:
            return []
        try:
            cursor = conn.cursor(dictionary=True)
            sql = "SELECT id_usuario, nombre, apellido, correo, id_rol, estado FROM usuarios"
            cursor.execute(sql)
            return cursor.fetchall()
        except Exception as e:
            print("Error al obtener usuarios:", e)
            return []
        finally:
            cursor.close()
            instancia_conexion.desconectar()

    def actualizar_rol_usuario(self, id_usuario, nuevo_rol):
        instancia_conexion = Conexion()
        conn = instancia_conexion.conectar()
        if not conn:
            return False, "Error de conexión."
        try:
            cursor = conn.cursor()
            sql = "UPDATE usuarios SET id_rol = %s WHERE id_usuario = %s"
            cursor.execute(sql, (nuevo_rol, id_usuario))
            conn.commit()
            return True, "Rol actualizado con éxito."
        except Exception as e:
            conn.rollback()
            return False, str(e)
        finally:
            cursor.close()
            instancia_conexion.desconectar()