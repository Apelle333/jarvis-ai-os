"""
JARVIS AI Operating System - Browser Tool
Handles web scraping, HTTP requests, and basic browser automation
"""

import asyncio
import logging
import aiohttp
import json
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse
import re
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class BrowserTool:
    """
    Browser Tool - Handles web requests, scraping, and basic automation
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_initialized = False
        self.session: Optional[aiohttp.ClientSession] = None
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.max_redirects = 5
        self.verify_ssl = True

        # Rate limiting
        self.request_delay = 0.1  # Seconds between requests
        self.last_request_time = 0

        # Blocked domains for security
        self.blocked_domains = {
            'localhost', '127.0.0.1', '0.0.0.0',
            '::1', '[::1]'
        }

        # Allowed content types
        self.allowed_content_types = {
            'text/html',
            'text/plain',
            'text/css',
            'text/javascript',
            'application/json',
            'application/xml',
            'image/jpeg',
            'image/png',
            'image/gif',
            'image/svg+xml'
        }

    async def initialize(self):
        """Initialize the browser tool"""
        try:
            self.logger.info("Initializing Browser Tool...")
            # Create a session
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=30,
                ttl_dns_cache=300,
                use_dns_cache=True,
            )
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=self.timeout,
                headers={'User-Agent': self.user_agent}
            )
            self.is_initialized = True
            self.logger.info("Browser Tool initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Browser Tool: {e}")
            raise

    async def _rate_limit(self):
        """Implement rate limiting"""
        now = asyncio.get_running_loop().time()
        time_since_last = now - self.last_request_time
        if time_since_last < self.request_delay:
            await asyncio.sleep(self.request_delay - time_since_last)
        self.last_request_time = asyncio.get_running_loop().time()

    def _is_url_allowed(self, url: str) -> bool:
        """Check if a URL is allowed to be accessed"""
        try:
            parsed = urlparse(url)
            hostname = hostname.lower() if (hostname := parsed.hostname) else ""

            # Check for blocked domains
            if hostname in self.blocked_domains:
                return False

            # Block internal/reserved IPs
            if re.match(r'^127\.', hostname) or \
               re.match(r'^192\.168\.', hostname) or \
               re.match(r'^10\.', hostname) or \
               re.match(r'^172\.(1[6-9]|2[0-9]|3[0-1])\.', hostname) or \
               re.match(r'^169\.254\.', hostname):
                return False

            return True
        except Exception:
            return False

    async def _fetch(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Any] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Internal method to fetch a URL"""
        if not self.is_initialized:
            await self.initialize()

        if not self._is_url_allowed(url):
            return {
                "success": False,
                "error": f"Access to URL '{url}' is not allowed for security reasons",
                "url": url
            }

        await self._rate_limit()

        try:
            # Prepare headers
            request_headers = {'User-Agent': self.user_agent}
            if headers:
                request_headers.update(headers)

            # Prepare data
            if json_data is not None:
                data = json.dumps(json_data)
                request_headers['Content-Type'] = 'application/json'

            # Make request
            async with self.session.request(
                method,
                url,
                headers=request_headers,
                data=data,
                allow_redirects=True,
                max_redirects=self.max_redirects,
                ssl=self.verify_ssl,
                timeout=self.timeout
            ) as response:
                # Read response
                content = await response.read()
                content_type = response.headers.get('Content-Type', '').split(';')[0].strip()

                # Check if content type is allowed
                if content_type and content_type not in self.allowed_content_types:
                    # Allow unknown types for flexibility, but warn
                    self.logger.warning(f"Unexpected content type: {content_type}")

                return {
                    "success": True,
                    "url": str(response.url),  # Final URL after redirects
                    "status": response.status,
                    "headers": dict(response.headers),
                    "content": content,
                    "content_type": content_type,
                    "text": content.decode('utf-8', errors='replace') if content else "",
                    "history": [str(resp.url) for resp in response.history] if response.history else []
                }

        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"Request timed out after {self.timeout.total} seconds",
                "url": url
            }
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return {
                "success": False,
                "error": f"Failed to fetch URL: {str(e)}",
                "url": url
            }

    async def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform a GET request"""
        if params:
            from urllib.parse import urlencode
            separator = '&' if '?' in url else '?'
            url = f"{url}{separator}{urlencode(params)}"
        return await self._fetch(url, "GET", headers)

    async def post(
        self,
        url: str,
        data: Optional[Any] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Perform a POST request"""
        return await self._fetch(url, "POST", headers, data, json_data)

    async def put(
        self,
        url: str,
        data: Optional[Any] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Perform a PUT request"""
        return await self._fetch(url, "PUT", headers, data, json_data)

    async def delete(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Perform a DELETE request"""
        return await self._fetch(url, "DELETE", headers)

    async def scrape(
        self,
        url: str,
        selector: Optional[str] = None,
        attributes: Optional[List[str]] = None,
        text_only: bool = False
    ) -> Dict[str, Any]:
        """
        Scrape a webpage for specific content

        Args:
            url: URL to scrape
            selector: CSS selector to extract elements
            attributes: List of attributes to extract (if None, gets text)
            text_only: Whether to extract only text content

        Returns:
            Dictionary with scraped data
        """
        try:
            # Fetch the page
            result = await self.get(url)
            if not result["success"]:
                return result

            # Parse HTML
            soup = BeautifulSoup(result["text"], 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            if selector:
                # Use CSS selector
                elements = soup.select(selector)
            else:
                # Get all elements if no selector
                elements = soup.find_all()

            extracted_data = []

            for element in elements:
                if text_only:
                    # Get text only
                    text = element.get_text(strip=True)
                    if text:
                        extracted_data.append(text)
                elif attributes:
                    # Get specific attributes
                    attrs = {}
                    for attr in attributes:
                        if element.has_attr(attr):
                            attrs[attr] = element[attr]
                    if attrs:
                        extracted_data.append(attrs)
                else:
                    # Get element HTML
                    extracted_data.append(str(element))

            return {
                "success": True,
                "url": result["url"],
                "selector": selector,
                "elements_found": len(extracted_data),
                "data": extracted_data,
                "method": "scrape"
            }

        except Exception as e:
            self.logger.error(f"Error scraping {url}: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to scrape URL: {str(e)}",
                "url": url
            }

    async def search_google(
        self,
        query: str,
        num_results: int = 10,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Search Google (using custom search or scraping)

        Note: This uses scraping which may violate Google's ToS.
        In production, use Google Custom Search JSON API.
        """
        try:
            # Format query for Google search
            formatted_query = query.replace(' ', '+')
            url = f"https://www.google.com/search?q={formatted_query}&num={num_results}&hl={language}"

            # Get search results
            result = await self.get(url)
            if not result["success"]:
                return result

            # Parse results
            soup = BeautifulSoup(result["text"], 'html.parser')

            # Find search result containers
            results = []

            # Try different selectors for Google results
            selectors = [
                'div.g',
                'div.v7W49e',
                'div.tF2Cxc',
                'div[data-sokoban-container]',
                'div.mnr-c'
            ]

            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    for element in elements[:num_results]:
                        try:
                            # Extract title
                            title_elem = element.select_one('h3, .LC20lb, .DKV0Md')
                            title = title_elem.get_text(strip=True) if title_elem else ""

                            # Extract URL
                            link_elem = element.select_one('a')
                            url = link_elem.get('href', '') if link_elem else ""

                            # Extract snippet
                            snippet_elem = element.select_one('.VwiC3b, .s3v9rd, .st, .aCOpRe')
                            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                            if title and url:
                                results.append({
                                    "title": title,
                                    "url": url,
                                    "snippet": snippet
                                })
                        except Exception as e:
                            self.logger.debug(f"Error parsing search result: {e}")
                            continue

                    if results:
                        break  # Found results with this selector

            # If no results found with specific selectors, try a general approach
            if not results:
                # Look for all links and try to extract meaningful data
                links = soup.find_all('a', href=True)
                for link in links[:num_results * 2]:  # Check more links to find good results
                    href = link.get('href', '')
                    if href.startswith('/url?q='):
                        # Extract actual URL from Google's redirect
                        import urllib.parse
                        try:
                            query_params = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                            actual_url = query_params.get('q', [''])[0]
                            if actual_url and actual_url.startswith('http'):
                                title = link.get_text(strip=True)
                                if title:
                                    results.append({
                                        "title": title,
                                        "url": actual_url,
                                        "snippet": ""  # Would need to visit page for snippet
                                    })
                        except:
                            pass

                    if len(results) >= num_results:
                        break

            return {
                "success": True,
                "query": query,
                "results": results,
                "results_count": len(results),
                "method": "google_search"
            }

        except Exception as e:
            self.logger.error(f"Error searching Google for '{query}': {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to search Google: {str(e)}",
                "query": query
            }

    async def get_page_title(self, url: str) -> Dict[str, Any]:
        """Get the title of a webpage"""
        try:
            result = await self.get(url)
            if not result["success"]:
                return result

            soup = BeautifulSoup(result["text"], 'html.parser')
            title_tag = soup.find('title')
            title = title_tag.get_text(strip=True) if title_tag else ""

            return {
                "success": True,
                "url": result["url"],
                "title": title
            }

        except Exception as e:
            self.logger.error(f"Error getting page title for {url}: {e}")
            return {
                "success": False,
                "error": f"Failed to get page title: {str(e)}",
                "url": url
            }

    async def get_meta_description(self, url: str) -> Dict[str, Any]:
        """Get the meta description of a webpage"""
        try:
            result = await self.get(url)
            if not result["success"]:
                return result

            soup = BeautifulSoup(result["text"], 'html.parser')
            meta_tag = soup.find('meta', attrs={'name': 'description'}) or \
                      soup.find('meta', attrs={'property': 'og:description'})
            content = meta_tag.get('content', '').strip() if meta_tag else ""

            return {
                "success": True,
                "url": result["url"],
                "description": content
            }

        except Exception as e:
            self.logger.error(f"Error getting meta description for {url}: {e}")
            return {
                "success": False,
                "error": f"Failed to get meta description: {str(e)}",
                "url": url
            }

    async def download_file(
        self,
        url: str,
        save_path: Optional[str] = None,
        chunk_size: int = 8192
    ) -> Dict[str, Any]:
        """
        Download a file from a URL

        Args:
            url: URL to download from
            save_path: Path to save the file (if None, returns bytes)
            chunk_size: Size of chunks to download

        Returns:
            Dictionary with download info or file path
        """
        try:
            result = await self._fetch(url)
            if not result["success"]:
                return result

            # Get filename from URL or Content-Disposition header
            filename = None
            if save_path:
                filename = save_path
            else:
                # Try to get from Content-Disposition
                content_disposition = result["headers"].get('Content-Disposition', '')
                if 'filename=' in content_disposition:
                    import re
                    match = re.search(r'filename[^;=\n]*=([\'"]*)(.*?)\1', content_disposition)
                    if match:
                        filename = match.group(2)
                if not filename:
                    # Extract from URL
                    parsed = urlparse(result["url"])
                    filename = os.path.basename(parsed.path)
                    if not filename:
                        filename = "downloaded_file"

            # If save_path provided, save to file
            if save_path:
                os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(result["content"])
                return {
                    "success": True,
                    "url": result["url"],
                    "saved_to": save_path,
                    "size": len(result["content"]),
                    "content_type": result["content_type"]
                }
            else:
                # Return the bytes
                return {
                    "success": True,
                    "url": result["url"],
                    "data": result["content"],
                    "size": len(result["content"]),
                    "content_type": result["content_type"],
                    "filename": filename
                }

        except Exception as e:
            self.logger.error(f"Error downloading file from {url}: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to download file: {str(e)}",
                "url": url
            }

    async def extract_links(
        self,
        url: str,
        filter_internal: bool = True,
        filter_external: bool = False
    ) -> Dict[str, Any]:
        """
        Extract all links from a webpage

        Args:
            url: URL to extract links from
            filter_internal: Whether to include internal links
            filter_external: Whether to include external links

        Returns:
            Dictionary with extracted links
        """
        try:
            result = await self.get(url)
            if not result["success"]:
                return result

            soup = BeautifulSoup(result["text"], 'html.parser')
            base_url = result["url"]

            links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                # Convert relative URLs to absolute
                absolute_url = urljoin(base_url, href)
                parsed = urlparse(absolute_url)

                # Skip empty links, anchors, javascript, mailto, etc.
                if not href or href.startswith('#') or href.startswith('javascript:') or href.startswith('mailto:'):
                    continue

                # Determine if link is internal or external
                base_domain = urlparse(base_url).netloc
                link_domain = parsed.netloc
                is_internal = (not link_domain) or (link_domain == base_domain)

                # Apply filters
                if (filter_internal and is_internal) or (filter_external and not is_internal):
                    link_text = link.get_text(strip=True)
                    links.append({
                        "url": absolute_url,
                        "text": link_text[:100],  # Limit text length
                        "is_internal": is_internal
                    })

            # Remove duplicates
            unique_links = []
            seen_urls = set()
            for link in links:
                if link["url"] not in seen_urls:
                    seen_urls.add(link["url"])
                    unique_links.append(link)

            return {
                "success": True,
                "url": base_url,
                "links": unique_links,
                "count": len(unique_links),
                "internal_count": sum(1 for l in unique_links if l["is_internal"]),
                "external_count": sum(1 for l in unique_links if not l["is_internal"])
            }

        except Exception as e:
            self.logger.error(f"Error extracting links from {url}: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to extract links: {str(e)}",
                "url": url
            }

    async def get_website_technology(self, url: str) -> Dict[str, Any]:
        """
        Attempt to detect technologies used by a website
        (Basic implementation - in production would use Wappalyzer or similar)
        """
        try:
            result = await self.get(url)
            if not result["success"]:
                return result

            html = result["text"].lower()
            headers = {k.lower(): v.lower() for k, v in result["headers"].items()}

            technologies = []

            # Check for common frameworks and technologies
            tech_patterns = {
                "WordPress": [
                    "wp-content",
                    "wp-includes",
                    "wordpress",
                    "xmlrpc.php"
                ],
                "Joomla": [
                    "joomla",
                    "/components/",
                    "/modules/",
                    "/templates/"
                ],
                "Drupal": [
                    "drupal",
                    "sites/all/",
                    "misc/drupal.js"
                ],
                "Shopify": [
                    "shopify",
                    "cdn.shopify.com",
                    "Shopify.shop"
                ],
                "Magento": [
                    "magento",
                    "skin/frontend",
                    "js/prototype/prototype.js"
                ],
                "React": [
                    "react",
                    "_react",
                    "react-dom"
                ],
                "Vue.js": [
                    "vue.js",
                    "vue.min.js",
                    "__vue__"
                ],
                "Angular": [
                    "angular",
                    "ng-app",
                    "ng-controller"
                ],
                "jQuery": [
                    "jquery",
                    "jquery.min.js"
                ],
                "Bootstrap": [
                    "bootstrap",
                    "bootstrap.min.css",
                    "bootstrap.bundle.min.js"
                ],
                "Google Analytics": [
                    "google-analytics.com",
                    "gtag(",
                    "ga("
                ],
                "Facebook Pixel": [
                    "facebook.net/tr",
                    "fbq("
                ]
            }

            for tech, patterns in tech_patterns.items():
                for pattern in patterns:
                    if pattern in html:
                        technologies.append(tech)
                        break  # Only count each technology once

            # Check headers for additional clues
            server = headers.get('server', '')
            if server:
                technologies.append(f"Server: {server}")

            powered_by = headers.get('x-powered-by', '')
            if powered_by:
                technologies.append(f"X-Powered-By: {powered_by}")

            # Remove duplicates
            technologies = list(dict.fromkeys(technologies))

            return {
                "success": True,
                "url": url,
                "technologies": technologies,
                "detected_count": len(technologies)
            }

        except Exception as e:
            self.logger.error(f"Error detecting technology for {url}: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to detect technology: {str(e)}",
                "url": url
            }

    async def shutdown(self):
        """Shutdown the browser tool"""
        self.logger.info("Shutting down Browser Tool")
        self.is_initialized = False
        if self.session:
            await self.session.close()