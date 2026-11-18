from modulos.conexion import Conexion


def _cerrar(cursor, instancia):
    if cursor is not None:
        try:
            cursor.close()
        except Exception:
            pass
    instancia.desconectar()


class CRUDProductos:
    def __init__(self):
        pass

    def obtener_productos(self, solo_activos=True):
        instancia = Conexion()
        conn = instancia.conectar()
        if not conn:
            return []
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            sql = """
                SELECT p.id_producto, p.nombre, p.descripcion, p.precio, p.stock,
                       p.imagen, p.id_categoria, c.nombre AS categoria,
                       p.ingredientes, p.estado
                FROM productos p
                JOIN categorias c ON c.id_categoria = p.id_categoria
            """
            if solo_activos:
                sql += " WHERE p.estado = 1"
            sql += " ORDER BY p.id_producto"
            cursor.execute(sql)
            return cursor.fetchall()
        except Exception as e:
            print(f"Error al obtener productos: {e}")
            return []
        finally:
            _cerrar(cursor, instancia)

    def obtener_categorias(self):
        instancia = Conexion()
        conn = instancia.conectar()
        if not conn:
            return []
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id_categoria, nombre FROM categorias ORDER BY id_categoria")
            return cursor.fetchall()
        except Exception as e:
            print(f"Error al obtener categorías: {e}")
            return []
        finally:
            _cerrar(cursor, instancia)

    def agregar_producto(self, nombre, descripcion, precio, imagen, stock=10,
                         id_categoria=1, ingredientes=""):
        instancia = Conexion()
        conn = instancia.conectar()
        if not conn:
            return False, "Error de conexión a la base de datos."
        cursor = None
        try:
            cursor = conn.cursor()
            sql = """
                INSERT INTO productos
                    (nombre, descripcion, precio, stock, imagen, id_categoria, ingredientes, estado)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
            """
            cursor.execute(sql, (nombre, descripcion, precio, stock, imagen,
                                 id_categoria, ingredientes))
            conn.commit()
            return True, "Producto guardado correctamente."
        except Exception as e:
            conn.rollback()
            print(f"Error al agregar producto: {e}")
            return False, "No se pudo guardar el producto. Revisa que la categoría sea válida."
        finally:
            _cerrar(cursor, instancia)

    def actualizar_producto(self, id_producto, nombre, descripcion, precio, stock,
                            id_categoria, ingredientes="", imagen=None):
        instancia = Conexion()
        conn = instancia.conectar()
        if not conn:
            return False, "Error de conexión a la base de datos."
        cursor = None
        try:
            cursor = conn.cursor()
            if imagen:
                sql = """
                    UPDATE productos
                    SET nombre=%s, descripcion=%s, precio=%s, stock=%s,
                        id_categoria=%s, ingredientes=%s, imagen=%s
                    WHERE id_producto=%s
                """
                params = (nombre, descripcion, precio, stock, id_categoria,
                          ingredientes, imagen, id_producto)
            else:
                sql = """
                    UPDATE productos
                    SET nombre=%s, descripcion=%s, precio=%s, stock=%s,
                        id_categoria=%s, ingredientes=%s
                    WHERE id_producto=%s
                """
                params = (nombre, descripcion, precio, stock, id_categoria,
                          ingredientes, id_producto)
            cursor.execute(sql, params)
            conn.commit()
            return True, "Producto actualizado correctamente."
        except Exception as e:
            conn.rollback()
            print(f"Error al actualizar producto: {e}")
            return False, "No se pudo actualizar el producto."
        finally:
            _cerrar(cursor, instancia)

    def desactivar_producto(self, id_producto):
        instancia = Conexion()
        conn = instancia.conectar()
        if not conn:
            return False, "Error de conexión a la base de datos."
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE productos SET estado = 0 WHERE id_producto = %s", (id_producto,))
            conn.commit()
            return True, "Producto quitado del catálogo."
        except Exception as e:
            conn.rollback()
            print(f"Error al desactivar producto: {e}")
            return False, "No se pudo quitar el producto."
        finally:
            _cerrar(cursor, instancia)