# email_service.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email_config import EMAIL_ADDRESS, EMAIL_PASSWORD, SMTP_SERVER, SMTP_PORT

def send_approval_email(application):
    """Send approval email to student"""
    try:
        subject = f"✅ HMC Hostel Application Approved - #{application['app_id']}"
        
        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .container {{ max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px; }}
                .header {{ background: #2c3e50; color: white; padding: 10px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ padding: 20px; }}
                .details {{ background: #f8f9fa; padding: 15px; border-radius: 10px; margin: 15px 0; }}
                .footer {{ text-align: center; font-size: 12px; color: #666; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🏢 HMC Godavari/Yamuna Hostel</h2>
                    <p>Defence Institute of Advanced Technology, Pune</p>
                </div>
                <div class="content">
                    <h3>Dear {application['applicant_name']},</h3>
                    <p>Your room booking application has been <strong style="color: #27ae60;">APPROVED</strong>!</p>
                    
                    <div class="details">
                        <h4>📋 Booking Details:</h4>
                        <p><strong>Application ID:</strong> #{application['app_id']}</p>
                        <p><strong>Room Required:</strong> {application.get('rooms_required', 1)} room(s)</p>
                        <p><strong>From:</strong> {application.get('from_date', 'N/A')}</p>
                        <p><strong>To:</strong> {application.get('to_date', 'N/A')}</p>
                        <p><strong>Purpose:</strong> {application.get('purpose', 'N/A')}</p>
                    </div>
                    
                    <p>Thank you for choosing HMC Hostel!</p>
                    <p><strong>Wishing you a pleasant stay! 🏨</strong></p>
                </div>
                <div class="footer">
                    <p>© 2024 HMC Hostel, DIAT Pune | This is an auto-generated email</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = application['email']
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Email sent to {application['email']}")
        return True
        
    except Exception as e:
        print(f"❌ Email failed: {e}")
        return False

def send_rejection_email(application):
    """Send rejection email to student"""
    try:
        subject = f"❌ HMC Hostel Application Update - #{application['app_id']}"
        
        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .container {{ max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px; }}
                .header {{ background: #e74c3c; color: white; padding: 10px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ padding: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🏢 HMC Godavari/Yamuna Hostel</h2>
                    <p>Defence Institute of Advanced Technology, Pune</p>
                </div>
                <div class="content">
                    <h3>Dear {application['applicant_name']},</h3>
                    <p>We regret to inform you that your room booking application has been <strong style="color: #e74c3c;">REJECTED</strong>.</p>
                    
                    <p><strong>Application ID:</strong> #{application['app_id']}</p>
                    
                    <p>Please contact the admin for more details.</p>
                    <p>You can submit a new application if needed.</p>
                    
                    <p>Thank you for your understanding.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = application['email']
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Rejection email sent to {application['email']}")
        return True
        
    except Exception as e:
        print(f"❌ Email failed: {e}")
        return False