from modulos.conexion import Conexion

class CRUDProductos:
    def __init__(self):
        pass

    def obtener_productos(self):
        instancia = Conexion()
        conn = instancia.conectar()
        if not conn:
            return []
        try:
            cursor = conn.cursor(dictionary=True)
            sql = "SELECT id_producto, nombre, descripcion, precio, stock, imagen, id_categoria, estado FROM productos WHERE estado = 1"
            cursor.execute(sql)
            return cursor.fetchall()
        except Exception as e:
            print(f"Error al obtener productos: {e}")
            return []
        finally:
            cursor.close()
            instancia.desconectar()

    def agregar_producto(self, nombre, descripcion, precio, imagen, stock=10, id_categoria=1):
        instancia = Conexion()
        conn = instancia.conectar()
        if not conn:
            return False, "Error de conexión a la base de datos."
        try:
            cursor = conn.cursor()
            sql = """
                INSERT INTO productos (nombre, descripcion, precio, stock, imagen, id_categoria, estado)
                VALUES (%s, %s, %s, %s, %s, %s, 1)
            """
            cursor.execute(sql, (nombre, descripcion, precio, stock, imagen, id_categoria))
            conn.commit()
            return True, "Producto guardado correctamente."
        except Exception as e:
            conn.rollback()
            return False, f"Error SQL: {str(e)}"
        finally:
            cursor.close()
            instancia.desconectar()