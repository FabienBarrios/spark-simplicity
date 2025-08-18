"""
Spark Simplicity - Notification Service
========================================

Email notification service for error reporting and alerts in Spark applications.
This module provides utilities to send beautifully formatted HTML error emails
with stack traces and context information.

Key Features:
    - Professional HTML email templates for error notifications
    - Context information display (job name, environment, parameters)
    - Stack trace formatting with syntax highlighting
    - Easy SMTP configuration and email sending

Usage:
    from spark_simplicity.notification_service import (
        create_email_sender,
        send_error_email,
    )

    sender = create_email_sender(
        "smtp.gmail.com", 587, "alerts@company.com", "password"
    )
    send_error_email(sender, "admin@company.com", exception, {"Job": "ETL_Pipeline"})
"""

import traceback
from datetime import datetime
from typing import Any, Dict, Optional

from .connections.email_connection import EmailSender


def create_email_sender(
    host: str,
    port: int,
    email: str,
    password: Optional[str] = None,
    verify_ssl: bool = True,
) -> EmailSender:
    """
    Create an email sender instance with SMTP configuration.

    Args:
        host: SMTP server hostname
        port: SMTP server port
        email: Sender email address
        password: Email password (optional for some configurations)
        verify_ssl: Whether to verify SSL certificate

    Returns:
        Configured EmailSender instance

    Example:
         sender = create_email_sender(
             "smtp.gmail.com", 587, "alert@company.com", "password"
         )
    """
    return EmailSender(
        smtp_server=host,
        port=port,
        email=email,
        password=password,
        verify_ssl=verify_ssl,
    )


def send_error_email(
    sender: EmailSender,
    recipient: str,
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Send a beautifully formatted HTML error notification email.

    Args:
        sender: EmailSender instance for sending the email
        recipient: Recipient email address
        error: Exception that occurred
        context: Additional context information (job name, parameters, etc.)

    Example:
         context = {"Job": "ETL_Pipeline", "Environment": "Production"}
         send_error_email(
             sender,
             "admin@company.com",
             ValueError("Data validation failed"),
             context,
         )
    """
    context = context or {}

    # Récupérer le nom du job pour le sujet
    job_name = context.get("Job", context.get("job"))

    # Créer le HTML contexte
    context_html = ""
    if context:
        context_items = []
        for k, v in context.items():
            context_items.append(
                f"""
            <div style="
                display: flex;
                justify-content: space-between;
                padding: 8px 0;
                border-bottom: 1px solid #eee;
            ">
                <span style="font-weight: 600; color: #495057;">{k}:</span>
                <span style="color: #6c757d;">{v}</span>
            </div>
            """
            )
        context_html = f"""
        <div style="margin: 20px 0;">
            <h3 style="color: #495057; margin-bottom: 15px; font-size: 18px;">
                📋 Contexte
            </h3>
            <div style="
                background: #f8f9fa;
                border-radius: 8px;
                padding: 15px;
                border-left: 4px solid #007bff;
            ">
                {''.join(context_items)}
            </div>
        </div>
        """

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    margin: 0;
    padding: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
">

    <div style="
        background: white;
        max-width: 700px;
        margin: 0 auto;
        border-radius: 12px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        overflow: hidden;
    ">

        <!-- Header -->
        <div style="
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
            color: white;
            padding: 30px;
            text-align: center;
            position: relative;
        ">
            <span style="font-size: 24px; margin-bottom: 10px;">🚨</span>
            <h1 style="
                margin: 0;
                font-size: 28px;
                font-weight: 300;
                color: black;
            ">Erreur Critique Détectée</h1>
            <p style="
                margin: 5px 0 0 0;
                opacity: 0.9;
                font-size: 14px;
                color: black;
            ">
                {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}
            </p>
            <div style="
                position: absolute;
                top: 0;
                right: 0;
                width: 100px;
                height: 100px;
                background: rgba(255,255,255,0.1);
                border-radius: 50%;
                transform: translate(30px, -30px);
            "></div>
        </div>

        <!-- Content -->
        <div style="padding: 30px;">

            <!-- Error Info -->
            <div style="
                background: linear-gradient(135deg, #ffe8e8 0%, #ffebee 100%);
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 25px;
                border-left: 5px solid #ff5252;
            ">
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                    <span style="font-size: 24px; margin-right: 10px;">⚠️</span>
                    <h2 style="
                        margin: 0;
                        color: #d32f2f;
                        font-size: 20px;
                    ">{type(error).__name__}</h2>
                </div>
                <p style="
                    margin: 0;
                    color: #424242;
                    font-size: 16px;
                    line-height: 1.5;
                ">{str(error)}</p>
            </div>

            {context_html}

            <!-- Stack Trace -->
            <div style="margin: 25px 0;">
                <h3 style="
                    color: #495057;
                    margin-bottom: 15px;
                    font-size: 18px;
                    display: flex;
                    align-items: center;
                ">
                    <span style="margin-right: 8px;">🔍</span>
                    Stack Trace
                </h3>
                <div style="
                    background: #2d3748;
                    border-radius: 8px;
                    padding: 20px;
                    overflow-x: auto;
                    border: 1px solid #4a5568;
                ">
                    <pre style="
                        margin: 0;
                        color: #e2e8f0;
                        font-family: 'Courier New', monospace;
                        font-size: 13px;
                        line-height: 1.4;
                        white-space: pre-wrap;
                    ">
                        {traceback.format_exc()}
                    </pre>
                </div>
            </div>

        </div>

        <!-- Footer -->
        <div style="background: #f8f9fa; padding: 20px; text-align: center;
                    border-top: 1px solid #dee2e6;">
            <p style="margin: 0; color: #6c757d; font-size: 12px;">
                📧 Rapport généré automatiquement | 🔧 Intervention requise
            </p>
        </div>

    </div>

</body>
</html>"""

    # Envoyer l'email avec le nom du job dans le sujet
    sender.send_html_email(
        to_email=recipient,
        subject=f"🚨 {job_name} - Erreur {type(error).__name__}",
        html_content=html,
        text_content=f"Erreur dans {job_name}: {str(error)}",
    )
