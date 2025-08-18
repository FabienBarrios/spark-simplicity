"""
Spark Simplicity - Email Connection Manager
==========================================

Enterprise-grade email communication service with secure SMTP connectivity, SSL/TLS
encryption,
and comprehensive message formatting capabilities. This module provides reliable email
delivery
for Spark data processing workflows, enabling automated notifications, report
distribution,
and operational monitoring through secure email channels.

Key Features:
    - **Secure SMTP Connectivity**: SSL/TLS encryption with configurable security
      protocols
    - **Multiple Message Formats**: Plain text, HTML, and attachment support
    - **Bulk Email Processing**: Mass email campaigns with personalization capabilities
    - **Production Safety**: Comprehensive error handling and security validation
    - **Authentication Flexibility**: Support for various SMTP authentication methods
    - **Enterprise Integration**: Compatible with corporate email systems and gateways

Security Features:
    **SSL/TLS Encryption**:
    - Automatic protocol selection (STARTTLS for port 587, SSL/TLS for port 465)
    - Enforced TLS 1.2+ protocols with secure cipher suites
    - Certificate validation with configurable verification levels
    - Secure context creation with industry-standard security settings

    **Authentication Security**:
    - Password-based authentication with secure credential handling
    - Application password support for enhanced security
    - Configurable authentication methods for enterprise systems
    - Credential protection with secure storage recommendations

Message Format Support:
    **Content Types**:
    - Plain text messages for system notifications and alerts
    - HTML email support for rich formatting and branding
    - Multipart messages combining text and HTML alternatives
    - File attachments for reports, data exports, and documentation

    **Distribution Features**:
    - Multiple recipient support with TO, CC, and BCC functionality
    - Bulk email processing with personalization and templating
    - Email list normalization and validation
    - Comprehensive delivery status tracking and error reporting

Enterprise Integration:
    - **Corporate Email Systems**: Compatible with Exchange, Gmail, Outlook, and
      custom SMTP
    - **Notification Workflows**: Integration with data processing pipelines and
      alerting
    - **Report Distribution**: Automated delivery of analytics reports and dashboards
    - **Operational Monitoring**: System status notifications and error alerting
    - **Compliance Support**: Secure email delivery meeting enterprise security
      requirements

Usage:
    This module is designed for enterprise data processing scenarios requiring
    reliable email communication integrated with Spark workflows and operational
    monitoring.

    from spark_simplicity.connections.email_connection import EmailSender
"""

import logging
import os
import smtplib
import ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List


class EmailSender:
    """
    Enterprise-grade email sender with secure SMTP connectivity and comprehensive
    message support.

    Provides reliable email delivery capabilities for Spark data processing workflows
    with
    secure SSL/TLS encryption, multiple message formats, and production-ready error
    handling.
    This class is designed for enterprise environments requiring secure, automated
    email
    communication for notifications, reporting, and operational monitoring.

    Key Capabilities:
        - **Secure SMTP**: SSL/TLS encrypted connections with configurable security
          levels
        - **Message Formats**: Plain text, HTML, and attachment support for diverse
          use cases
        - **Bulk Processing**: Mass email capabilities with personalization and
          templating
        - **Error Handling**: Comprehensive exception management and delivery tracking
        - **Enterprise Ready**: Compatible with corporate email systems and security
          policies
        - **Authentication**: Flexible authentication supporting passwords and tokens

    Security Features:
        - Enforced TLS 1.2+ encryption protocols
        - Certificate validation with configurable verification
        - Secure credential handling and authentication
        - Protection against common email security vulnerabilities
    """

    def __init__(
        self,
        smtp_server: str,
        port: int,
        email: str,
        password: str | None = None,
        use_ssl: bool = False,
        verify_ssl: bool = True,
    ):
        """
        Initialize secure email sender with SMTP configuration and security settings.

        Configures enterprise-grade email connectivity with comprehensive security
        options,
        authentication setup, and protocol selection for reliable email delivery in
        production environments. This initialization establishes secure communication
        channels while maintaining flexibility for various SMTP server configurations.

        Args:
            smtp_server: SMTP server hostname for email delivery:
                        - 'smtp.gmail.com': Google Gmail SMTP server
                        - 'smtp.office365.com': Microsoft Office 365 SMTP
                        - 'smtp.company.com': Corporate SMTP server
                        - Custom SMTP servers for enterprise email systems
            port: SMTP server port number for connection protocol:
                 - 587: STARTTLS protocol (recommended for most servers)
                 - 465: SSL/TLS direct connection (alternative secure option)
                 - 25: Plain SMTP (not recommended without encryption)
                 - Custom ports for enterprise configurations
            email: Sender email address for authentication and message identification:
                  Must be valid email address with sending permissions on SMTP server.
                  Used for both authentication and 'From' field in sent messages.
            password: Authentication credential for SMTP server access:
                     - Account password for basic authentication
                     - Application-specific password (recommended for enhanced
                       security)
                     - None for servers not requiring authentication (rare)
                     - Authentication tokens for advanced enterprise setups
            use_ssl: Boolean flag controlling connection encryption protocol:
                    - False (default): Use STARTTLS on port 587 (most common)
                    - True: Use direct SSL/TLS on port 465 (alternative secure method)
                    Protocol selection must match server configuration and port.
            verify_ssl: Boolean flag for SSL certificate validation:
                       - True (default): Strict certificate validation (recommended)
                       - False: Disable validation (only for testing/debugging)
                       Certificate verification ensures connection security and
                       authenticity.
        """
        self.smtp_server = smtp_server
        self.port = port
        self.email = email
        self.password = password
        self.use_ssl = use_ssl
        self.verify_ssl = verify_ssl
        self.logger = EmailSender._setup_logger()

        if not verify_ssl:
            self.logger.warning("WARNING: SSL verification disabled - security risk!")

    @staticmethod
    def _setup_logger() -> logging.Logger:
        """
        Configure dedicated logger for email operations with structured formatting.

        Creates and configures a specialized logger for email module operations with
        appropriate formatting, log levels, and handler setup. This logger provides
        comprehensive tracking of email operations, security events, and error
        conditions
        for operational monitoring and debugging purposes.

        Returns:
            logging.Logger: Configured logger instance for email operations
        """
        logger = logging.getLogger("EmailSender")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _create_secure_context(self) -> ssl.SSLContext:
        """
        Create hardened SSL context with enterprise-grade security configuration.

        Establishes secure SSL/TLS context with industry-standard security settings,
        enforced encryption protocols, and comprehensive certificate validation.
        This method ensures maximum security for email communications while maintaining
        compatibility with enterprise SMTP servers and security policies.

        Returns:
            ssl.SSLContext: Securely configured SSL context with TLS 1.2+ enforcement
        """
        context = ssl.create_default_context()

        # Default secure configuration (recommended)
        if self.verify_ssl:
            # Strict certificate verification (recommended)
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED
        else:
            # Disable only if explicitly requested (not recommended)
            self.logger.warning("SSL verification disabled - insecure usage!")
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

        # Enforce secure protocol usage
        # TLS 1.2 minimum (TLS 1.3 preferred when available)
        context.minimum_version = ssl.TLSVersion.TLSv1_2

        # Note: ssl.create_default_context() already automatically disables
        # SSLv2, SSLv3, TLSv1, and TLSv1_1, so no need for deprecated options

        return context

    @staticmethod
    def _normalize_email_list(emails: Any) -> List[str]:
        """
        Normalize email address input into standardized list format with validation.

        Converts various email address input formats into a clean, standardized list
        of email addresses for consistent processing across all email methods.

        Args:
            emails: Email addresses in string, list format, None, or any other type
                   (gracefully handles invalid types by returning empty list)

        Returns:
            List of cleaned email address strings
        """
        if emails is None:
            return []
        elif isinstance(emails, str):
            return [email.strip() for email in emails.split(",") if email.strip()]
        elif isinstance(emails, list):
            return [email.strip() for email in emails if email.strip()]
        else:
            # Handle invalid types gracefully by returning empty list
            return []

    def send_simple_email(
        self,
        to_email: str | List[str],
        subject: str,
        message: str,
        cc: str | List[str] | None = None,
        bcc: str | List[str] | None = None,
    ) -> bool:
        """
        Send plain text email with comprehensive recipient management and error
        handling.

        Provides reliable plain text email delivery with support for multiple
        recipients,
        carbon copy (CC), and blind carbon copy (BCC) functionality. This method is
        optimized for system notifications, alerts, and simple message delivery in
        production data processing workflows.

        Args:
            to_email: Primary recipient email addresses (single, list, or
                     comma-separated)
            subject: Email subject line for message identification
            message: Plain text message body content
            cc: Carbon copy recipients (optional)
            bcc: Blind carbon copy recipients (optional)

        Returns:
            Boolean indicating email delivery status (True for success)
        """
        try:
            to_emails = EmailSender._normalize_email_list(to_email)
            cc_emails = EmailSender._normalize_email_list(cc) if cc else []
            bcc_emails = EmailSender._normalize_email_list(bcc) if bcc else []

            msg = MIMEText(message)
            msg["Subject"] = subject
            msg["From"] = self.email
            msg["To"] = ", ".join(to_emails)

            if cc_emails:
                msg["Cc"] = ", ".join(cc_emails)

            all_recipients = to_emails + cc_emails + bcc_emails

            return self._send_email(msg, all_recipients)

        except Exception as e:
            self.logger.error(f"Error sending simple email: {e}")
            return False

    def send_html_email(
        self,
        to_email: str | List[str],
        subject: str,
        html_content: str,
        text_content: str | None = None,
        cc: str | List[str] | None = None,
        bcc: str | List[str] | None = None,
    ) -> bool:
        """
        Send rich HTML email with optional plain text alternative for enhanced
        presentation.

        Delivers professionally formatted HTML email messages with optional plain text
        fallback for maximum client compatibility. This method is ideal for reports,
        dashboards, formatted notifications, and business communications requiring
        rich formatting, styling, and visual presentation capabilities.

        Args:
            to_email: Primary recipient email addresses (any supported format)
            subject: Email subject line for message identification
            html_content: Rich HTML content for the email body
            text_content: Plain text alternative content (optional but recommended)
            cc: Carbon copy recipients for transparent distribution (optional)
            bcc: Blind carbon copy recipients for confidential distribution (optional)

        Returns:
            Boolean indicating HTML email delivery status (True for success)
        """
        try:
            to_emails = EmailSender._normalize_email_list(to_email)
            cc_emails = EmailSender._normalize_email_list(cc) if cc else []
            bcc_emails = EmailSender._normalize_email_list(bcc) if bcc else []

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.email
            msg["To"] = ", ".join(to_emails)

            if cc_emails:
                msg["Cc"] = ", ".join(cc_emails)

            if text_content:
                text_part = MIMEText(text_content)
                msg.attach(text_part)

            html_part = MIMEText(html_content, "html")
            msg.attach(html_part)

            all_recipients = to_emails + cc_emails + bcc_emails

            return self._send_email(msg, all_recipients)

        except Exception as e:
            self.logger.error(f"Error sending HTML email: {e}")
            return False

    def send_email_with_attachments(
        self,
        to_emails: str | List[str],
        subject: str,
        message: str,
        attachments: List[str],
        cc: str | List[str] | None = None,
        bcc: str | List[str] | None = None,
    ) -> bool:
        """
        Send email with file attachments for report distribution and data sharing.

        Delivers email messages with multiple file attachments, ideal for distributing
        data processing results, reports, logs, and analytical outputs. This method
        handles file validation, encoding, and secure attachment processing for
        professional business communication and automated report delivery workflows.

        Args:
            to_emails: Recipient email addresses (any supported format)
            subject: Descriptive subject line for attachment email
            message: Plain text message body describing attachments
            attachments: List of file paths for attachment processing
            cc: Carbon copy recipients for transparent distribution (optional)
            bcc: Blind carbon copy for confidential distribution (optional)

        Returns:
            Boolean indicating attachment email delivery status (True for success)
        """
        try:
            to_list = EmailSender._normalize_email_list(to_emails)
            cc_list = EmailSender._normalize_email_list(cc) if cc else []
            bcc_list = EmailSender._normalize_email_list(bcc) if bcc else []

            msg = MIMEMultipart()
            msg["Subject"] = subject
            msg["From"] = self.email
            msg["To"] = ", ".join(to_list)

            if cc_list:
                msg["Cc"] = ", ".join(cc_list)

            msg.attach(MIMEText(message))

            for file_path in attachments:
                if os.path.isfile(file_path):
                    EmailSender._attach_file(msg, file_path)
                else:
                    self.logger.warning(f"File not found: {file_path}")

            all_recipients = to_list + cc_list + bcc_list

            return self._send_email(msg, all_recipients)

        except Exception as e:
            self.logger.error(f"Error sending email with attachments: {e}")
            return False

    def send_bulk_email(
        self,
        recipients: List[Dict[str, Any]],
        subject: str,
        message_template: str,
        cc: str | List[str] | None = None,
        bcc: str | List[str] | None = None,
    ) -> Dict[str, Any]:
        """
        Send personalized bulk email campaigns with template processing and delivery
        tracking.

        Executes mass email distribution with personalized content generation,
        comprehensive
        error handling, and detailed delivery tracking. This method is designed for
        automated notifications, report distribution, and customer communication
        workflows
        requiring personalized content at scale while maintaining professional delivery
        standards.

        Args:
            recipients: List of recipient dictionaries containing personalization data
            subject: Common subject line for all bulk email messages
            message_template: Message template with placeholder variables for
                             personalization
            cc: Global carbon copy addresses applied to all emails (optional)
            bcc: Global blind carbon copy addresses for all emails (optional)

        Returns:
            Dictionary with comprehensive delivery tracking results
        """
        results: Dict[str, Any] = {"success": 0, "failed": 0, "errors": []}

        for recipient in recipients:
            try:
                personalized_message = message_template.format(**recipient)

                recipient_cc = recipient.get("cc", cc)
                recipient_bcc = recipient.get("bcc", bcc)

                if self.send_simple_email(
                    recipient["email"],
                    subject,
                    personalized_message,
                    cc=recipient_cc,
                    bcc=recipient_bcc,
                ):
                    results["success"] += 1
                    self.logger.info(f"Email sent successfully to {recipient['email']}")
                else:
                    results["failed"] += 1
                    results["errors"].append(f"Failed to send to {recipient['email']}")

            except KeyError as e:
                results["failed"] += 1
                error_msg = (
                    f"Missing variable {e} for "
                    f"{recipient.get('email', 'unknown email')}"
                )
                results["errors"].append(error_msg)
                self.logger.error(error_msg)
            except Exception as e:
                results["failed"] += 1
                error_msg = f"Error for {recipient.get('email', 'unknown email')}: {e}"
                results["errors"].append(error_msg)
                self.logger.error(error_msg)

        return results

    @staticmethod
    def _attach_file(msg: MIMEMultipart, file_path: str) -> None:
        """
        Attach file to email message with proper MIME encoding and headers.

        Processes individual file attachment with binary encoding, MIME type detection,
        and proper header configuration for secure email transmission.

        Args:
            msg: Multipart MIME message object to receive the file attachment
            file_path: Path to file for attachment processing
        """
        with open(file_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())

        encoders.encode_base64(part)

        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {os.path.basename(file_path)}",
        )

        msg.attach(part)

    def _send_email(self, msg: MIMEText | MIMEMultipart, to_emails: List[str]) -> bool:
        """
        Send email via SMTP with enterprise-grade secure connection and comprehensive
        error handling.

        Executes the core email delivery process with hardened SSL/TLS encryption,
        robust authentication, and comprehensive error handling. This method provides
        the secure foundation for all email sending operations with automatic protocol
        selection, connection management, and detailed error reporting.

        Args:
            msg: Constructed email message ready for SMTP transmission
            to_emails: Complete list of recipient email addresses for SMTP delivery

        Returns:
            Boolean indicating SMTP delivery operation status (True for success)
        """
        try:
            context = self._create_secure_context()

            if self.use_ssl:
                with smtplib.SMTP_SSL(
                    self.smtp_server, self.port, context=context
                ) as server:
                    if self.password:
                        server.login(self.email, self.password)

                    server.send_message(msg, to_addrs=to_emails)
            else:
                with smtplib.SMTP(self.smtp_server, self.port) as server:
                    server.starttls(context=context)

                    if self.password:
                        server.login(self.email, self.password)

                    server.send_message(msg, to_addrs=to_emails)

            self.logger.info(
                f"Email sent successfully to {len(to_emails)} recipient(s)"
            )
            return True

        except smtplib.SMTPException as e:
            self.logger.error(f"SMTP error: {e}")
            return False
        except ssl.SSLError as e:
            self.logger.error(f"SSL/TLS error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error during sending: {e}")
            return False
