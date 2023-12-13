-- Crea una base de datos
CREATE DATABASE IF NOT EXISTS rendimiento_pc;

-- Usa la base de datos
USE rendimiento_pc;

-- Crea una tabla para almacenar los datos
CREATE TABLE IF NOT EXISTS datos_pc (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fecha_hora DATETIME,
    mac_address VARCHAR(17),
    rendimiento_cpu FLOAT,
    rendimiento_memoria FLOAT,
    rendimiento_red FLOAT,
    sistema_operativo VARCHAR(50)
);