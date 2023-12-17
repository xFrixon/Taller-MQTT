-- Crea una base de datos
CREATE DATABASE IF NOT EXISTS clientemqtt;

-- Usa la base de datos
USE clientemqtt;

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

-- SELECT * FROM datos_pc;