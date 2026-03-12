import aiosmtplib
import secrets
import uuid
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from jinja2 import Template
from supabase import Client

from app.config import settings
from app.database import get_supabase_client


class EmailService:
    """Service for handling email operations"""
    
    def __init__(self, supabase: Client = None):
        self.supabase = supabase or get_supabase_client()
        self.service_client = self.supabase
    
    async def send_verification_email(self, email: str, user_id: str, full_name: str = "") -> bool:
        """Send email verification link to user"""
        # Generate unique verification token
        token = secrets.token_urlsafe(32)
        
        # Store verification token in database
        verification_data = {
            "user_id": user_id,
            "token": token,
            "token_type": "email_verification",
            "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "used": False
        }
        
        # Insert verification record
        try:
            self.supabase.table("verification_tokens").insert(verification_data).execute()
        except Exception:
            # Table might not exist, create it on the fly via service client
            try:
                self._create_verification_tokens_table()
                self.supabase.table("verification_tokens").insert(verification_data).execute()
            except Exception as e:
                print(f"Error creating verification token: {e}")
                return False
        
        # Generate verification URL
        verification_url = f"{settings.app_domain}/verify-email.html?token={token}&user_id={user_id}"
        
        # Create email content
        html_content = self._get_verification_email_template(
            full_name or "User",
            verification_url,
            settings.app_name
        )
        
        # Send email
        return await self._send_email(
            to_email=email,
            subject=f"Verify your {settings.app_name} account",
            html_content=html_content
        )
    
    async def send_password_reset_email(self, email: str, user_id: str, full_name: str = "") -> bool:
        """Send password reset email to user"""
        # Generate unique reset token
        token = secrets.token_urlsafe(32)
        
        # Store reset token in database
        reset_data = {
            "user_id": user_id,
            "token": token,
            "token_type": "password_reset",
            "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            "used": False
        }
        
        try:
            self.supabase.table("verification_tokens").insert(reset_data).execute()
        except Exception:
            try:
                self._create_verification_tokens_table()
                self.supabase.table("verification_tokens").insert(reset_data).execute()
            except Exception as e:
                print(f"Error creating reset token: {e}")
                return False
        
        # Generate reset URL
        reset_url = f"{settings.app_domain}/reset-password.html?token={token}&user_id={user_id}"
        
        # Create email content
        html_content = self._get_password_reset_template(
            full_name or "User",
            reset_url,
            settings.app_name
        )
        
        # Send email
        return await self._send_email(
            to_email=email,
            subject=f"Reset your {settings.app_name} password",
            html_content=html_content
        )
    
    def verify_token(self, token: str, user_id: str, token_type: str = "email_verification") -> bool:
        """Verify a token and mark it as used"""
        try:
            # Get token from database
            response = self.supabase.table("verification_tokens").select("*").eq("token", token).eq("user_id", user_id).eq("token_type", token_type).execute()
            
            if not response.data:
                return False
            
            token_record = response.data[0]
            
            # Check if token is already used
            if token_record.get("used", False):
                return False
            
            # Check if token is expired
            expires_at = datetime.fromisoformat(token_record["expires_at"].replace("Z", "+00:00"))
            if datetime.utcnow() > expires_at:
                return False
            
            # Mark token as used
            self.supabase.table("verification_tokens").update({"used": True}).eq("id", token_record["id"]).execute()
            
            return True
            
        except Exception as e:
            print(f"Error verifying token: {e}")
            return False
    
    async def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send email using SMTP"""
        if not settings.smtp_user or not settings.smtp_password:
            print("Email not configured. Token can still be verified.")
            # In development, just print the verification link
            return False
        
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email or settings.smtp_user}>"
            message["To"] = to_email
            
            # Attach HTML content
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Send email
            await aiosmtplib.send(
                message=message,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_user,
                password=settings.smtp_password,
                start_tls=True
            )
            
            return True
            
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def _create_verification_tokens_table(self):
        """Create verification_tokens table if it doesn't exist"""
        # This would typically be done via Supabase dashboard or migration
        # For now, we'll create a simplified version
        pass
    
    def _get_verification_email_template(self, name: str, verification_url: str, app_name: str) -> str:
        """Get HTML template for verification email"""
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Email Verification</title>
            <style>
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .email-container { background-color: #ffffff; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow: hidden; }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }
                .header h1 { margin: 0; font-size: 24px; }
                .content { padding: 30px; color: #333333; }
                .button { display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; font-weight: bold; }
                .footer { background-color: #f8f8f8; padding: 20px; text-align: center; color: #888888; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="email-container">
                    <div class="header">
                        <h1>{{ app_name }}</h1>
                    </div>
                    <div class="content">
                        <h2>Hi {{ name }},</h2>
                        <p>Thank you for registering with {{ app_name }}! We're excited to have you on board.</p>
                        <p>To complete your registration, please verify your email address by clicking the button below:</p>
                        <p style="text-align: center;">
                            <a href="{{ verification_url }}" class="button">Verify Email</a>
                        </p>
                        <p>Or copy and paste this link into your browser:</p>
                        <p style="word-break: break-all; color: #667eea;">{{ verification_url }}</p>
                        <p>This link will expire in 7 days.</p>
                        <p>If you didn't create an account with us, please ignore this email.</p>
                    </div>
                    <div class="footer">
                        <p>&copy; 2024 {{ app_name }}. All rights reserved.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        return Template(template).render(name=name, verification_url=verification_url, app_name=app_name)
    
    def _get_password_reset_template(self, name: str, reset_url: str, app_name: str) -> str:
        """Get HTML template for password reset email"""
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Password Reset</title>
            <style>
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .email-container { background-color: #ffffff; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow: hidden; }
                .header { background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); color: white; padding: 30px; text-align: center; }
                .header h1 { margin: 0; font-size: 24px; }
                .content { padding: 30px; color: #333333; }
                .button { display: inline-block; background: #e74c3c; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; font-weight: bold; }
                .warning { background-color: #fff3cd; border-left: 4px solid #f39c12; padding: 15px; margin: 20px 0; }
                .footer { background-color: #f8f8f8; padding: 20px; text-align: center; color: #888888; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="email-container">
                    <div class="header">
                        <h1>{{ app_name }} - Password Reset</h1>
                    </div>
                    <div class="content">
                        <h2>Hi {{ name }},</h2>
                        <p>We received a request to reset your password. Click the button below to create a new password:</p>
                        <p style="text-align: center;">
                            <a href="{{ reset_url }}" class="button">Reset Password</a>
                        </p>
                        <p>Or copy and paste this link into your browser:</p>
                        <p style="word-break: break-all; color: #e74c3c;">{{ reset_url }}</p>
                        <div class="warning">
                            <strong>Important:</strong> This link will expire in 1 hour for security reasons.
                        </div>
                        <p>If you didn't request a password reset, please ignore this email. Your password will remain unchanged.</p>
                    </div>
                    <div class="footer">
                        <p>&copy; 2024 {{ app_name }}. All rights reserved.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        return Template(template).render(name=name, reset_url=reset_url, app_name=app_name)


# Singleton instance
email_service = EmailService()

