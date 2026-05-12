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

    def _generate_with_retry(self, messages, max_tokens=2000, max_retries=2, retry_delay=10):
        """Call LLM with retry on transient failures (429/502/503/529)."""
        for attempt in range(max_retries + 1):
            try:
                return self.provider.generate(messages=messages, max_tokens=max_tokens)
            except Exception as e:
                err = str(e)
                is_transient = any(code in err for code in ("429", "502", "503", "529", "rate_limit", "overloaded"))
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
                    formatted += f"**Description:** {item['description'][:400]}...\n"
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
                    formatted += f"**Description:** {item['description'][:400]}...\n"
                if item['published']:
                    formatted += f"**Published:** {item['published']}\n"
                formatted += "\n"
                item_id += 1

        return formatted, news_items

    def generate_news_digest_from_sources(
        self,
        max_tokens: int = 12000,
        language: str = "en",
        max_items_per_source: int = 5,
        stage1_template: Optional[str] = None,
        stage2_template: Optional[str] = None
    ) -> str:
        """
        Fetch real-time news and generate a digest using two-stage prompt chaining:
        Stage 1: Analyze and select 15-20 high-quality news items
        Stage 2: Create detailed summaries for selected items

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
            # STAGE 1: Selection - Analyze and select 15-20 best items
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
                {"role": "system", "content": "You are a news selection assistant. Return ONLY a JSON array of news IDs. No explanations, no thinking process, no analysis. Example: [\"INT-1\", \"INT-5\", \"DOM-2\"]"},
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
                # Fallback: select first 37 items
                selected_ids = list(news_items.keys())[:25]
            else:
                try:
                    selected_ids = json.loads(json_match.group(0))
                    # Validate IDs
                    selected_ids = [id for id in selected_ids if id in news_items]

                    # Ensure we have 30-40 items (target is 37)
                    if len(selected_ids) < 20:
                        logger.warning(f"Only {len(selected_ids)} items selected, adding more")
                        remaining = [id for id in news_items.keys() if id not in selected_ids]
                        selected_ids.extend(remaining[:25 - len(selected_ids)])
                    elif len(selected_ids) > 30:
                        logger.warning(f"{len(selected_ids)} items selected, trimming to 40")
                        selected_ids = selected_ids[:30]

                except json.JSONDecodeError:
                    logger.warning("JSON parse error, using fallback selection")
                    selected_ids = list(news_items.keys())[:25]

            logger.info(f"Stage 1 completed: Selected {len(selected_ids)} news items")
            logger.debug(f"Selected IDs: {selected_ids}")

            # ============================================================
            # STAGE 2: Summarization - Create detailed summaries
            # ============================================================
            logger.info(f"Stage 2: Creating detailed summaries for selected items...")

            # Format selected news for summarization
            formatted_selected = "# Selected High-Quality Study Abroad News Items\n\n"
            for news_id in selected_ids:
                item = news_items[news_id]
                formatted_selected += f"### [{news_id}] {item['title']}\n"
                formatted_selected += f"**Source:** {item['source']}\n"
                if item['description']:
                    formatted_selected += f"**Content:** {item['description']}\n"
                formatted_selected += f"**Link:** {item['link']}\n"
                if item['published']:
                    formatted_selected += f"**Published:** {item['published']}\n"
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
                summarization_prompt += f"\n\nIMPORTANT: Please respond entirely in {language_name}."

            # Execute Stage 2: Generate detailed summaries
            # System message to suppress thinking/reasoning output
            system_message = {
                "role": "system",
                "content": "你是一名专业中文新闻编辑。直接输出最终格式化的新闻日报，禁止输出任何思考过程、推理步骤、分类逻辑或规划内容。回复必须以'## 国际新闻'开头，只包含6个分类的新闻摘要。"
            }
            messages = [system_message, {"role": "user", "content": summarization_prompt}]
            response_text = self._generate_with_retry(
                messages=messages,
                max_tokens=max_tokens
            )

            # Post-process: strip thinking/reasoning that reasoning models leak into content
            # 1. Find the first standalone "## 国际新闻" header and cut everything before it
            #    Reasoning models may mention "## 国际新闻" in comma-separated lists during thinking,
            #    so we match only the standalone header (end of line, not followed by comma)
            header_pattern = r'^[\s\S]*?(?=\*{0,2}## 国际新闻\*{0,2}\s*$)'
            match = re.search(header_pattern, response_text, re.MULTILINE)
            if match and match.group(0).strip():
                prefix = match.group(0).strip()
                if prefix and not prefix.startswith('## 国际新闻'):
                    logger.warning(f"Stripping {len(prefix)} chars of thinking/reasoning from Stage 2 response")
                    response_text = response_text[match.end():]

            # 2. Remove "*Char count*" lines that reasoning models insert
            response_text = re.sub(r'\n\s*\*Char count[^\n]*', '', response_text)
            # 3. Remove "*Char count check*" lines
            response_text = re.sub(r'\n\s*\*Char count check\*[^\n]*', '', response_text)
            # 4. Clean up bold-wrapped headers: "**## 国际新闻**" → "## 国际新闻"
            response_text = re.sub(r'\*\*(## [^*]+)\*\*', r'\1', response_text)
            # 5. Remove leading whitespace on each line (4-space indent from thinking)
            lines = response_text.split('\n')
            cleaned_lines = []
            for line in lines:
                # Strip leading 4+ spaces that come from indented thinking output
                if line.startswith('    '):
                    line = line.lstrip()
                cleaned_lines.append(line)
            response_text = '\n'.join(cleaned_lines)
            # 6. Remove multiple consecutive blank lines
            response_text = re.sub(r'\n{3,}', '\n\n', response_text)

            # Footer is now handled by the email HTML template, no need to add it here

            logger.info("Stage 2 completed: News digest generated successfully")
            logger.info(f"Two-stage prompt chaining completed: {total_items} items → {len(selected_ids)} selected → full digest")
            logger.debug(f"Response length: {len(response_text)} characters")

            return response_text

        except Exception as e:
            logger.error(f"Failed to generate news digest from sources: {str(e)}", exc_info=True)
            raise
