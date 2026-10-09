from modulos.conexion import Conexion

class CRUDProductos:
    def __init__(self):
        self.db = Conexion()

    def obtener_productos(self):
        conexion = self.db.conectar()
        if not conexion:
            return []
        
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT id_producto, nombre, descripcion, precio, stock, imagen_url, id_categoria FROM productos")
        productos = cursor.fetchall()
        cursor.close()
        self.db.desconectar()
        return productos

    def agregar_producto(self, nombre, descripcion, precio, stock, imagen_url, id_categoria):
        conexion = self.db.conectar()
        if not conexion:
            return False
        
        cursor = conexion.cursor()
        query = """
            INSERT INTO productos (nombre, descripcion, precio, stock, imagen_url, id_categoria)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (nombre, descripcion, precio, stock, imagen_url, id_categoria))
        conexion.commit()
        cursor.close()
        self.db.desconectar()
        return True