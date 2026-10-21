CREATE DATABASE IF NOT EXISTS db_academica;
USE db_academica;

CREATE TABLE IF NOT EXISTS usuarios_usss046123 (
    idUsuario INT(10) AUTO_INCREMENT PRIMARY KEY,
    usuario CHAR(35) NOT NULL,
    clave CHAR(35) NOT NULL,
    nombre CHAR(85) NOT NULL,
    `dirección` CHAR(100),
    `teléfono` CHAR(9)
);


INSERT INTO usuarios_usss046123 (usuario, clave, nombre, `dirección`, `teléfono`) 
VALUES ('admin', '1234', 'Administrador', 'Oficina Central', '12345678');