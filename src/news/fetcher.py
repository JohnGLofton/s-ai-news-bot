"""
News fetcher module - Fetches real-time AI news from various sources
"""
import requests
from typing import List, Dict, Optional
from datetime import datetime
import xml.etree.ElementTree as ET
from ..logger import setup_logger


logger = setup_logger(__name__)


class NewsFetcher:
    """Fetch real-time AI news from RSS feeds and news APIs"""

    def __init__(self):
        """Initialize the news fetcher"""
        # RSS feed sources for international study abroad news
        self.rss_feeds = {
            # University Admissions & International Students
            "Times Higher Education": "https://www.timeshighereducation.com/news/rss.xml",
            "Inside Higher Ed": "https://www.insidehighered.com/rss.xml",
            "The PIE News": "https://thepienews.com/feed/",
            "ICEF Monitor": "https://monitor.icef.com/feed/",
            "Study International": "https://studyinternational.com/feed/",

            # US University & Policy News
            "Chronicle of Higher Education": "https://www.chronicle.com/feeds/default",
            "US News Education": "https://www.usnews.com/rss/education",
            "Diverse Education": "https://diverseeducation.com/feed/",

            # UK University News
            "The Guardian Education": "https://www.theguardian.com/education/rss",
            "BBC Education": "https://feeds.bbci.co.uk/news/education/rss.xml",

            # Language Tests News
            "Duolingo Blog": "https://blog.duolingo.com/rss/",
            "College Board (SAT/ACT)": "https://newsroom.collegeboard.org/rss.xml",

            # Global University Rankings
            "QS World Rankings News": "https://www.qs.com/feed/",

            # Immigration & Visa Policy (Google News)
            "US Student Visa News": "https://news.google.com/rss/search?q=US+student+visa+international+students&hl=en&gl=US&ceid=US:en",
            "UK Student Visa News": "https://news.google.com/rss/search?q=UK+student+visa+international+students&hl=en&gl=GB&ceid=GB:en",
            "Google News Study Abroad": "https://news.google.com/rss/search?q=international+students+university+admission&hl=en&gl=US&ceid=US:en",
            "Google News Language Tests": "https://news.google.com/rss/search?q=IELTS+TOEFL+SAT+ACT+Duolingo+test&hl=en&gl=US&ceid=US:en",
            "Google News University Rankings": "https://news.google.com/rss/search?q=world+university+rankings+2025&hl=en&gl=US&ceid=US:en",
        }

        # Chinese study abroad news sources (zh)
        self.chinese_feeds = {
            "Google News 留学申请": "https://news.google.com/rss/search?q=留学+申请+美国+英国+大学&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
            "Google News 语言考试": "https://news.google.com/rss/search?q=雅思+托福+SAT+留学考试&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
            "Google News 大学排名": "https://news.google.com/rss/search?q=世界大学排名+QS+泰晤士&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
            "Google News 留学政策": "https://news.google.com/rss/search?q=留学政策+签证+国际生&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
            "Google News 美英大学": "https://news.google.com/rss/search?q=美国大学+英国大学+国际学生+录取&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        }

        # Japanese AI news sources (ja)
        self.japanese_feeds = {
            # Tech News Outlets
            "ITmedia AI+": "https://rss.itmedia.co.jp/rss/2.0/aiplus.xml",
            "Nikkei xTECH": "https://xtech.nikkei.com/rss/index.rdf",
            "ASCII.jp AI": "https://ascii.jp/elem/000/004/000/4000000/index-2.xml",
            "Impress Watch": "https://www.watch.impress.co.jp/data/rss/1.0/ipw/feed.rdf",
            # Google News (fallback)
            "Google News AI (JP)": "https://news.google.com/rss/search?q=人工知能+AI&hl=ja&gl=JP&ceid=JP:ja",
            "Google News Tech (JP)": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtcG9HZ0pEVGlnQVAB?hl=ja&gl=JP&ceid=JP:ja",
        }

        # French AI news sources (fr)
        self.french_feeds = {
            # Tech News Outlets
            "L'Usine Digitale": "https://www.usine-digitale.fr/rss/intelligence-artificielle.xml",
            "01net": "https://www.01net.com/rss/actualites/",
            "Frandroid": "https://www.frandroid.com/feed",
            "BFM Tech": "https://www.bfmtv.com/rss/tech/",
            # Google News (fallback)
            "Google News AI (FR)": "https://news.google.com/rss/search?q=intelligence+artificielle&hl=fr&gl=FR&ceid=FR:fr",
            "Google News Tech (FR)": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtcG9HZ0pEVGlnQVAB?hl=fr&gl=FR&ceid=FR:fr",
        }

        # Spanish AI news sources (es)
        self.spanish_feeds = {
            # Tech News Outlets
            "Xataka": "https://www.xataka.com/tag/inteligencia-artificial/rss2.xml",
            "El País Tecnología": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/tecnologia/portada",
            "Hipertextual": "https://hipertextual.com/feed",
            "Genbeta": "https://www.genbeta.com/tag/inteligencia-artificial/rss2.xml",
            # Google News
            "Google News AI (ES)": "https://news.google.com/rss/search?q=inteligencia+artificial&hl=es&gl=ES&ceid=ES:es",
        }

        # German AI news sources (de)
        self.german_feeds = {
            # Tech News Outlets
            "Heise Online": "https://www.heise.de/rss/heise-atom.xml",
            "t3n Digital Pioneers": "https://t3n.de/tag/kuenstliche-intelligenz/feed/",
            "Golem.de": "https://rss.golem.de/rss.php?feed=RSS2.0",
            "Computerwoche": "https://www.computerwoche.de/rss/feed/computerwoche-alle",
            # Google News
            "Google News AI (DE)": "https://news.google.com/rss/search?q=künstliche+intelligenz&hl=de&gl=DE&ceid=DE:de",
        }

        # Korean AI news sources (ko)
        self.korean_feeds = {
            # Tech News Outlets
            "Chosun Biz Tech": "https://biz.chosun.com/rss/tech.xml",
            "ZDNet Korea": "https://zdnet.co.kr/rss/",
            "ETNews": "https://rss.etnews.com/Section901.xml",
            "Korean AI News": "https://www.aitimes.kr/rss/allArticle.xml",
            # Google News
            "Google News AI (KR)": "https://news.google.com/rss/search?q=인공지능&hl=ko&gl=KR&ceid=KR:ko",
        }

        # Portuguese AI news sources (pt)
        self.portuguese_feeds = {
            # Tech News Outlets
            "TecMundo": "https://www.tecmundo.com.br/rss",
            "Olhar Digital": "https://olhardigital.com.br/feed/",
            "Canaltech": "https://canaltech.com.br/rss/",
            "Exame": "https://exame.com/feed/tecnologia/",
            # Google News
            "Google News AI (BR)": "https://news.google.com/rss/search?q=inteligência+artificial&hl=pt-BR&gl=BR&ceid=BR:pt-419",
        }

        # Italian AI news sources (it)
        self.italian_feeds = {
            # Tech News Outlets
            "Il Sole 24 Ore Tech": "https://www.ilsole24ore.com/rss/tecnologia.xml",
            "Punto Informatico": "https://www.punto-informatico.it/feed/",
            "Tom's Hardware IT": "https://www.tomshw.it/feed",
            "Wired Italia": "https://www.wired.it/feed/rss",
            # Google News
            "Google News AI (IT)": "https://news.google.com/rss/search?q=intelligenza+artificiale&hl=it&gl=IT&ceid=IT:it",
        }

        # Russian AI news sources (ru)
        self.russian_feeds = {
            # Tech News Outlets
            "Habr": "https://habr.com/ru/rss/all/",
            "CNews": "https://www.cnews.ru/inc/rss/news.xml",
            "Roem.ru": "https://roem.ru/feed/",
            "VC.ru": "https://vc.ru/rss/all",
            # Google News
            "Google News AI (RU)": "https://news.google.com/rss/search?q=искусственный+интеллект&hl=ru&gl=RU&ceid=RU:ru",
        }

        # Dutch AI news sources (nl)
        self.dutch_feeds = {
            # Tech News Outlets
            "Tweakers": "https://feeds.feedburner.com/tweakers/mixed",
            "Computable": "https://www.computable.nl/rss.xml",
            "Dutch IT Channel": "https://dutchitchannel.nl/feed/",
            # Google News
            "Google News AI (NL)": "https://news.google.com/rss/search?q=kunstmatige+intelligentie&hl=nl&gl=NL&ceid=NL:nl",
        }

        # Arabic AI news sources (ar)
        self.arabic_feeds = {
            # Tech News Outlets
            "Arageek": "https://www.arageek.com/feed",
            "Tech Wd": "https://www.tech-wd.com/feed/",
            # Google News
            "Google News AI (AR)": "https://news.google.com/rss/search?q=الذكاء+الاصطناعي&hl=ar&gl=SA&ceid=SA:ar",
        }

        # Hindi AI news sources (hi)
        self.hindi_feeds = {
            # Tech News Outlets
            "Jagran Josh Tech": "https://www.jagranjosh.com/rss/tech.xml",
            "NDTV Gadgets": "https://feeds.feedburner.com/ndtvgadgets-latest",
            # Google News
            "Google News AI (HI)": "https://news.google.com/rss/search?q=कृत्रिम+बुद्धिमत्ता&hl=hi&gl=IN&ceid=IN:hi",
        }


    def fetch_rss_feed(self, feed_url: str, max_items: int = 10) -> List[Dict[str, str]]:
        """
        Fetch news items from an RSS feed.

        Args:
            feed_url: URL of the RSS feed
            max_items: Maximum number of items to fetch

        Returns:
            List of news items with title, link, description, and published date
        """
        try:
            logger.info(f"Fetching RSS feed: {feed_url}")

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(feed_url, headers=headers, timeout=10)
            response.raise_for_status()

            # Parse XML
            root = ET.fromstring(response.content)

            items = []
            # Handle both RSS 2.0 and Atom formats
            if root.tag == 'rss':
                news_items = root.findall('.//item')[:max_items]
                for item in news_items:
                    title = item.find('title')
                    link = item.find('link')
                    description = item.find('description')
                    pub_date = item.find('pubDate')

                    items.append({
                        'title': title.text if title is not None else '',
                        'link': link.text if link is not None else '',
                        'description': self._clean_html(description.text if description is not None else ''),
                        'published': pub_date.text if pub_date is not None else '',
                    })
            else:
                # Atom format
                namespace = {'atom': 'http://www.w3.org/2005/Atom'}
                entries = root.findall('.//atom:entry', namespace)[:max_items]
                for entry in entries:
                    title = entry.find('atom:title', namespace)
                    link = entry.find('atom:link', namespace)
                    summary = entry.find('atom:summary', namespace)
                    updated = entry.find('atom:updated', namespace)

                    items.append({
                        'title': title.text if title is not None else '',
                        'link': link.get('href', '') if link is not None else '',
                        'description': self._clean_html(summary.text if summary is not None else ''),
                        'published': updated.text if updated is not None else '',
                    })

            logger.info(f"Fetched {len(items)} items from RSS feed")
            return items

        except Exception as e:
            logger.error(f"Failed to fetch RSS feed {feed_url}: {str(e)}")
            return []

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text"""
        import re
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text).strip()

    def fetch_recent_news(
        self,
        language: str = "en",
        max_items_per_source: int = 5
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        Fetch recent AI news from all configured sources.

        Args:
            language: Language code for the response
            max_items_per_source: Maximum items to fetch per source

        Returns:
            Dictionary with 'international' and 'domestic' news lists
        """
        logger.info("Fetching recent AI news from all sources...")

        all_news = {
            'international': [],
            'domestic': []
        }

        # Fetch international news
        for source_name, feed_url in self.rss_feeds.items():
            items = self.fetch_rss_feed(feed_url, max_items_per_source)
            for item in items:
                item['source'] = source_name
                all_news['international'].append(item)

        # Fetch domestic news based on language
        language_feeds_map = {
            "zh": self.chinese_feeds,
            "ja": self.japanese_feeds,
            "fr": self.french_feeds,
            "es": self.spanish_feeds,
            "de": self.german_feeds,
            "ko": self.korean_feeds,
            "pt": self.portuguese_feeds,
            "it": self.italian_feeds,
            "ru": self.russian_feeds,
            "nl": self.dutch_feeds,
            "ar": self.arabic_feeds,
            "hi": self.hindi_feeds,
        }

        feeds = language_feeds_map.get(language)
        if not feeds:
            logger.warning(f"No domestic feeds configured for language: {language}, using international only")
            return all_news

        for source_name, feed_url in feeds.items():
            items = self.fetch_rss_feed(feed_url, max_items_per_source)
            for item in items:
                item['source'] = source_name
                all_news['domestic'].append(item)

        logger.info(
            f"Fetched {len(all_news['international'])} international news items "
            f"and {len(all_news['domestic'])} domestic ({language}) news items"
        )

        return all_news

    def format_news_for_summary(self, news_data: Dict[str, List[Dict[str, str]]]) -> str:
        """
        Format fetched news into a text suitable for AI summarization.

        Args:
            news_data: Dictionary with 'international' and 'domestic' news lists

        Returns:
            Formatted news text
        """
        formatted = "# Recent AI News Items to Summarize\n\n"

        if news_data['international']:
            formatted += "## International News\n\n"
            for i, item in enumerate(news_data['international'], 1):
                formatted += f"### {i}. {item['title']}\n"
                formatted += f"**Source:** {item['source']}\n"
                if item['description']:
                    formatted += f"**Description:** {item['description'][:300]}...\n"
                formatted += f"**Link:** {item['link']}\n"
                if item['published']:
                    formatted += f"**Published:** {item['published']}\n"
                formatted += "\n"

        if news_data['domestic']:
            formatted += "## Domestic News\n\n"
            for i, item in enumerate(news_data['domestic'], 1):
                formatted += f"### {i}. {item['title']}\n"
                formatted += f"**Source:** {item['source']}\n"
                if item['description']:
                    formatted += f"**Description:** {item['description'][:300]}...\n"
                formatted += f"**Link:** {item['link']}\n"
                if item['published']:
                    formatted += f"**Published:** {item['published']}\n"
                formatted += "\n"

        return formatted
