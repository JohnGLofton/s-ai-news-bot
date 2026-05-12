"""
Email notification module using Resend API
"""
import os
import re
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
        raw_from = from_email or os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")
        # If no display name set, add default display name
        if "<" not in raw_from:
            self.from_email = f"BHE留学资讯 <{raw_from}>"
        else:
            self.from_email = raw_from
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

            # Generate clean plain text version (strip markdown syntax)
            plain_text = self._markdown_to_plain_text(content)

            payload = {
                "from": self.from_email,
                "to": self.to_emails,
                "subject": subject,
                "html": html_content,
                "text": plain_text,
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

    def _markdown_to_plain_text(self, content: str) -> str:
        """Convert markdown content to clean plain text for email text fallback."""
        text = content
        # Remove the footer line (already in HTML template)
        text = re.sub(r'\n---\s*\n\*OpenClaw.*$', '', text)
        # Convert [text](url) → text (url)
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1 (\2)', text)
        # Remove bold markers
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        # Remove italic markers
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        # Clean up ## headers → uppercase section name
        text = re.sub(r'^## (.+)$', r'━━━━━━━━━━━━━━━━━━\n\1\n━━━━━━━━━━━━━━━━━━', text, flags=re.MULTILINE)
        return text

    def _create_html_email(self, content: str, subject: str) -> str:
        """Create HTML version of email with card-style news items."""
        # Strip footer from markdown content (we add it in HTML template)
        clean_content = re.sub(r'\n---\s*\n\*OpenClaw.*$', '', content.strip())

        # Parse markdown into structured news items
        news_items = self._parse_news_items(clean_content)

        # Build HTML from structured data
        html_content = self._render_news_html(news_items)

        # Use fixed heading for email body
        email_heading = "BHE国际教育新闻深度简报"

        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 720px;
            margin: 0 auto;
            padding: 10px;
            background-color: #f0f2f5;
        }}
        .container {{
            background-color: #ffffff;
            border-radius: 8px;
            padding: 0;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        .header {{
            background: linear-gradient(135deg, #1a56db, #0366d6);
            color: #fff;
            padding: 20px 24px 12px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 20px;
            font-weight: 700;
            letter-spacing: 1px;
        }}
        .header .date {{
            font-size: 13px;
            opacity: 0.85;
            margin-top: 4px;
        }}
        .content {{
            padding: 16px 20px;
        }}
        .category {{
            margin-bottom: 24px;
        }}
        .category-header {{
            color: #0366d6;
            font-size: 17px;
            font-weight: 700;
            margin: 0 0 12px 0;
            padding-bottom: 6px;
            border-bottom: 2px solid #0366d6;
            display: flex;
            align-items: center;
        }}
        .category-header .icon {{
            margin-right: 6px;
            font-size: 18px;
        }}
        .news-item {{
            background: #fafbfc;
            border-left: 3px solid #0366d6;
            border-radius: 4px;
            padding: 10px 14px;
            margin-bottom: 10px;
        }}
        .news-item .title {{
            font-size: 14px;
            font-weight: 600;
            color: #1a1a1a;
            margin: 0 0 6px 0;
            line-height: 1.5;
        }}
        .news-item .summary {{
            font-size: 13px;
            color: #444;
            margin: 0 0 6px 0;
            line-height: 1.7;
        }}
        .news-item .source {{
            font-size: 12px;
            margin: 0;
        }}
        .news-item .source a {{
            color: #0366d6;
            text-decoration: none;
        }}
        .news-item .source a:hover {{
            text-decoration: underline;
        }}
        .footer {{
            background: #f6f8fa;
            padding: 12px 20px;
            text-align: center;
            font-size: 12px;
            color: #666;
            border-top: 1px solid #e1e4e8;
        }}
        .footer a {{
            color: #0366d6;
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{email_heading}</h1>
            <div class="date">{subject}</div>
        </div>
        <div class="content">
            {html_content}
        </div>
        <div class="footer">
            BHE留学H6 · <a href="https://www.bhevip.com">WWW.BHEVIP.COM</a>
        </div>
    </div>
</body>
</html>"""

    def _parse_news_items(self, content: str) -> list:
        """Parse markdown content into structured list of (category, items)."""
        categories = []
        # Split by category headers
        parts = re.split(r'^## (.+)$', content, flags=re.MULTILINE)

        # parts[0] is anything before first ## header (usually empty)
        # Then alternating: category_name, content
        for i in range(1, len(parts), 2):
            cat_name = parts[i].strip()
            cat_content = parts[i + 1].strip() if i + 1 < len(parts) else ""

            items = []
            # Split by news items (each starts with **标题)
            item_parts = re.split(r'\*\*标题[：:]\s*', cat_content)
            for j in range(1, len(item_parts)):
                item_text = item_parts[j].strip()
                # Parse title, summary, source
                title = ""
                summary = ""
                source_text = ""
                source_url = ""

                # Extract title (text before **摘要**)
                title_match = re.match(r'(.+?)\n\*\*摘要[：:]', item_text, re.DOTALL)
                if title_match:
                    title = title_match.group(1).strip().rstrip('*').strip()
                    # Remove trailing ** from title if present
                    title = re.sub(r'\*\*$', '', title).strip()

                # Extract summary (between **摘要：** and **来源：**)
                summary_match = re.search(r'\*\*摘要[：:]\*\*\s*(.+?)(?:\n\*\*来源|$)', item_text, re.DOTALL)
                if summary_match:
                    summary = summary_match.group(1).strip()

                # Extract source
                source_match = re.search(r'\*\*来源[：:]\*\*\s*\[([^\]]+)\]\(([^)]+)\)', item_text)
                if source_match:
                    source_text = source_match.group(1)
                    source_url = source_match.group(2)

                if title:
                    items.append({
                        'title': title,
                        'summary': summary,
                        'source_text': source_text,
                        'source_url': source_url,
                    })

            if cat_name:
                categories.append({
                    'name': cat_name,
                    'items': items,
                })

        return categories

    def _render_news_html(self, categories: list) -> str:
        """Render parsed news items into card-style HTML."""
        # Category icons
        icons = {
            '国际新闻': '🌐',
            '国内新闻': '🇨🇳',
            '美国大学招生与国际学生': '🎓',
            '英国大学招生与国际学生': '🇬🇧',
            '留学签证与移民政策': '📋',
            '其他国际教育新闻': '📖',
        }

        html_parts = []
        for cat in categories:
            icon = icons.get(cat['name'], '📰')
            items_html = ""
            for item in cat['items']:
                source_html = ""
                if item['source_text'] and item['source_url']:
                    source_html = f'<p class="source">📎 <a href="{item["source_url"]}" target="_blank">{item["source_text"]}</a></p>'
                elif item['source_text']:
                    source_html = f'<p class="source">📎 {item["source_text"]}</p>'

                items_html += f"""<div class="news-item">
    <div class="title">{item['title']}</div>
    <div class="summary">{item['summary']}</div>
    {source_html}
</div>
"""

            html_parts.append(f"""<div class="category">
    <div class="category-header"><span class="icon">{icon}</span>{cat['name']}</div>
    {items_html}
</div>""")

        return "\n".join(html_parts)
