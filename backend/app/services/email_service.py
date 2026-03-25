from app.core.config import settings
import resend
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.client = None
        if settings.RESEND_API_KEY:
            resend.api_key = settings.RESEND_API_KEY
            self.client = resend
            logger.info("Resend email service initialized")
        else:
            logger.warning("Resend API key not configured - email service disabled")
    
    def send_otp_email(self, to_email: str, otp_code: str) -> bool:
        """
        Send OTP code to admin email
        """
        if not self.client:
            logger.error("Email service not initialized")
            return False
        
        try:
            params = {
                "from": f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>",
                "to": [to_email],
                "subject": "SurePay Admin - Security Code",
                "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background: #0066FF; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
                        <h1 style="color: white; margin: 0;">SurePay</h1>
                    </div>
                    <div style="background: white; padding: 30px; border: 1px solid #eee; border-top: none; border-radius: 0 0 8px 8px;">
                        <h2 style="color: #333;">Admin Security Code</h2>
                        <p>Your security code for this admin action is:</p>
                        <div style="background: #f8f9fa; padding: 20px; text-align: center; border-radius: 8px; margin: 20px 0;">
                            <h1 style="font-size: 32px; letter-spacing: 8px; color: #0066FF; margin: 0;">{otp_code}</h1>
                        </div>
                        <p>This code will expire in 5 minutes.</p>
                        <p style="color: #666; font-size: 14px;">If you did not request this code, please contact security immediately.</p>
                    </div>
                </div>
                """
            }
            
            self.client.Emails.send(params)
            logger.info(f"OTP email sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Error sending OTP email to {to_email}: {str(e)}")
            return False
    
    def send_notification_email(self, to_email: str, subject: str, message: str) -> bool:
        """
        Send notification email
        """
        if not self.client:
            logger.error("Email service not initialized")
            return False
        
        try:
            params = {
                "from": f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>",
                "to": [to_email],
                "subject": subject,
                "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background: #0066FF; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
                        <h1 style="color: white; margin: 0;">SurePay</h1>
                    </div>
                    <div style="background: white; padding: 30px; border: 1px solid #eee; border-top: none; border-radius: 0 0 8px 8px;">
                        <h2 style="color: #333;">{subject}</h2>
                        <div style="color: #555; line-height: 1.6;">
                            {message}
                        </div>
                        <p style="color: #999; font-size: 12px; margin-top: 30px;">
                            This is an automated message from SurePay Admin System.
                        </p>
                    </div>
                </div>
                """
            }
            
            self.client.Emails.send(params)
            logger.info(f"Notification email sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Error sending notification email to {to_email}: {str(e)}")
            return False

# Create singleton instance
email_service = EmailService()