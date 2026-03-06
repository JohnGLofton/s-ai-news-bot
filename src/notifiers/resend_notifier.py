"""
Email notification module using Resend API
"""
import os
import requests
from typing import Optional, List
from datetime import datetime
from ..logger import setup_logger


logger = setup_logger(__name__)


class ResendNotifier:
    """Send email notifications with news digest using Resend API"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        from_email: Optional[str] = None,
        to_emails: Optional[str] = None,
    ):
        """
        Initialize ResendNotifier.

        Args:
            api_key: Resend API key
            from_email: Sender email address (must be verified in Resend)
            to_emails: Recipient email address(es), comma-separated for multiple
        """
        self.api_key = api_key or os.getenv("RESEND_API_KEY")
        self.from_email = from_email or os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")
        to_str = to_emails or os.getenv("EMAIL_TO", "")
        self.to_emails: List[str] = [e.strip() for e in to_str.split(",") if e.strip()]

        self.api_url = "https://api.resend.com/emails"

        if not self.api_key or not self.to_emails:
            logger.warning(
                "Resend notifier not fully configured. "
                "Required: RESEND_API_KEY, EMAIL_TO"
            )
        else:
            logger.info(f"ResendNotifier initialized (to: {', '.join(self.to_emails)})")

    def send(self, content: str, subject: Optional[str] = None, language: str = "en") -> bool:
        """
        Send email notification with news digest via Resend API.

        Args:
            content: Email body content (news digest in markdown)
            subject: Email subject. If None, uses default with current date
            language: Language code to include in subject

        Returns:
            True if email sent successfully, False otherwise
        """
        if subject is None:
            today = datetime.now().strftime("%Y-%m-%d")
            lang_suffix = f" [{language.upper()}]" if language != "en" else ""
            subject = f"International Study Abroad News Digest - {today}{lang_suffix}"

        if not self.api_key or not self.to_emails:
            logger.error("Resend notifier is not fully configured. Skipping email send.")
            return False

        try:
            html_content = self._create_html_email(content, subject)

            payload = {
                "from": self.from_email,
                "to": self.to_emails,
                "subject": subject,
                "html": html_content,
                "text": content,
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            logger.info(f"Sending email via Resend to {', '.join(self.to_emails)}")
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

            result = response.json()
            logger.info(f"Email sent successfully via Resend (id: {result.get('id', 'unknown')})")
            return True

        except requests.HTTPError as e:
            logger.error(f"Resend API HTTP error: {e.response.status_code} - {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"Failed to send email via Resend: {str(e)}", exc_info=True)
            return False

    def _create_html_email(self, content: str, subject: str) -> str:
        """Create HTML version of email."""
        try:
            import markdown
            html_content = markdown.markdown(
                content,
                extensions=['nl2br', 'tables', 'fenced_code', 'sane_lists']
            )
        except ImportError:
            import html as html_lib
            html_content = html_lib.escape(content).replace('\n', '<br>\n')

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
                    line-height: 1.8;
                    color: #24292e;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f6f8fa;
                }}
                .container {{
                    background-color: #ffffff;
                    border-radius: 8px;
                    padding: 40px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }}
                .title {{
                    color: #0366d6;
                    font-size: 28px;
                    font-weight: 700;
                    margin-bottom: 20px;
                    padding-bottom: 15px;
                    border-bottom: 4px solid #0366d6;
                    text-align: center;
                }}
                .content h1 {{ color: #0366d6; font-size: 24px; margin-top: 36px;
                    padding-bottom: 10px; border-bottom: 3px solid #0366d6; }}
                .content h2 {{ color: #2c3e50; font-size: 20px; margin-top: 30px;
                    padding-bottom: 8px; border-bottom: 2px solid #e1e4e8; }}
                .content h3 {{ color: #24292e; font-size: 17px; margin-top: 24px;
                    padding-left: 12px; border-left: 4px solid #0366d6; }}
                .content p {{ margin: 14px 0; line-height: 1.8; }}
                .content a {{ color: #0366d6; text-decoration: none; }}
                .content hr {{ border: none; border-top: 2px solid #e1e4e8; margin: 28px 0; }}
                .content strong {{ color: #0366d6; }}
                .content em {{ color: #586069; }}
                .content ul, .content ol {{ margin: 12px 0; padding-left: 28px; }}
                .content li {{ margin: 8px 0; }}
                .footer {{
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 2px solid #e1e4e8;
                    text-align: center;
                    font-size: 13px;
                    color: #586069;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="title">{subject}</div>
                <div class="content">{html_content}</div>
            </div>
            <div class="footer">
                <p>Automatically generated by Study Abroad News Bot</p>
            </div>
        </body>
        </html>
        """
