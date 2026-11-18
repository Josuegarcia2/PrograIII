import os
import mysql.connector
from mysql.connector import Error


class Conexion:
    

    def __init__(self):
        self.host = os.environ.get("DB_HOST", "localhost")
        self.user = os.environ.get("DB_USER", "root")
        self.password = os.environ.get("DB_PASSWORD", "")
        self.database = os.environ.get("DB_NAME", "pastelitos_abuela")
        self.connection = None

    def conectar(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
            )
            if self.connection.is_connected():
                return self.connection
        except Error as e:
            print(f"Error al conectar con la base de datos: {e}")
        return None

    def desconectar(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()