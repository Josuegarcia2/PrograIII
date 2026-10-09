import mysql.connector
from mysql.connector import Error

class Conexion:
    def __init__(self):
        self.host = "localhost"
        self.user = "root"
        self.password = ""  # Tu contraseña de MySQL si la tienes
        self.database = "pastelitos_abuela"  # <-- Nombre exacto según phpMyAdmin
        self.connection = None

    def conectar(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            if self.connection.is_connected():
                return self.connection
        except Error as e:
            print(f"Error al conectar con la base de datos: {e}")
            return None

    def desconectar(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()