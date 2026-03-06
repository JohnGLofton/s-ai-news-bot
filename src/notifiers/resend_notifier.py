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
        # Fixed subject format: BHE留学新闻资讯 - YYYY-MM-DD (no language suffix)
        if subject is None:
            today = datetime.now().strftime("%Y-%m-%d")
            subject = f"BHE留学新闻资讯 - {today}"

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

            logger.info(f"Sending email via Resend to {len(self.to_emails)} recipient(s): {', '.join(self.to_emails)}")
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

        # Use fixed heading for email body
        email_heading = "BHE国际教育新闻深度简报"

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', Helvetica, Arial, sans-serif;
                    line-height: 1.6;
                    color: #24292e;
                    max-width: 720px;
                    margin: 0 auto;
                    padding: 10px;
                    background-color: #f6f8fa;
                }}
                .container {{
                    background-color: #ffffff;
                    border-radius: 6px;
                    padding: 16px 20px;
                    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
                }}
                .title {{
                    color: #0366d6;
                    font-size: 22px;
                    font-weight: 700;
                    margin-bottom: 6px;
                    padding-bottom: 8px;
                    border-bottom: 3px solid #0366d6;
                    text-align: center;
                }}
                .date-line {{
                    text-align: center;
                    font-size: 13px;
                    color: #586069;
                    margin-bottom: 12px;
                }}
                .content h1 {{
                    color: #0366d6;
                    font-size: 18px;
                    font-weight: 700;
                    margin-top: 20px;
                    margin-bottom: 8px;
                    padding-bottom: 6px;
                    border-bottom: 2px solid #0366d6;
                }}
                .content h2 {{
                    color: #2c3e50;
                    font-size: 16px;
                    font-weight: 600;
                    margin-top: 16px;
                    margin-bottom: 6px;
                    padding-bottom: 4px;
                    border-bottom: 1px solid #e1e4e8;
                }}
                .content h3 {{
                    color: #24292e;
                    font-size: 14px;
                    font-weight: 600;
                    margin-top: 12px;
                    margin-bottom: 4px;
                    padding-left: 8px;
                    border-left: 3px solid #0366d6;
                }}
                .content p {{
                    margin: 6px 0;
                    line-height: 1.6;
                    font-size: 13px;
                }}
                .content a {{ color: #0366d6; text-decoration: none; }}
                .content hr {{
                    border: none;
                    border-top: 1px solid #e1e4e8;
                    margin: 12px 0;
                }}
                .content strong {{ color: #0366d6; }}
                .content em {{ color: #586069; font-size: 12px; }}
                .content ul, .content ol {{
                    margin: 4px 0;
                    padding-left: 20px;
                }}
                .content li {{
                    margin: 3px 0;
                    font-size: 13px;
                }}
                .footer {{
                    margin-top: 16px;
                    padding-top: 10px;
                    border-top: 1px solid #e1e4e8;
                    text-align: center;
                    font-size: 12px;
                    color: #586069;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="title">{email_heading}</div>
                <div class="date-line">{subject}</div>
                <div class="content">{html_content}</div>
            </div>
            <div class="footer">
                <p>Generated by BHE Bot - <a href="https://www.bhevip.com" style="color:#0366d6;">www.bhevip.com</a></p>
            </div>
        </body>
        </html>
        """
