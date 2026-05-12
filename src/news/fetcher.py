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
            # ── International Education Media ──
            "Times Higher Education": "https://www.timeshighereducation.com/news/rss.xml",
            "Inside Higher Ed": "https://www.insidehighered.com/rss.xml",
            "The PIE News": "https://thepienews.com/feed/",
            "ICEF Monitor": "https://monitor.icef.com/feed/",
            "Study International": "https://studyinternational.com/feed/",
            "The Pie Chat": "https://thepienews.com/category/news/feed/",

            # ── US University & Higher Ed Policy ──
            "Chronicle of Higher Education": "https://www.chronicle.com/feeds/default",
            "US News Education": "https://www.usnews.com/rss/education",
            "Diverse Education": "https://diverseeducation.com/feed/",
            "EdSurge": "https://www.edsurge.com/news.rss",
            "Higher Ed Dive": "https://www.highereddive.com/feeds/news/",
            "Google News US University": "https://news.google.com/rss/search?q=US+university+international+students+admission&hl=en&gl=US&ceid=US:en&as_qdr=d2",
            "Google News Harvard MIT Stanford": "https://news.google.com/rss/search?q=Harvard+MIT+Stanford+Yale+Columbia+admission&hl=en&gl=US&ceid=US:en&as_qdr=d2",
            "Google News US Education Policy": "https://news.google.com/rss/search?q=US+higher+education+policy+international+students&hl=en&gl=US&ceid=US:en&as_qdr=d2",

            # ── UK University & Higher Ed ──
            "The Guardian Education": "https://www.theguardian.com/education/rss",
            "BBC Education": "https://feeds.bbci.co.uk/news/education/rss.xml",
            "Times Education Supplement": "https://www.tes.com/magazine/rss",
            "Wonkhe": "https://wonkhe.com/feed/",
            "Google News UK University": "https://news.google.com/rss/search?q=UK+university+international+students+UCAS&hl=en&gl=GB&ceid=GB:en&as_qdr=d2",
            "Google News Oxford Cambridge": "https://news.google.com/rss/search?q=Oxford+Cambridge+Imperial+UCL+LSE+admission&hl=en&gl=GB&ceid=GB:en&as_qdr=d2",
            "Google News UK Education Policy": "https://news.google.com/rss/search?q=UK+higher+education+international+students&hl=en&gl=GB&ceid=GB:en&as_qdr=d2",
            "Google News UK Student Visa": "https://news.google.com/rss/search?q=UK+student+visa+graduate+route+international&hl=en&gl=GB&ceid=GB:en&as_qdr=d2",
            "Google News UK University Fees": "https://news.google.com/rss/search?q=UK+university+tuition+fees+international+students&hl=en&gl=GB&ceid=GB:en&as_qdr=d2",

            # ── Language Tests ──
            "Duolingo Blog": "https://blog.duolingo.com/rss/",
            "College Board (SAT/ACT)": "https://newsroom.collegeboard.org/rss.xml",
            "Google News IELTS": "https://news.google.com/rss/search?q=IELTS+score+policy+university&hl=en&gl=US&ceid=US:en&as_qdr=d2",
            "Google News TOEFL": "https://news.google.com/rss/search?q=TOEFL+ETS+score+requirement&hl=en&gl=US&ceid=US:en&as_qdr=d2",
            "Google News SAT ACT": "https://news.google.com/rss/search?q=SAT+ACT+test+optional+college+admission&hl=en&gl=US&ceid=US:en&as_qdr=d2",
            "Google News Duolingo Test": "https://news.google.com/rss/search?q=Duolingo+English+Test+university+acceptance&hl=en&gl=US&ceid=US:en&as_qdr=d2",

            # ── University Rankings ──
            "QS World Rankings News": "https://www.qs.com/feed/",
            "Google News QS Rankings": "https://news.google.com/rss/search?q=QS+world+university+rankings&hl=en&gl=US&ceid=US:en&as_qdr=d2",
            "Google News THE Rankings": "https://news.google.com/rss/search?q=Times+Higher+Education+world+university+rankings&hl=en&gl=US&ceid=US:en&as_qdr=d2",
            "Google News University Scholarships": "https://news.google.com/rss/search?q=international+scholarship+university&hl=en&gl=US&ceid=US:en&as_qdr=d2",

            # ── Visa & Immigration Policy ──
            "US Student Visa News": "https://news.google.com/rss/search?q=F1+visa+OPT+STEM+international+students+US&hl=en&gl=US&ceid=US:en&as_qdr=d2",
            "US Immigration Student Policy": "https://news.google.com/rss/search?q=US+immigration+policy+international+students&hl=en&gl=US&ceid=US:en&as_qdr=d2",
            "UK Student Visa News": "https://news.google.com/rss/search?q=UK+student+visa+Tier4+Graduate+Route&hl=en&gl=GB&ceid=GB:en&as_qdr=d2",
            "UK Immigration Policy": "https://news.google.com/rss/search?q=UK+immigration+international+students+visa+policy&hl=en&gl=GB&ceid=GB:en&as_qdr=d2",
            "Australia Student Visa": "https://news.google.com/rss/search?q=Australia+student+visa+international+students&hl=en&gl=AU&ceid=AU:en&as_qdr=d2",
            "Canada Student Visa": "https://news.google.com/rss/search?q=Canada+study+permit+international+students&hl=en&gl=CA&ceid=CA:en&as_qdr=d2",

            # ── International General Headlines ──
            "AP News Top": "https://rsshub.app/apnews/topics/apf-topnews",
            "BBC World News": "https://feeds.bbci.co.uk/news/world/rss.xml",
            "Associated Press": "https://rsshub.app/apnews/topics/apf-topnews",
            "Financial Times Education": "https://news.google.com/rss/search?q=education+university+global&hl=en&gl=US&ceid=US:en&as_qdr=d2",
        }

        # Chinese study abroad news sources (zh)
        self.chinese_feeds = {
            # ── 国内头条（Google News 可在海外服务器访问）──
            "Google News 中国政治": "https://news.google.com/rss/search?q=中国+政府+政策+外交&hl=zh-CN&gl=CN&ceid=CN:zh-Hans&as_qdr=d2",
            "Google News 中国经济": "https://news.google.com/rss/search?q=中国+经济+GDP+贸易+金融&hl=zh-CN&gl=CN&ceid=CN:zh-Hans&as_qdr=d2",
            "Google News 中国科技": "https://news.google.com/rss/search?q=中国+科技+人工智能+芯片+互联网&hl=zh-CN&gl=CN&ceid=CN:zh-Hans&as_qdr=d2",
            "Google News 中国社会": "https://news.google.com/rss/search?q=中国+社会+民生+热点&hl=zh-CN&gl=CN&ceid=CN:zh-Hans&as_qdr=d2",
            "Google News 中美关系": "https://news.google.com/rss/search?q=中美+关系+贸易战+外交&hl=zh-CN&gl=CN&ceid=CN:zh-Hans&as_qdr=d2",
            # ── 留学相关 ──
            "Google News 留学申请": "https://news.google.com/rss/search?q=留学+申请+美国+英国+大学&hl=zh-CN&gl=CN&ceid=CN:zh-Hans&as_qdr=d2",
            "Google News 语言考试": "https://news.google.com/rss/search?q=雅思+托福+SAT+ACT+多邻国+留学考试&hl=zh-CN&gl=CN&ceid=CN:zh-Hans&as_qdr=d2",
            "Google News 大学排名": "https://news.google.com/rss/search?q=世界大学排名+QS+泰晤士+软科&hl=zh-CN&gl=CN&ceid=CN:zh-Hans&as_qdr=d2",
            "Google News 留学政策": "https://news.google.com/rss/search?q=留学政策+学生签证+国际生+OPT&hl=zh-CN&gl=CN&ceid=CN:zh-Hans&as_qdr=d2",
            "Google News 美英名校": "https://news.google.com/rss/search?q=哈佛+麻省理工+剑桥+牛津+名校+录取&hl=zh-CN&gl=CN&ceid=CN:zh-Hans&as_qdr=d2",
        }

        # Japanese study abroad news sources (ja)
        self.japanese_feeds = {
            "Google News 留学+米国+英国+大学 (JP)": "https://news.google.com/rss/search?q=留学+アメリカ+イギリス+大学+入試&hl=ja&gl=JP&ceid=JP:ja&as_qdr=d2",
            "Google News 留学ビザ+学生 (JP)": "https://news.google.com/rss/search?q=留学+ビザ+学生+就労&hl=ja&gl=JP&ceid=JP:ja&as_qdr=d2",
            "Google News IELTS+TOEFL+留学 (JP)": "https://news.google.com/rss/search?q=IELTS+TOEFL+留学+英語試験&hl=ja&gl=JP&ceid=JP:ja&as_qdr=d2",
            "Google News 世界大学ランキング (JP)": "https://news.google.com/rss/search?q=世界大学ランキング+QS+THE&hl=ja&gl=JP&ceid=JP:ja&as_qdr=d2",
            "Google News 国際ニュース (JP)": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtcG9HZ0pEVGlnQVAB?hl=ja&gl=JP&ceid=JP:ja",
        }

        # French study abroad news sources (fr)
        self.french_feeds = {
            "Google News études à l'étranger (FR)": "https://news.google.com/rss/search?q=études+à+l'étranger+université+étudiants+internationaux&hl=fr&gl=FR&ceid=FR:fr&as_qdr=d2",
            "Google News visa étudiant (FR)": "https://news.google.com/rss/search?q=visa+étudiant+France+immigration&hl=fr&gl=FR&ceid=FR:fr&as_qdr=d2",
            "Google News IELTS+TOEFL+université (FR)": "https://news.google.com/rss/search?q=IELTS+TOEFL+université+admission&hl=fr&gl=FR&ceid=FR:fr&as_qdr=d2",
            "Google News classement universités (FR)": "https://news.google.com/rss/search?q=classement+universités+mondial+QS+THE&hl=fr&gl=FR&ceid=FR:fr&as_qdr=d2",
            "Google News international (FR)": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtcG9HZ0pEVGlnQVAB?hl=fr&gl=FR&ceid=FR:fr",
        }

        # Spanish study abroad news sources (es)
        self.spanish_feeds = {
            "Google News estudiar extranjero (ES)": "https://news.google.com/rss/search?q=estudiar+en+el+extranjero+universidad+estudiantes+internacionales&hl=es&gl=ES&ceid=ES:es&as_qdr=d2",
            "Google News visa de estudiante (ES)": "https://news.google.com/rss/search?q=visa+de+estudiante+inmigración&hl=es&gl=ES&ceid=ES:es&as_qdr=d2",
            "Google News IELTS+TOEFL+universidad (ES)": "https://news.google.com/rss/search?q=IELTS+TOEFL+universidad+admisión&hl=es&gl=ES&ceid=ES:es&as_qdr=d2",
            "Google News ranking universidades (ES)": "https://news.google.com/rss/search?q=ranking+universidades+mundial+QS&hl=es&gl=ES&ceid=ES:es&as_qdr=d2",
            "Google News internacional (ES)": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtcG9HZ0pEVGlnQVAB?hl=es&gl=ES&ceid=ES:es",
        }

        # German study abroad news sources (de)
        self.german_feeds = {
            "Google News Auslandsstudium (DE)": "https://news.google.com/rss/search?q=Auslandsstudium+Universität+internationale+Studenten&hl=de&gl=DE&ceid=DE:de&as_qdr=d2",
            "Google News Studentenvisum (DE)": "https://news.google.com/rss/search?q=Studentenvisum+Deutschland+Einwanderung&hl=de&gl=DE&ceid=DE:de&as_qdr=d2",
            "Google News IELTS+TOEFL+Universität (DE)": "https://news.google.com/rss/search?q=IELTS+TOEFL+Universität+Zulassung&hl=de&gl=DE&ceid=DE:de&as_qdr=d2",
            "Google News Weltrangliste Universitäten (DE)": "https://news.google.com/rss/search?q=Weltrangliste+Universitäten+QS+THE&hl=de&gl=DE&ceid=DE:de&as_qdr=d2",
            "Google News international (DE)": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtcG9HZ0pEVGlnQVAB?hl=de&gl=DE&ceid=DE:de",
        }

        # Korean study abroad news sources (ko)
        self.korean_feeds = {
            "Google News 유학+미국+영국 (KR)": "https://news.google.com/rss/search?q=유학+미국+영국+대학+입시&hl=ko&gl=KR&ceid=KR:ko&as_qdr=d2",
            "Google News 유학비자+학생 (KR)": "https://news.google.com/rss/search?q=유학비자+학생+취업&hl=ko&gl=KR&ceid=KR:ko&as_qdr=d2",
            "Google News IELTS+TOEFL+유학 (KR)": "https://news.google.com/rss/search?q=IELTS+TOEFL+유학+어학시험&hl=ko&gl=KR&ceid=KR:ko&as_qdr=d2",
            "Google News 세계대학순위 (KR)": "https://news.google.com/rss/search?q=세계대학순위+QS+THE&hl=ko&gl=KR&ceid=KR:ko&as_qdr=d2",
            "Google News 국제뉴스 (KR)": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtcG9HZ0pEVGlnQVAB?hl=ko&gl=KR&ceid=KR:ko",
        }

        # Portuguese study abroad news sources (pt)
        self.portuguese_feeds = {
            "Google News estudar exterior (BR)": "https://news.google.com/rss/search?q=estudar+no+exterior+universidade+estudantes+internacionais&hl=pt-BR&gl=BR&ceid=BR:pt-419&as_qdr=d2",
            "Google News visto de estudante (BR)": "https://news.google.com/rss/search?q=visto+de+estudante+imigração&hl=pt-BR&gl=BR&ceid=BR:pt-419&as_qdr=d2",
            "Google News IELTS+TOEFL+universidade (BR)": "https://news.google.com/rss/search?q=IELTS+TOEFL+universidade+admissão&hl=pt-BR&gl=BR&ceid=BR:pt-419&as_qdr=d2",
            "Google News ranking universidades (BR)": "https://news.google.com/rss/search?q=ranking+universidades+mundial&hl=pt-BR&gl=BR&ceid=BR:pt-419&as_qdr=d2",
            "Google News internacional (BR)": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtcG9HZ0pEVGlnQVAB?hl=pt-BR&gl=BR&ceid=BR:pt-419",
        }

        # Italian study abroad news sources (it)
        self.italian_feeds = {
            "Google News studio all'estero (IT)": "https://news.google.com/rss/search?q=studio+all'estero+università+studenti+internazionali&hl=it&gl=IT&ceid=IT:it&as_qdr=d2",
            "Google News visto studentesco (IT)": "https://news.google.com/rss/search?q=visto+studentesco+Italia+immigrazione&hl=it&gl=IT&ceid=IT:it&as_qdr=d2",
            "Google News IELTS+TOEFL+università (IT)": "https://news.google.com/rss/search?q=IELTS+TOEFL+università+ammissione&hl=it&gl=IT&ceid=IT:it&as_qdr=d2",
            "Google News classifica università (IT)": "https://news.google.com/rss/search?q=classifica+università+mondiale+QS&hl=it&gl=IT&ceid=IT:it&as_qdr=d2",
            "Google News internazionale (IT)": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtcG9HZ0pEVGlnQVAB?hl=it&gl=IT&ceid=IT:it",
        }

        # Russian study abroad news sources (ru)
        self.russian_feeds = {
            "Google News обучение за рубежом (RU)": "https://news.google.com/rss/search?q=обучение+за+рубежом+университет+иностранные+студенты&hl=ru&gl=RU&ceid=RU:ru&as_qdr=d2",
            "Google News студенческая виза (RU)": "https://news.google.com/rss/search?q=студенческая+виза+иммиграция&hl=ru&gl=RU&ceid=RU:ru&as_qdr=d2",
            "Google News IELTS+TOEFL+университет (RU)": "https://news.google.com/rss/search?q=IELTS+TOEFL+университет+поступление&hl=ru&gl=RU&ceid=RU:ru&as_qdr=d2",
            "Google News рейтинг университетов (RU)": "https://news.google.com/rss/search?q=рейтинг+университетов+мировой+QS&hl=ru&gl=RU&ceid=RU:ru&as_qdr=d2",
            "Google News международные новости (RU)": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtcG9HZ0pEVGlnQVAB?hl=ru&gl=RU&ceid=RU:ru",
        }

        # Dutch study abroad news sources (nl)
        self.dutch_feeds = {
            "Google News studeren buitenland (NL)": "https://news.google.com/rss/search?q=studeren+in+het+buitenland+universiteit+internationale+studenten&hl=nl&gl=NL&ceid=NL:nl&as_qdr=d2",
            "Google News studentenvisum (NL)": "https://news.google.com/rss/search?q=studentenvisum+Nederland+immigratie&hl=nl&gl=NL&ceid=NL:nl&as_qdr=d2",
            "Google News IELTS+TOEFL+universiteit (NL)": "https://news.google.com/rss/search?q=IELTS+TOEFL+universiteit+toelating&hl=nl&gl=NL&ceid=NL:nl&as_qdr=d2",
            "Google News wereldranglijst universiteiten (NL)": "https://news.google.com/rss/search?q=wereldranglijst+universiteiten+QS&hl=nl&gl=NL&ceid=NL:nl&as_qdr=d2",
            "Google News internationaal (NL)": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtcG9HZ0pEVGlnQVAB?hl=nl&gl=NL&ceid=NL:nl",
        }

        # Arabic study abroad news sources (ar)
        self.arabic_feeds = {
            "Google News الدراسة في الخارج (AR)": "https://news.google.com/rss/search?q=الدراسة+في+الخارج+جامعة+طلاب+دوليين&hl=ar&gl=SA&ceid=SA:ar&as_qdr=d2",
            "Google News تأشيرة طالب (AR)": "https://news.google.com/rss/search?q=تأشيرة+طالب+هجرة&hl=ar&gl=SA&ceid=SA:ar&as_qdr=d2",
            "Google News IELTS+TOEFL+جامعة (AR)": "https://news.google.com/rss/search?q=IELTS+TOEFL+جامعة+قبول&hl=ar&gl=SA&ceid=SA:ar&as_qdr=d2",
            "Google News تصنيف الجامعات (AR)": "https://news.google.com/rss/search?q=تصنيف+الجامعات+العالمي+QS&hl=ar&gl=SA&ceid=SA:ar&as_qdr=d2",
            "Google News أخبار دولية (AR)": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtcG9HZ0pEVGlnQVAB?hl=ar&gl=SA&ceid=SA:ar",
        }

        # Hindi study abroad news sources (hi)
        self.hindi_feeds = {
            "Google News विदेश अध्ययन (HI)": "https://news.google.com/rss/search?q=विदेश+अध्ययन+विश्वविद्यालय+अंतरराष्ट्रीय+छात्र&hl=hi&gl=IN&ceid=IN:hi&as_qdr=d2",
            "Google News छात्र वीजा (HI)": "https://news.google.com/rss/search?q=छात्र+वीजा+आव्रजन&hl=hi&gl=IN&ceid=IN:hi&as_qdr=d2",
            "Google News IELTS+TOEFL+विश्वविद्यालय (HI)": "https://news.google.com/rss/search?q=IELTS+TOEFL+विश्वविद्यालय+प्रवेश&hl=hi&gl=IN&ceid=IN:hi&as_qdr=d2",
            "Google News विश्वविद्यालय रैंकिंग (HI)": "https://news.google.com/rss/search?q=विश्वविद्यालय+रैंकिंग+QS+THE&hl=hi&gl=IN&ceid=IN:hi&as_qdr=d2",
            "Google News अंतर्राष्ट्रीय (HI)": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtcG9HZ0pEVGlnQVAB?hl=hi&gl=IN&ceid=IN:hi",
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
        formatted = "# Recent Study Abroad News Items to Summarize\n\n"

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
