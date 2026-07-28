"""
AI News Generator using configurable LLM providers
"""
from typing import List, Optional, Dict
import json
import re
import time
from ..logger import setup_logger
from ..config import LANGUAGE_NAMES
from .web_search import WebSearchTool, get_search_tool_definition
from .fetcher import NewsFetcher
from ..llm_providers import get_llm_provider


logger = setup_logger(__name__)


class NewsGenerator:
    """Generate AI news digest using configurable LLM providers"""

    def __init__(
        self,
        provider_name: str = "claude",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        enable_web_search: bool = False
    ):
        """
        Initialize the NewsGenerator.

        Args:
            provider_name: Name of LLM provider to use ('claude' or 'deepseek')
            api_key: API key for the provider. If None, will read from environment
            model: Model name to use. If None, uses provider's default model
            enable_web_search: Whether to enable web search tool for fetching current news

        Raises:
            ValueError: If provider is not recognized or API key is not provided
        """
        # Initialize LLM provider
        self.provider = get_llm_provider(
            provider_name=provider_name,
            api_key=api_key,
            model=model
        )

        self.enable_web_search = enable_web_search
        self.search_tool = WebSearchTool() if enable_web_search else None
        self.news_fetcher = NewsFetcher()
        logger.info(
            f"NewsGenerator initialized with {self.provider.provider_name} "
            f"(model: {self.provider.model}, web_search: {enable_web_search})"
        )

    def _generate_with_retry(self, messages, max_tokens=2000, max_retries=3, retry_delay=10):
        """Call LLM with retry on transient failures (429/502/503/524/529)."""
        for attempt in range(max_retries + 1):
            try:
                return self.provider.generate(messages=messages, max_tokens=max_tokens)
            except Exception as e:
                err = str(e)
                is_transient = any(code in err for code in ("429", "502", "503", "524", "529", "rate_limit", "overloaded", "timeout", "origin_response_timeout"))
                if is_transient and attempt < max_retries:
                    wait = retry_delay * (attempt + 1)
                    logger.warning(f"LLM transient error (attempt {attempt+1}/{max_retries+1}), retrying in {wait}s: {err}")
                    time.sleep(wait)
                else:
                    raise

    def _format_news_with_ids(self, news_data: Dict) -> tuple:
        """
        Format news with unique IDs for selection stage.

        Args:
            news_data: Dictionary with 'international' and 'domestic' news lists

        Returns:
            Tuple of (formatted_text, news_items_dict)
        """
        formatted = "# Recent Study Abroad News Items for Selection\n\n"
        news_items = {}  # id -> full news item
        item_id = 1

        if news_data['international']:
            formatted += "## International News\n\n"
            for item in news_data['international']:
                news_id = f"INT-{item_id}"
                news_items[news_id] = item

                formatted += f"### [{news_id}] {item['title']}\n"
                formatted += f"**Source:** {item['source']}\n"
                if item['description']:
                    formatted += f"**Description:** {item['description'][:200]}...\n"
                if item['published']:
                    formatted += f"**Published:** {item['published']}\n"
                formatted += "\n"
                item_id += 1

        if news_data['domestic']:
            formatted += "## Domestic News\n\n"
            item_id = 1
            for item in news_data['domestic']:
                news_id = f"DOM-{item_id}"
                news_items[news_id] = item

                formatted += f"### [{news_id}] {item['title']}\n"
                formatted += f"**Source:** {item['source']}\n"
                if item['description']:
                    formatted += f"**Description:** {item['description'][:200]}...\n"
                if item['published']:
                    formatted += f"**Published:** {item['published']}\n"
                formatted += "\n"
                item_id += 1

        return formatted, news_items

    def _format_digest_from_json(self, digest_json: List[Dict], news_items: Dict, language: str) -> str:
        """
        Format parsed JSON digest into clean markdown text.

        Args:
            digest_json: List of category dicts with 'category' and 'items' keys
            news_items: Dict mapping news IDs to full news items (for source links)
            language: Language code

        Returns:
            Formatted markdown string
        """
        output = ""
        for category in digest_json:
            category_name = category.get("category", "")
            items = category.get("items", [])
            if not category_name or not items:
                continue

            output += f"## {category_name}\n\n"
            for item in items:
                title = item.get("title", "")
                summary = item.get("summary", "")
                source_name = item.get("source_name", "")
                news_id = item.get("id", "")

                # Try to get the source link from original news data
                source_link = ""
                if news_id in news_items:
                    source_link = news_items[news_id].get("link", "")

                output += f"**标题**：{title}\n"
                output += f"**摘要**：{summary}\n"
                if source_link:
                    output += f"**来源**：[{source_name}]({source_link})\n"
                else:
                    output += f"**来源**：{source_name}\n"
                output += "\n"

        return output.strip()

    def generate_news_digest_from_sources(
        self,
        max_tokens: int = 10000,
        language: str = "en",
        max_items_per_source: int = 5,
        stage1_template: Optional[str] = None,
        stage2_template: Optional[str] = None
    ) -> str:
        """
        Fetch real-time news and generate a digest using two-stage prompt chaining:
        Stage 1: Analyze and select 12 high-quality news items
        Stage 2: Create summaries for selected items (returns JSON, code formats it)

        Args:
            max_tokens: Maximum tokens in response
            language: Language code for the response
            max_items_per_source: Maximum items to fetch per source
            stage1_template: Optional Stage 1 prompt template (from config)
            stage2_template: Optional Stage 2 prompt template (from config)

        Returns:
            Generated news digest as string

        Raises:
            Exception: If fetching or generation fails
        """
        try:
            # Fetch real-time news
            logger.info("Fetching real-time AI news from sources...")
            news_data = self.news_fetcher.fetch_recent_news(
                language=language,
                max_items_per_source=max_items_per_source
            )

            if not news_data['international'] and not news_data['domestic']:
                error_msg = "No news items fetched from RSS sources. Please check your network connection or RSS feed availability."
                logger.error(error_msg)
                raise Exception(error_msg)

            # Format news with unique IDs for selection
            formatted_news, news_items = self._format_news_with_ids(news_data)
            total_items = len(news_items)

            logger.info(f"Starting two-stage prompt chaining with {total_items} news items")

            # ============================================================
            # STAGE 1: Selection - Analyze and select 12 best items
            # ============================================================
            logger.info(f"Stage 1: Analyzing and selecting high-quality news items...")

            # Use provided template or load from config
            if stage1_template is None:
                from ..config import Config
                config = Config()
                stage1_template = config.stage1_prompt_template

            # Format Stage 1 prompt with placeholders
            selection_prompt = stage1_template.format(
                formatted_news=formatted_news,
                total_items=total_items
            )

            messages = [
                {"role": "system", "content": "You are a news selection assistant. Your response must contain a JSON array of selected news IDs. Wrap the JSON in ```json ... ``` code blocks if needed. Example: [\"INT-1\", \"INT-5\", \"DOM-2\"]"},
                {"role": "user", "content": selection_prompt}
            ]
            selection_response = self._generate_with_retry(
                messages=messages,
                max_tokens=2000
            )

            # Parse selected IDs
            json_match = re.search(r'\[[\s\S]*?\]', selection_response)
            if not json_match:
                logger.warning("Could not parse JSON from selection response, using fallback")
                selected_ids = list(news_items.keys())[:24]
            else:
                try:
                    selected_ids = json.loads(json_match.group(0))
                    # Validate IDs
                    selected_ids = [id for id in selected_ids if id in news_items]

                    # Target is 24 items (4+4+8+8)
                    target_count = 24
                    if len(selected_ids) < target_count:
                        logger.warning(f"Only {len(selected_ids)} items selected, adding more to reach {target_count}")
                        remaining = [id for id in news_items.keys() if id not in selected_ids]
                        selected_ids.extend(remaining[:target_count - len(selected_ids)])
                    elif len(selected_ids) > target_count + 4:
                        logger.warning(f"{len(selected_ids)} items selected, trimming to {target_count}")
                        selected_ids = selected_ids[:target_count]

                except json.JSONDecodeError:
                    logger.warning("JSON parse error, using fallback selection")
                    selected_ids = list(news_items.keys())[:24]

            logger.info(f"Stage 1 completed: Selected {len(selected_ids)} news items")
            logger.debug(f"Selected IDs: {selected_ids}")

            # ============================================================
            # STAGE 2: Summarization - Return structured JSON
            # ============================================================
            logger.info(f"Stage 2: Creating summaries for selected items (JSON mode)...")

            # Format selected news for summarization - include link for each item
            formatted_selected = "# Selected News Items\n\n"
            for news_id in selected_ids:
                item = news_items[news_id]
                formatted_selected += f"### [{news_id}] {item['title']}\n"
                formatted_selected += f"Source: {item['source']}\n"
                formatted_selected += f"Link: {item['link']}\n"
                if item['description']:
                    formatted_selected += f"Content: {item['description']}\n"
                formatted_selected += "\n"

            # Use provided template or load from config
            if stage2_template is None:
                from ..config import Config
                config = Config()
                stage2_template = config.stage2_prompt_template

            # Format Stage 2 prompt with placeholders
            summarization_prompt = stage2_template.format(
                count=len(selected_ids),
                selected_news=formatted_selected
            )

            # Add language instruction if not English
            if language and language.lower() != "en":
                language_name = LANGUAGE_NAMES.get(language.lower(), language.upper())
                summarization_prompt += f"\n\nIMPORTANT: All titles, summaries, category names, and source names must be in {language_name}."

            # System message: enforce Markdown output directly
            system_message = {
                "role": "system",
                "content": """You are a news editor. Respond with a well-formatted Markdown news digest. No JSON, no explanation, no thinking process, no commentary. Just the Markdown.

Required format:
## Category Name

**标题**：News Title
**摘要**：80-120 word analytical summary
**来源**：[Source Name](https://source.url)

CRITICAL: Output ONLY the Markdown digest. Nothing else. No ```markdown``` blocks. No preamble. No postamble. Each news item must have exactly 3 lines: title, summary, source."""
            }
            messages = [system_message, {"role": "user", "content": summarization_prompt}]
            response_text = self._generate_with_retry(
                messages=messages,
                max_tokens=max_tokens
            )

            # Clean up any markdown code block wrappers
            cleaned = response_text.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r'^```(?:markdown)?\s*\n?', '', cleaned)
                cleaned = re.sub(r'\n?```\s*$', '', cleaned)
                cleaned = cleaned.strip()
            response_text = cleaned

            logger.info(f"Stage 2 completed: News digest generated successfully ({len(response_text)} chars)")
            logger.debug(f"Response preview: {response_text[:200]}...")

            return response_text

        except Exception as e:
            logger.error(f"Failed to generate news digest from sources: {str(e)}", exc_info=True)
            raise

    def _fallback_clean_response(self, text: str) -> str:
        """Fallback: try to clean thinking/reasoning from raw text response."""
        # Find the first category header and cut everything before it
        header_pattern = r'^[\s\S]*?(?=\*{0,2}## [\u4e00-\u9fff])'
        match = re.search(header_pattern, text, re.MULTILINE)
        if match and match.group(0).strip():
            prefix = match.group(0).strip()
            if prefix and not prefix.startswith('##'):
                logger.warning(f"Fallback: stripping {len(prefix)} chars of thinking/reasoning")
                text = text[match.end():]

        # Remove various thinking artifacts
        text = re.sub(r'\n\s*\*Char count[^\n]*', '', text)
        text = re.sub(r'\n\s*\*Char count check\*[^\n]*', '', text)
        text = re.sub(r'\*\*(## [^*]+)\*\*', r'\1', text)

        # Remove leading 4+ space indent
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            if line.startswith('    '):
                line = line.lstrip()
            cleaned_lines.append(line)
        text = '\n'.join(cleaned_lines)

        # Remove multiple consecutive blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text
