import sqlite3

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

# Configura o leitor RFID
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
        entrada DATETIME,
        image TEXT
    )
    """
)

try:
    while True:
        # Pede o nome da pessoa que está se registrando
        name = input("Digite o nome da pessoa que está se registrando: ")
        image = input("Digite o caminho da imagem da pessoa que está se registrando: ")

        # Lê o cartão RFID
        print("Posicione o cartão RFID no leitor...")
        id, text = reader.read()
        print("ID do cartão:", id)

        # Salva o ID do cartão e o nome da pessoa no banco de dados
        cursor.execute(
            "INSERT INTO usuarios (id, nome, image, entrada) VALUES (?, ?, ?, NULL)",
            (
                id,
                name,
                image,
            ),
        )
        db.commit()

except KeyboardInterrupt:  # Se o usuário pressionar Ctrl+C
    print("Programa encerrado.")
finally:
    # Fecha a conexão com o banco de dados
    db.close()

    # Limpa as conexões com o GPIO
    GPIO.cleanup()
