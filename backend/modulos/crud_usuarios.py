import hashlib
import hmac
from werkzeug.security import generate_password_hash, check_password_hash
from modulos.conexion import Conexion


def _cerrar(cursor, instancia):
    if cursor is not None:
        try:
            cursor.close()
        except Exception:
            pass
    instancia.desconectar()


def _es_hash_antiguo(valor):
    return len(valor) == 64 and all(c in "0123456789abcdef" for c in valor.lower())


class CRUDUsuarios:
    def __init__(self):
        pass

    # 
    # Contraseñas
    def hash_password(self, password):
        return generate_password_hash(password)

    def _hash_antiguo(self, password):
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def _verificar_password(self, password, guardado):
        """Devuelve (ok, necesita_migrar)."""
        if not guardado:
            return False, False
        if _es_hash_antiguo(guardado):
            ok = hmac.compare_digest(self._hash_antiguo(password), guardado.lower())
            return ok, ok
        try:
            return check_password_hash(guardado, password), False
        except Exception:
            return False, False

    # Registro / login
    
    def registrar_usuario(self, nombre_completo, correo, telefono, password, id_rol=2):
        instancia = Conexion()
        conn = instancia.conectar()
        if not conn:
            return False, "Error de conexión a MySQL."

        cursor = None
        try:
            correo = correo.strip().lower()
            cursor = conn.cursor()
            cursor.execute("SELECT id_usuario FROM usuarios WHERE correo = %s", (correo,))
            if cursor.fetchone():
                return False, "El correo electrónico ya está registrado."

            partes = nombre_completo.strip().split(" ", 1)
            nombre = partes[0]
            apellido = partes[1] if len(partes) > 1 else ""

            sql = """
                INSERT INTO usuarios (nombre, apellido, correo, telefono, password, id_rol, estado)
                VALUES (%s, %s, %s, %s, %s, %s, 1)
            """
            cursor.execute(sql, (nombre, apellido, correo, telefono or "",
                                 self.hash_password(password), id_rol))
            conn.commit()
            return True, "Registro exitoso"
        except Exception as e:
            conn.rollback()
            print(f"Error al registrar usuario: {e}")
            return False, "No se pudo completar el registro."
        finally:
            _cerrar(cursor, instancia)

    def autenticar_usuario(self, correo, password):
        instancia = Conexion()
        conn = instancia.conectar()
        if not conn:
            return None, "Error de conexión."

        cursor = None
        try:
            correo = (correo or "").strip().lower()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT id_usuario, nombre, apellido, correo, password, id_rol, estado "
                "FROM usuarios WHERE correo = %s",
                (correo,),
            )
            usuario = cursor.fetchone()
            if not usuario:
                return None, "Correo o contraseña incorrectos."

            ok, migrar = self._verificar_password(password, usuario["password"])
            if not ok:
                return None, "Correo o contraseña incorrectos."

            if usuario["estado"] == 0:
                return None, "Tu cuenta está inactiva."

            if migrar:
                try:
                    cursor.execute(
                        "UPDATE usuarios SET password = %s WHERE id_usuario = %s",
                        (self.hash_password(password), usuario["id_usuario"]),
                    )
                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    print(f"No se pudo migrar el hash de la contraseña: {e}")

            usuario.pop("password", None)
            return usuario, "OK"
        except Exception as e:
            print(f"Error al autenticar: {e}")
            return None, "Error interno al iniciar sesión."
        finally:
            _cerrar(cursor, instancia)

    # Administración de usuarios
    
    def obtener_todos_usuarios(self):
        instancia = Conexion()
        conn = instancia.conectar()
        if not conn:
            return []
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT id_usuario, nombre, apellido, correo, id_rol, estado FROM usuarios"
            )
            return cursor.fetchall()
        except Exception as e:
            print("Error al obtener usuarios:", e)
            return []
        finally:
            _cerrar(cursor, instancia)

    def actualizar_rol_usuario(self, id_usuario, nuevo_rol):
        if nuevo_rol not in (1, 2):
            return False, "Rol no válido."
        instancia = Conexion()
        conn = instancia.conectar()
        if not conn:
            return False, "Error de conexión."
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE usuarios SET id_rol = %s WHERE id_usuario = %s", (nuevo_rol, id_usuario)
            )
            conn.commit()
            return True, "Rol actualizado con éxito."
        except Exception as e:
            conn.rollback()
            print(f"Error al actualizar rol: {e}")
            return False, "No se pudo actualizar el rol."
        finally:
            _cerrar(cursor, instancia)

    def cambiar_estado_usuario(self, id_usuario, estado):
        if estado not in (0, 1):
            return False, "Estado no válido."
        instancia = Conexion()
        conn = instancia.conectar()
        if not conn:
            return False, "Error de conexión."
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE usuarios SET estado = %s WHERE id_usuario = %s", (estado, id_usuario)
            )
            conn.commit()
            return True, "Usuario activado." if estado == 1 else "Usuario desactivado."
        except Exception as e:
            conn.rollback()
            print(f"Error al cambiar estado de usuario: {e}")
            return False, "No se pudo cambiar el estado."
        finally:
            _cerrar(cursor, instancia)