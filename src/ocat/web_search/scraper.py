"""
Content scraper for extracting text from web pages.
"""

import asyncio
import aiohttp
from typing import Optional, List, Union, cast
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, Tag
import logging

from ..utils.logging import setup_logger, LogLevel


class PageContent:
    """Represents content extracted from a web page."""
    
    def __init__(self, url: str, title: str, text: str, success: bool = True, error: Optional[str] = None):
        self.url = url
        self.title = title
        self.text = text
        self.success = success
        self.error = error
        
    def __repr__(self):
        return f"PageContent(url='{self.url}', title='{self.title}', success={self.success})"


class ContentScraper:
    """Scrapes and extracts text content from web pages."""
    
    def __init__(self, config):
        """
        Initialize content scraper.
        
        Parameters
        ----------
        config : Config
            Configuration object containing web_search settings
        """
        self.config = config
        self.web_config = config.web_search
        self.timeout = self.web_config.timeout
        self.logger = setup_logger(
            "ocat.web_search.scraper", LogLevel[config.logging.level], config
        )
        
    async def scrape_url(self, url: str) -> PageContent:
        """
        Scrape content from a single URL.
        
        Parameters
        ----------
        url : str
            URL to scrape
            
        Returns
        -------
        PageContent
            Extracted content or error information
        """
        try:
            # Check if URL is likely to be HTML content
            if not self._is_html_url(url):
                return PageContent(url, "", "", success=False, error="Non-HTML content type")
                
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        return PageContent(url, "", "", success=False, error=f"HTTP {response.status}")
                    
                    # Check content type
                    content_type = response.headers.get('content-type', '').lower()
                    if 'text/html' not in content_type:
                        return PageContent(url, "", "", success=False, error=f"Content type: {content_type}")
                    
                    html = await response.text()
                    return self._extract_content(url, html)
                    
        except asyncio.TimeoutError:
            self.logger.warning(f"Timeout scraping {url}")
            return PageContent(url, "", "", success=False, error="Timeout")
        except Exception as e:
            self.logger.warning(f"Error scraping {url}: {e}")
            return PageContent(url, "", "", success=False, error=str(e))
            
    async def scrape_urls(self, urls: List[str]) -> List[PageContent]:
        """
        Scrape content from multiple URLs concurrently.
        
        Parameters
        ----------
        urls : List[str]
            URLs to scrape
            
        Returns
        -------
        List[PageContent]
            List of extracted content
        """
        if not urls:
            return []
            
        self.logger.info(f"Scraping {len(urls)} URLs")
        
        # Scrape all URLs concurrently
        tasks = [self.scrape_url(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        page_contents = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.warning(f"Exception scraping {urls[i]}: {result}")
                page_contents.append(PageContent(urls[i], "", "", success=False, error=str(result)))
            elif isinstance(result, PageContent):
                page_contents.append(result)
                
        successful = sum(1 for pc in page_contents if pc.success)
        self.logger.info(f"Successfully scraped {successful}/{len(urls)} URLs")
        
        return page_contents
        
    def _extract_content(self, url: str, html: str) -> PageContent:
        """
        Extract text content from HTML.
        
        Parameters
        ----------
        url : str
            Source URL
        html : str
            HTML content
            
        Returns
        -------
        PageContent
            Extracted content
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract title
            title_elem = soup.find('title')
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "aside", "header"]):
                script.decompose()
                
            # Extract main content areas first (better content quality)
            main_content: Union[Tag, BeautifulSoup, None] = None
            for selector in ['main', 'article', '[role="main"]', '.content', '.main-content']:
                element = soup.select_one(selector)
                if element and hasattr(element, 'get_text'):  # Ensure it's a Tag, not NavigableString
                    main_content = element
                    break
                    
            # If no main content found, use body
            if not main_content:
                body_element = soup.find('body')
                if body_element and hasattr(body_element, 'get_text'):
                    main_content = cast(Tag, body_element)
                
            if not main_content:
                # Fallback to the entire soup as a last resort
                main_content = cast(Union[Tag, BeautifulSoup], soup)
                
            # Extract text
            text = main_content.get_text(separator=' ', strip=True)
            
            # Clean up text - remove excessive whitespace
            text = ' '.join(text.split())
            
            return PageContent(url, title, text, success=True)
            
        except Exception as e:
            self.logger.warning(f"Error extracting content from {url}: {e}")
            return PageContent(url, "", "", success=False, error=f"Content extraction failed: {e}")
            
    def _is_html_url(self, url: str) -> bool:
        """
        Check if URL is likely to contain HTML content.
        
        Parameters
        ----------
        url : str
            URL to check
            
        Returns
        -------
        bool
            True if likely HTML content
        """
        # Parse URL
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        # Skip obvious non-HTML files
        skip_extensions = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', 
                          '.zip', '.rar', '.tar', '.gz', '.mp3', '.mp4', '.avi', 
                          '.mov', '.wav', '.jpg', '.jpeg', '.png', '.gif', '.svg',
                          '.css', '.js', '.xml', '.json', '.csv'}
        
        for ext in skip_extensions:
            if path.endswith(ext):
                return False
                
        return True
