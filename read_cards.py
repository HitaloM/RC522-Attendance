import csv
import datetime
import os
import sqlite3
import threading
import time
import tkinter as tk

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


class App(tk.Tk):
    def __init__(self, master):
        # Criar frames
        self.frame_left = tk.Frame(master)
        self.frame_right = tk.Frame(master)

        # Adicionar frames ao widget principal
        self.frame_left.pack(side="left", fill="both", expand=True)
        self.frame_right.pack(side="right", fill="both", expand=True)

        # Criar elementos na esquerda
        self.image = tk.PhotoImage(file="image.png")
        self.image_label = tk.Label(self.frame_left, image=self.image)
        self.image_label.pack(side="left", fill="both", expand=True)

        self.time_divider = tk.Frame(self.frame_right, height=2, bd=1, relief="sunken")
        self.date_divider = tk.Frame(self.frame_right, height=2, bd=1, relief="sunken")

        self.name_label = tk.Label(
            self.frame_right, text="Nome:", font=("Helvetica", 20)
        )
        self.name_label.grid(row=0, column=0)
        self.name = tk.Label(self.frame_right, text="", font=("Helvetica", 20))
        self.name.grid(row=0, column=1)

        self.enter_label = tk.Label(
            self.frame_right, text="Entrada:", font=("Helvetica", 20)
        )
        self.enter_label.grid(row=1, column=0)
        self.enter = tk.Label(self.frame_right, text="", font=("Helvetica", 20))
        self.enter.grid(row=1, column=1)

        self.left_label = tk.Label(
            self.frame_right, text="Saída:", font=("Helvetica", 20)
        )
        self.left_label.grid(row=2, column=0)
        self.left = tk.Label(self.frame_right, text="", font=("Helvetica", 20))
        self.left.grid(row=2, column=1)

        self.time_label = tk.Label(
            self.frame_right, text="Tempo:", font=("Helvetica", 20)
        )
        self.time_label.grid(row=3, column=0)
        self.time = tk.Label(self.frame_right, text="", font=("Helvetica", 20))
        self.time.grid(row=3, column=1)

        self.date_label = tk.Label(
            self.frame_right, text="Data:", font=("Helvetica", 20)
        )
        self.date_label.grid(row=4, column=0)
        self.date = tk.Label(self.frame_right, text="", font=("Helvetica", 20))
        self.date.grid(row=4, column=1)

        self.update_info("", "", "", "", "")

    def update_info(self, name, enter, left, time, date):
        self.name.configure(text=name)
        self.enter.configure(text=enter)
        self.left.configure(text=left)
        self.time.configure(text=time)
        self.date.configure(text=date)


# Criar widget principal
tkui = tk.Tk()
# Criar instância da classe
iterface = App(tkui)


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
    with open(filename, "a", newline="") as csvfile:
        # Crie um objeto de escrita para o arquivo CSV
        csv_writer = csv.writer(csvfile)

        # Escreva as linhas no arquivo CSV
        csv_writer.writerow(lines)


def ativar_servo():
    # Configure o pino do servo motor
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(37, GPIO.OUT)

    # Crie um objeto PWM para controlar o servo motor
    servo = GPIO.PWM(37, 50)

    # Inicie o PWM com a frequência de 50 Hz
    servo.start(0)

    # Faça o servo motor girar 90 graus
    servo.ChangeDutyCycle(2.5)
    time.sleep(6)

    # Retorne o servo motor para a posição inicial de 0 graus
    servo.ChangeDutyCycle(7.5)
    time.sleep(1)

    # Interrompa o PWM
    servo.stop()


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
        tkui.update()
        # Lê a ID do cartão RFID
        id, text = reader.read()
        # Busca a ID do cartão no banco de dados
        cursor.execute("SELECT * FROM usuarios WHERE id=?", (id,))
        if usuario := cursor.fetchone():
            # Se o campo entrada está vazio, a pessoa está entrando
            if usuario[2] is None:
                print(f"Bem-vindo, {usuario[1]}!")
                # Armazena a hora atual no campo entradad do banco de dados
                entrada = datetime.datetime.now().strftime("%H:%M:%S")
                cursor.execute(
                    "UPDATE usuarios SET entrada=? WHERE id=?",
                    (entrada, id),
                )
                verde = LedThread(12)  # Cria uma thread para o LED verde
                verde.start()  # Inicia a thread
                # Define as novas informações na interface gráfica
                iterface.update_info(
                    name=usuario[1],
                    enter=entrada,
                    left="",
                    time="",
                    date=datetime.date.today().strftime("%d/%m/%Y"),
                )
                # ativar_servo()
            else:
                print(f"Até logo, {usuario[1]}!")
                entrada = usuario[2]  # Armazena a hora de entrada antes de ser limpada
                # Limpa o campo entrada
                cursor.execute("UPDATE usuarios SET entrada=NULL WHERE id=?", (id,))
                leftime = datetime.datetime.now().strftime("%H:%M:%S")
                # Adiciona ID, nome, entrada e saída no arquivo csv
                line = [id, usuario[1], usuario[2], leftime]
                line_str = map(str, line)
                add_line_to_csv(line_str)
                azul = LedThread(36)  # Cria uma thread para o LED azul
                azul.start()  # Inicia a thread
                # calcula a diferença entre a hora de entrada e saída
                time_diff = datetime.datetime.strptime(
                    leftime, "%H:%M:%S"
                ) - datetime.datetime.strptime(entrada, "%H:%M:%S")
                # Define as novas informações na interface gráfica
                iterface.update_info(
                    name=usuario[1],
                    enter=usuario[2],
                    left=leftime,
                    time=time_diff,
                    date=datetime.date.today().strftime("%d/%m/%Y"),
                )
                # ativar_servo()
            db.commit()  # Salva as alterações no banco de dados
            # Aplica as alterações na interface gráfica
            tkui.update()
        else:
            print("ID de cartão não encontrado.")
            vermelho = LedThread(7)  # Cria uma thread para o LED vermelho
            vermelho.start()  # Inicia a thread
except KeyboardInterrupt:  # Se o usuário pressionar Ctrl+C
    print("Programa encerrado.")
finally:
    # Fecha a conexão com o banco de dados
    db.close()
    # Limpa os pinos do GPIO ao encerrar o programa
    GPIO.cleanup()
