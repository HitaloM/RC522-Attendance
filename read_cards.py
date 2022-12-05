import csv
import datetime
import os
import sqlite3
import threading
import time

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

# Inicializar o módulo RFID
reader = SimpleMFRC522()

# Conectar ao banco de dados SQLite
db = sqlite3.connect("database.sqlite")
cursor = db.cursor()

# Cria a tabela usuarios, caso ela não exista
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY,
        nome TEXT,
        entrada DATETIME
    )
    """
)


def add_line_to_csv(lines):
    # Gere o nome do arquivo com base na data atual
    filename = f"presenca_semanal_{datetime.date.today().strftime('%Y-%m-%d')}.csv"

    # Verifica se o arquivo CSV já existe
    if not os.path.exists(filename):
        # Cria o cabeçalho do arquivo CSV
        with open(filename, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["ID", "Nome", "Entrada", "Saída"])

    # Abra o arquivo CSV em modo de escrita
    with open(filename, "w") as csvfile:
        # Crie um objeto de escrita para o arquivo CSV
        csv_writer = csv.writer(csvfile)

        # Escreva as linhas no arquivo CSV
        csv_writer.writerow(lines)


# Cria uma classe que herda de Thread para controlar os LEDs RGB
class LedThread(threading.Thread):
    def __init__(self, pin):
        super().__init__()
        self.pin = pin

    # Define o código que será executado em uma thread separada
    def run(self):
        # Configura o pino do LED como saída
        GPIO.setup(self.pin, GPIO.OUT)
        # Acende o LED
        GPIO.output(self.pin, GPIO.HIGH)
        # Aguarda 3 segundo e depos apaga o LED
        time.sleep(3)
        GPIO.output(self.pin, GPIO.LOW)


try:
    # Continuar lendo os cartões RFID em um loop infinito
    while True:
        # Lê a ID do cartão RFID
        id, text = reader.read()
        # Busca a ID do cartão no banco de dados
        cursor.execute("SELECT * FROM usuarios WHERE id=?", (id,))
        if usuario := cursor.fetchone():
            # Se o campo entrada está vazio, a pessoa está entrando
            if usuario[2] is None:
                print(f"Bem-vindo, {usuario[1]}!")
                # Armazena a hora atual no campo entradad do banco de dados
                cursor.execute(
                    "UPDATE usuarios SET entrada=? WHERE id=?",
                    (datetime.datetime.now(), id),
                )
                verde = LedThread(12)  # Cria uma thread para o LED verde
                verde.start()  # Inicia a thread
            else:
                print(f"Até logo, {usuario[1]}!")
                # Limpa o campo entrada
                cursor.execute("UPDATE usuarios SET entrada=NULL WHERE id=?", (id,))
                # Adiciona ID, nome, entrada e saída no arquivo csv
                line = [id, usuario[1], usuario[2], datetime.datetime.now()]
                line_str = map(str, line)
                add_line_to_csv(line_str)
                azul = LedThread(36)  # Cria uma thread para o LED azul
                azul.start()  # Inicia a thread
            db.commit()  # Salva as alterações no banco de dados
        else:
            print("ID de cartão não encontrado.")
            vermelho = LedThread(7)  # Cria uma thread para o LED vermelho
            vermelho.start()  # Inicia a thread
finally:
    # Fecha a conexão com o banco de dados
    db.close()
    # Limpa os pinos do GPIO ao encerrar o programa
    GPIO.cleanup()
