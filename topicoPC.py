import time
import psutil
import paho.mqtt.client as mqtt
import mysql.connector
import smtplib
from email.mime.text import MIMEText

# Configuración del broker MQTT y MySQL
mqtt_broker_address = "broker.hivemq.com"
mqtt_port = 1883
mqtt_topic = "cpu/performance"

mysql_host = "localhost"
mysql_user = "root"
mysql_password = "root22"
mysql_database = "prueba"

email_sender = "rendimientopc@gmail.com"
email_password = "rendimientopc123"

# Función para medir el rendimiento de la CPU
def get_cpu_performance():
    return psutil.cpu_percent(interval=1)

# Función de callback cuando se conecta al broker MQTT
def on_connect(client, userdata, flags, rc):
    print("Conectado con código de resultado " + str(rc))

# Función de callback cuando se recibe un mensaje MQTT
def on_message(client, userdata, msg):
    payload = msg.payload.decode().split(',')
    cpu_performance = float(payload[0])
    sender_email = payload[1]

    # Insertar los datos en MySQL
    insert_data_to_mysql(sender_email, cpu_performance)

    # Verificar si el rendimiento es mayor al 40% y enviar correo electrónico al remitente
    if cpu_performance > 40:
        send_email_alert(sender_email, cpu_performance)

# Función para insertar datos en MySQL
def insert_data_to_mysql(sender_email, cpu_performance):
    try:
        connection = mysql.connector.connect(
            host=mysql_host,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database
        )

        cursor = connection.cursor()

        # Crear una tabla si no existe
        cursor.execute("CREATE TABLE IF NOT EXISTS cpu_data (id INT AUTO_INCREMENT PRIMARY KEY, sender_email VARCHAR(255), performance FLOAT)")

        # Insertar los datos de rendimiento en la tabla
        cursor.execute("INSERT INTO cpu_data (sender_email, performance) VALUES (%s, %s)", (sender_email, cpu_performance))

        connection.commit()

    except Exception as e:
        print("Error al insertar datos en MySQL:", e)

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Función para enviar un correo electrónico de alerta al remitente
def send_email_alert(sender_email, cpu_performance):
    try:
        subject = "Alerta de Rendimiento de CPU"
        body = f"Estimado {sender_email},\n\nEl rendimiento de tu CPU es {cpu_performance}%, superior al 40%."

        # Configuración del servidor SMTP de Gmail
        smtp_server = "smtp.gmail.com"
        smtp_port = 587

        # Crear el objeto MIMEText
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = email_sender
        msg["To"] = sender_email

        # Iniciar sesión en el servidor SMTP y enviar el correo electrónico
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email_sender, email_password)
            server.sendmail(email_sender, [sender_email], msg.as_string())

        print(f"Correo electrónico de alerta enviado a {sender_email}.")

    except Exception as e:
        print("Error al enviar el correo electrónico:", e)

# Inicialización del cliente MQTT
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# Conexión al broker MQTT
client.connect(mqtt_broker_address, mqtt_port, 60)
client.subscribe(mqtt_topic)

try:
    client.loop_start()

    while True:
        # Obtener el rendimiento de la CPU
        cpu_performance = get_cpu_performance()

        # Obtener la dirección de correo electrónico del remitente
        sender_email = input("Ingresa tu dirección de correo electrónico: ")

        # Enviar el rendimiento al topic MQTT
        client.publish(mqtt_topic, f"{cpu_performance},{sender_email}")

        # Esperar antes de la próxima medición y publicación
        time.sleep(5)

except KeyboardInterrupt:
    # Manejar la interrupción del teclado (Ctrl+C)
    print("Desconectando del broker MQTT...")
    client.disconnect()
    client.loop_stop()
