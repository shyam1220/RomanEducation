import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import app_config

def send_email(to_email, subject, body):
    """
    Send an email to the specified recipient.
    
    Args:
        to_email (str): Recipient email address
        subject (str): Email subject
        body (str): Email body (HTML format)
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    # Get email configuration
    smtp_server = app_config.SMTP_SERVER
    smtp_port = app_config.SMTP_PORT
    smtp_username = app_config.SMTP_USERNAME
    smtp_password = app_config.SMTP_PASSWORD
    
    # Create message
    message = MIMEMultipart()
    message["From"] = smtp_username
    message["To"] = to_email
    message["Subject"] = subject
    
    # Add body to email
    message.attach(MIMEText(body, "html"))
    
    try:
        # Create SMTP session
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        
        # Send email
        server.send_message(message)
        server.quit()
        return True
    except Exception as e:
        print(f"Email sending error: {e}")
        return False