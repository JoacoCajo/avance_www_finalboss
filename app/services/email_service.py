import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
from typing import Optional
from datetime import datetime

load_dotenv()

class EmailService:
    """
    Servicio para envío de correos electrónicos.
    Configurado para usar SMTP (Gmail o Mailtrap).
    """
    
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_user)
        self.from_name = os.getenv("FROM_NAME", "Biblioteca Estación Central")
    
    def send_email(self, to: str, subject: str, html_content: str) -> bool:
        """
        Enviar email genérico.
        Retorna True si fue exitoso, False si falló.
        """
        try:
            # Crear mensaje
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to
            
            # Adjuntar contenido HTML
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Conectar y enviar
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            print(f"✅ Email enviado a {to}: {subject}")
            return True
            
        except Exception as e:
            print(f"❌ Error enviando email a {to}: {str(e)}")
            return False
    
    def send_validation_email(self, to: str, nombre: str, token: str) -> bool:
        """
        Enviar email de validación de cuenta.
        """
        # URL base (ajustar según tu configuración)
        base_url = os.getenv("BASE_URL", "http://localhost:8000")
        activation_link = f"{base_url}/api/v1/usuarios/activar/{token}"
        
        subject = "Activa tu cuenta - Biblioteca Estación Central"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2c3e50; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f4f4f4; }}
                .button {{ 
                    display: inline-block; 
                    padding: 12px 24px; 
                    background-color: #3498db; 
                    color: white; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    margin: 20px 0;
                }}
                .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #777; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📚 Biblioteca Estación Central</h1>
                </div>
                <div class="content">
                    <h2>¡Bienvenido, {nombre}!</h2>
                    <p>Gracias por registrarte en nuestro sistema de préstamos.</p>
                    <p>Para activar tu cuenta, haz clic en el siguiente botón:</p>
                    <p style="text-align: center;">
                        <a href="{activation_link}" class="button">Activar mi cuenta</a>
                    </p>
                    <p>O copia y pega este enlace en tu navegador:</p>
                    <p style="word-break: break-all; color: #3498db;">{activation_link}</p>
                    <p><strong>Este enlace expirará en 24 horas.</strong></p>
                </div>
                <div class="footer">
                    <p>Si no solicitaste esta cuenta, ignora este mensaje.</p>
                    <p>&copy; 2025 Biblioteca Estación Central</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to, subject, html_content)
    
    def send_recordatorio_vencido(self, to: str, nombre: str, prestamos_vencidos: list) -> bool:
        """
        Enviar recordatorio de préstamos vencidos.
        """
        subject = "⚠️ Recordatorio: Tienes préstamos vencidos"
        
        # Generar tabla de préstamos
        tabla_prestamos = ""
        for prestamo in prestamos_vencidos:
            tabla_prestamos += f"""
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;">{prestamo['documento']}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{prestamo['fecha_devolucion']}</td>
                <td style="padding: 10px; border: 1px solid #ddd; color: red; font-weight: bold;">
                    {prestamo['dias_atraso']} días
                </td>
            </tr>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #e74c3c; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f4f4f4; }}
                .warning {{ background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; background: white; }}
                th {{ background-color: #2c3e50; color: white; padding: 12px; text-align: left; }}
                .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #777; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⚠️ Préstamos Vencidos</h1>
                </div>
                <div class="content">
                    <h2>Hola, {nombre}</h2>
                    <p>Este es un recordatorio de que tienes los siguientes préstamos vencidos:</p>
                    
                    <table>
                        <thead>
                            <tr>
                                <th>Documento</th>
                                <th>Fecha de devolución</th>
                                <th>Días de atraso</th>
                            </tr>
                        </thead>
                        <tbody>
                            {tabla_prestamos}
                        </tbody>
                    </table>
                    
                    <div class="warning">
                        <strong>⚠️ Importante:</strong>
                        <p>Por cada día de atraso se aplicarán 2 días de sanción (mínimo 3 días, máximo 30 días).</p>
                        <p>Durante el período de sanción no podrás solicitar nuevos préstamos.</p>
                    </div>
                    
                    <p>Por favor, devuelve los documentos lo antes posible en el mesón de atención.</p>
                </div>
                <div class="footer">
                    <p>Biblioteca Estación Central</p>
                    <p>&copy; 2025 Todos los derechos reservados</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to, subject, html_content)
    
    def send_confirmacion_prestamo(self, to: str, nombre: str, prestamo_info: dict) -> bool:
        """
        Enviar confirmación de préstamo realizado.
        """
        subject = "✅ Confirmación de préstamo - Biblioteca EC"
        
        # Generar lista de documentos
        lista_docs = ""
        for doc in prestamo_info['documentos']:
            lista_docs += f"""
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;">{doc['titulo']}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{doc['autor']}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{doc['fecha_devolucion']}</td>
            </tr>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #27ae60; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f4f4f4; }}
                .info-box {{ background-color: #e8f5e9; border-left: 4px solid #27ae60; padding: 15px; margin: 20px 0; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; background: white; }}
                th {{ background-color: #2c3e50; color: white; padding: 12px; text-align: left; }}
                .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #777; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✅ Préstamo Confirmado</h1>
                </div>
                <div class="content">
                    <h2>Hola, {nombre}</h2>
                    <p>Tu préstamo ha sido registrado exitosamente.</p>
                    
                    <div class="info-box">
                        <strong>Tipo de préstamo:</strong> {prestamo_info['tipo']}<br>
                        <strong>Fecha de préstamo:</strong> {prestamo_info['fecha_prestamo']}<br>
                        <strong>Código de préstamo:</strong> #{prestamo_info['id']}
                    </div>
                    
                    <h3>Documentos prestados:</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Título</th>
                                <th>Autor</th>
                                <th>Fecha de devolución</th>
                            </tr>
                        </thead>
                        <tbody>
                            {lista_docs}
                        </tbody>
                    </table>
                    
                    <p><strong>Recuerda devolver los documentos en la fecha indicada para evitar sanciones.</strong></p>
                </div>
                <div class="footer">
                    <p>Biblioteca Estación Central</p>
                    <p>&copy; 2025 Todos los derechos reservados</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to, subject, html_content)

# Instancia global del servicio
email_service = EmailService()