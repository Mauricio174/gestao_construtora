import threading
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from reportlab.pdfgen import canvas
import schedule
import time

# Configurações do servidor SMTP
EMAIL_HOST = 'email-ssl.com.br'
EMAIL_PORT = 587
EMAIL_USER = 'tijolito@oldservconstrutora.com.br'
EMAIL_PASS = 'Chatgptoldserv24@'

# Inicializa o Flask
app = Flask(__name__)

# Configurações do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gestao_construtora.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Modelo de Usuário
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Modelo de Pagamento
class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    value = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=True)

# Função para enviar e-mails
def send_email(to_email, subject, body, attachment_path, attachment_name):
    try:
        print("Configurando o e-mail...")

        # Configurar o e-mail
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Adicionar o anexo
        with open(attachment_path, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={attachment_name}')
        msg.attach(part)

        # Conectar ao servidor SMTP
        print("Conectando ao servidor SMTP...")
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            print("Autenticando no servidor SMTP...")
            server.login(EMAIL_USER, EMAIL_PASS)
            print("Autenticado com sucesso.")
            server.send_message(msg)
            print(f"E-mail enviado com sucesso para {to_email}.")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")

# Função para gerar o PDF
def generate_pdf():
    output_path = "relatorio_pagamentos.pdf"

    # Calcula o intervalo das últimas 24 horas
    now = datetime.now()
    last_24_hours = now - timedelta(hours=24)

    with app.app_context():  # Garante o contexto de aplicação
        payments = Payment.query.filter(Payment.date >= last_24_hours).all()

    try:
        pdf = canvas.Canvas(output_path)
        pdf.drawString(100, 800, "Relatório de Pagamentos (Últimas 24 Horas)")
        pdf.drawString(100, 780, f"Gerado em: {now.strftime('%d/%m/%Y %H:%M:%S')}")
        y = 750

        if not payments:
            pdf.drawString(50, y, "Nenhum pagamento registrado nas últimas 24 horas.")
        else:
            for payment in payments:
                pdf.drawString(50, y, f"ID: {payment.id} | Data: {payment.date.strftime('%d/%m/%Y %H:%M:%S')} | Valor: R${payment.value:.2f} | Descrição: {payment.description}")
                y -= 20
                if y < 50:  # Adiciona uma nova página se necessário
                    pdf.showPage()
                    y = 750

        pdf.save()
        print(f"PDF gerado em: {output_path}")
        return output_path
    except Exception as e:
        print(f"Erro ao gerar o PDF: {e}")
        return None

# Variável para controlar execução
lock = threading.Lock()

# Função para enviar relatórios às 18h
def send_report():
    with lock:  # Garante que apenas uma instância será executada
        print("Gerando e enviando relatório às 18:00...")
        pdf_path = generate_pdf()
        if pdf_path is None:
            print("Erro: Relatório não foi gerado.")
            return

        today_date = datetime.now().strftime("%d/%m/%Y")
        email_body = f"""Prezado chefe,

Espero que este e-mail o encontre bem!
Segue em anexo o relatório diário de atividades do sistema, referente ao dia {today_date}.

O relatório contém as seguintes informações:

- Interações realizadas por cada usuário.
- Mensagens enviadas e recebidas.
- Pedidos de pagamento e ações relevantes do dia.

Caso precise de algum ajuste ou informação adicional, estarei sempre à disposição para ajudar a otimizar a gestão.

Atenciosamente,
Tijolito
Inteligência Artificial da Oldserv"""

        send_email(
            to_email='mauriciorocha.c@hotmail.com',
            subject='Relatório Diário de Pagamentos',
            body=email_body,
            attachment_path=pdf_path,
            attachment_name='relatorio_pagamentos.pdf'
        )

# Configuração de agendamento
schedule.every().day.at("18:00").do(send_report)

# Thread para rodar o agendamento
def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Bloco principal
if __name__ == '__main__':
    with app.app_context():  # Certifique-se de que está no contexto do app
        db.create_all()  # Cria todas as tabelas definidas no modelo
        print("Banco de dados recriado com sucesso!")

    # Iniciar a thread de agendamento
    schedule_thread = threading.Thread(target=run_schedule, daemon=True)
    schedule_thread.start()

    app.run(debug=True)
