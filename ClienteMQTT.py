import paho.mqtt.client as mqtt
import psutil
import platform
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import uuid
import json
import mysql.connector
from mysql.connector import Error
import re


# Configuración del broker MQTT
broker_address = "broker.hivemq.com"
port = 1883
topic = "metadatos"
#Topico al que se enviará la información
topic_diferencia_metadatos = "topico_a_enviar"

# Configuración del servidor SMTP para enviar correos
smtp_server = "smtp.gmail.com"
smtp_port = 587
smtp_username = "rendimientopc22@gmail.com"
smtp_password = "vieh rqvm ryty bfdn"
recipient_email = "frixonluna2003@gmail.com"

# Configuración de la conexión MySQL
mysql_host = "localhost"
mysql_user = "root"
mysql_password = "root22"
mysql_database = "clientemqtt"

# Función que se ejecuta cuando se conecta al broker
def on_connect(client, userdata, flags, rc):
    print(f"Conectado con código de resultado {rc}")
    client.subscribe(topic)

def on_message(client, userdata, msg):
    print(f"\nMensaje recibido:\n {msg.payload.decode()}")

    try:
        mensaje_json = msg.payload.decode()
        mensaje_dict = json.loads(mensaje_json)

        # Inserta los datos en la base de datos
        try:
            # Conexión a MySQL
            connection = mysql.connector.connect(
                host=mysql_host,
                user=mysql_user,
                password=mysql_password,
                database=mysql_database
            )

            if connection.is_connected():
                db_Info = connection.get_server_info()
                print("Conectado a MySQL Server version ", db_Info)

                cursor = connection.cursor()

                try:
                    # Insertar datos en la tabla
                    cursor.execute("""
                        INSERT INTO datos_pc
                        (fecha_hora, mac_address, rendimiento_cpu, rendimiento_memoria, rendimiento_red, sistema_operativo)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        mensaje_dict["fecha_hora"],
                        mensaje_dict["mac_address"],
                        mensaje_dict["rendimiento_cpu"],
                        mensaje_dict["rendimiento_memoria"],
                        mensaje_dict["rendimiento_red"],
                        mensaje_dict["sistema_operativo"]
                    ))

                    # Hacer commit para guardar los cambios
                    connection.commit()

                    print("Datos insertados en la base de datos.")
                except Error as e:
                    print("Error al insertar datos en la base de datos:", e)
            else:
                print("No se pudo conectar a MySQL.")
        except Error as e:
            print("Error al conectar a MySQL:", e)
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
                print("Conexión a MySQL cerrada.")

    except json.JSONDecodeError as e:
        print("Error al decodificar el mensaje JSON:", e)
    except Exception as e:
        print("Error general:", e)

# Función para obtener el rendimiento del CPU
def obtener_rendimiento_cpu():
    return psutil.cpu_percent(interval=1)

# Función para obtener el rendimiento de la memoria
def obtener_rendimiento_memoria():
    return psutil.virtual_memory().percent

# Función para obtener el rendimiento de la red
def obtener_rendimiento_red():
    return psutil.net_io_counters().bytes_recv / 1024**3

# Función para obtener el sistema operativo
def obtener_sistema_operativo():
    return platform.system()

# Función para enviar un correo de alerta
def enviar_alerta():
    subject = "Alerta: Rendimiento del CPU superior al 40%"
    body = "El rendimiento del CPU ha superado el 40%. Verifica el estado de la computadora."

    # Configuración del mensaje
    msg = MIMEMultipart()
    msg['From'] = smtp_username
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Conexión al servidor SMTP y envío del correo
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_username, recipient_email, msg.as_string())

    print("Correo de alerta enviado.")

# Función para verificar y enviar alerta si el rendimiento del CPU es mayor al 40%
def verificar_y_enviar_alerta(mensaje):
    # Busca la línea que contiene el rendimiento del CPU en el mensaje
    linea_cpu = next((linea for linea in mensaje.split('\n') if 'rendimiento_cpu' in linea), None)

    if linea_cpu:
        try:
            # Utiliza expresiones regulares para extraer solo el valor numérico del rendimiento del CPU
            match = re.search(r'[\d.]+', linea_cpu)
            if match:
                rendimiento_cpu = float(match.group())

                if rendimiento_cpu > 40:
                    enviar_alerta()
                    print("El rendimiento del pc es mayor al 40%, se enviará una alerta a su correo")
            else:
                print("No se encontró un valor numérico en la línea del CPU.")
        except ValueError:
            print("Error al convertir el rendimiento del CPU a un número.")
            print("Mensaje completo:", mensaje)  # Agrega esta línea para depuración


# Función para calcular la diferencia entre dos conjuntos de metadatos y enviarla
def calcular_diferencia_y_enviar(mensaje):
    # Recolecta datos de rendimiento del segundo equipo
    rendimiento_cpu_segundo_equipo = obtener_rendimiento_cpu()
    rendimiento_memoria_segundo_equipo = obtener_rendimiento_memoria()
    rendimiento_red_segundo_equipo = obtener_rendimiento_red()
    sistema_operativo_segundo_equipo = obtener_sistema_operativo()

    # Formatea los datos como un mensaje del segundo equipo
    mensaje_segundo_equipo = (
        f"Rendimiento del CPU (%): {rendimiento_cpu_segundo_equipo}\n"
        f"Rendimiento de la Memoria (%): {rendimiento_memoria_segundo_equipo}\n"
        f"Rendimiento de la Red (GB): {rendimiento_red_segundo_equipo}\n"
        f"Sistema Operativo: {sistema_operativo_segundo_equipo}"
    )

    # Calcula la diferencia entre los dos conjuntos de metadatos
    diferencia_metadatos = "Diferencia en metadatos:\n"
    for linea_equipo1, linea_equipo2 in zip(mensaje.split('\n'), mensaje_segundo_equipo.split('\n')):
        if ':' in linea_equipo1 and ':' in linea_equipo2:
            clave1, valor1 = [parte.strip() for parte in linea_equipo1.split(':')]
            clave2, valor2 = [parte.strip() for parte in linea_equipo2.split(':')]
            if clave1 == clave2:
                try:
                    diferencia = float(valor1.replace('%', '')) - float(valor2.replace('%', ''))
                    diferencia_metadatos += f"{clave1}: {diferencia}\n"
                except ValueError:
                    print(f"Error al calcular la diferencia para {clave1}.")

    # Enviar la diferencia al tópico correspondiente
    client.publish(topic_diferencia_metadatos, diferencia_metadatos)
    print("Diferencia de metadatos enviada:\n", diferencia_metadatos)


# Configuración del cliente MQTT
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# Conexión al broker
client.connect(broker_address, port, 60)
client.loop_start()

try:
    while True:
        # Recolecta datos de rendimiento
        rendimiento_cpu = obtener_rendimiento_cpu()
        rendimiento_memoria = obtener_rendimiento_memoria()
        rendimiento_red = obtener_rendimiento_red()
        sistema_operativo = obtener_sistema_operativo()

        # Obtén la fecha y hora actual
        fecha_hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Obtén la dirección MAC
        mac_address = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(5, -1, -1)])

        # Construye un diccionario con los datos
        datos = {
            "fecha_hora": fecha_hora_actual,
            "mac_address": mac_address,
            "rendimiento_cpu": rendimiento_cpu,
            "rendimiento_memoria": rendimiento_memoria,
            "rendimiento_red": rendimiento_red,
            "sistema_operativo": sistema_operativo
        }

        # Convierte el diccionario a una cadena JSON
        mensaje_json = json.dumps(datos, indent=2)  # Usa indent para formatear la salida JSON

        # Envia el mensaje JSON al broker MQTT
        client.publish(topic, mensaje_json)

        # Limpia el búfer de la consola
        os.system('cls' if os.name == 'nt' else 'clear')

        # Imprime cada línea del mensaje
        print("Mensaje JSON enviado:")
        for linea in mensaje_json.split('\n'):
            print(linea)

        # Verifica y envía una alerta si es necesario
        verificar_y_enviar_alerta(mensaje_json)

        # Espera a que el usuario presione ENTER para enviar el siguiente mensaje
        input("\nPresiona ENTER para enviar el siguiente mensaje...\n")

except KeyboardInterrupt:
    # Desconectar al recibir una interrupción del teclado (Ctrl+C)
    client.disconnect()
    client.loop_stop()

    #Versión 7