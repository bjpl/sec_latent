"""
SEC EDGAR Connector
Handles data fetching and parsing from SEC EDGAR database
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import aiohttp
from bs4 import BeautifulSoup
import pandas as pd
from ratelimit import limits, sleep_and_retry

from config.settings import get_settings

logger = logging.getLogger(__name__)


class SECEdgarConnector:
    """
    Async connector for SEC EDGAR database
    Implements rate limiting and retry logic
    """

    def __init__(self):
        self.settings = get_settings().sec_edgar
        self.session: Optional[aiohttp.ClientSession] = None
        self._request_count = 0
        self._last_request_time = datetime.now()

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()

    async def connect(self):
        """Initialize HTTP session"""
        if self.session is None:
            headers = {
                "User-Agent": self.settings.user_agent,
                "Accept-Encoding": "gzip, deflate",
                "Host": "www.sec.gov"
            }
            timeout = aiohttp.ClientTimeout(total=self.settings.timeout)
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout
            )
            logger.info("SEC EDGAR connector initialized")

    async def disconnect(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("SEC EDGAR connector closed")

    async def _rate_limit(self):
        """Enforce SEC rate limits (10 requests per second)"""
        current_time = datetime.now()
        time_diff = (current_time - self._last_request_time).total_seconds()

        if time_diff < self.settings.rate_limit_period:
            if self._request_count >= self.settings.rate_limit_requests:
                wait_time = self.settings.rate_limit_period - time_diff
                logger.debug(f"Rate limit reached, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                self._request_count = 0
                self._last_request_time = datetime.now()
        else:
            self._request_count = 0
            self._last_request_time = current_time

        self._request_count += 1

    async def fetch_company_filings(
        self,
        cik: str,
        form_type: str = "10-K",
        count: int = 10,
        before_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch company filings by CIK

        Args:
            cik: Central Index Key (company identifier)
            form_type: Filing form type (10-K, 10-Q, 8-K, etc.)
            count: Number of filings to retrieve
            before_date: Only fetch filings before this date (YYYY-MM-DD)

        Returns:
            List of filing metadata dictionaries
        """
        await self._rate_limit()

        # Normalize CIK (must be 10 digits with leading zeros)
        cik_normalized = str(cik).zfill(10)

        url = f"https://data.sec.gov/submissions/CIK{cik_normalized}.json"

        try:
            async with self.session.get(url) as response:
                response.raise_for_status()
                data = await response.json()

                # Extract filings
                filings = []
                recent_filings = data.get("filings", {}).get("recent", {})

                if not recent_filings:
                    logger.warning(f"No filings found for CIK {cik}")
                    return []

                # Parse filings
                form_types = recent_filings.get("form", [])
                filing_dates = recent_filings.get("filingDate", [])
                accession_numbers = recent_filings.get("accessionNumber", [])
                primary_documents = recent_filings.get("primaryDocument", [])

                for i in range(len(form_types)):
                    if form_types[i] == form_type:
                        filing_date = filing_dates[i]

                        # Filter by date if specified
                        if before_date and filing_date >= before_date:
                            continue

                        filing = {
                            "cik": cik_normalized,
                            "form_type": form_types[i],
                            "filing_date": filing_date,
                            "accession_number": accession_numbers[i],
                            "primary_document": primary_documents[i],
                            "document_url": self._build_document_url(
                                cik_normalized,
                                accession_numbers[i],
                                primary_documents[i]
                            )
                        }
                        filings.append(filing)

                        if len(filings) >= count:
                            break

                logger.info(f"Fetched {len(filings)} {form_type} filings for CIK {cik}")
                return filings

        except aiohttp.ClientError as e:
            logger.error(f"Failed to fetch filings for CIK {cik}: {e}")
            raise

    def _build_document_url(
        self,
        cik: str,
        accession_number: str,
        primary_document: str
    ) -> str:
        """Build full document URL"""
        # Remove dashes from accession number for URL
        accession_clean = accession_number.replace("-", "")
        return (
            f"https://www.sec.gov/Archives/edgar/data/{cik}/"
            f"{accession_clean}/{primary_document}"
        )

    async def fetch_filing_content(self, document_url: str) -> str:
        """
        Fetch raw filing content

        Args:
            document_url: Full URL to filing document

        Returns:
            Raw HTML/text content
        """
        await self._rate_limit()

        try:
            async with self.session.get(document_url) as response:
                response.raise_for_status()
                content = await response.text()
                logger.info(f"Fetched content from {document_url}")
                return content

        except aiohttp.ClientError as e:
            logger.error(f"Failed to fetch content from {document_url}: {e}")
            raise

    async def parse_filing_content(self, html_content: str) -> Dict[str, Any]:
        """
        Parse filing HTML content into structured data

        Args:
            html_content: Raw HTML content

        Returns:
            Parsed filing data
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Extract sections
            parsed = {
                "raw_html": html_content,
                "text_content": soup.get_text(separator="\n", strip=True),
                "sections": {},
                "tables": []
            }

            # Extract common sections
            section_markers = {
                "business": ["Item 1", "Business"],
                "risk_factors": ["Item 1A", "Risk Factors"],
                "md_and_a": ["Item 7", "Management's Discussion"],
                "financial_statements": ["Item 8", "Financial Statements"]
            }

            # Simple section extraction
            for section_name, markers in section_markers.items():
                section_text = self._extract_section(soup, markers)
                if section_text:
                    parsed["sections"][section_name] = section_text

            # Extract tables
            tables = soup.find_all("table")
            for i, table in enumerate(tables[:20]):  # Limit to first 20 tables
                try:
                    df = pd.read_html(str(table))[0]
                    parsed["tables"].append({
                        "index": i,
                        "data": df.to_dict(orient="records"),
                        "shape": df.shape
                    })
                except Exception as e:
                    logger.debug(f"Failed to parse table {i}: {e}")

            logger.info(f"Parsed filing with {len(parsed['sections'])} sections and {len(parsed['tables'])} tables")
            return parsed

        except Exception as e:
            logger.error(f"Failed to parse filing content: {e}")
            raise

    def _extract_section(self, soup: BeautifulSoup, markers: List[str]) -> Optional[str]:
        """Extract section by marker text"""
        for marker in markers:
            # Look for marker in text
            for element in soup.find_all(text=True):
                if marker.lower() in element.lower():
                    # Try to get following content
                    parent = element.parent
                    if parent:
                        # Get next siblings until next section
                        content = []
                        for sibling in parent.next_siblings:
                            if isinstance(sibling, str):
                                content.append(sibling)
                            elif sibling.name:
                                text = sibling.get_text(separator=" ", strip=True)
                                if text:
                                    content.append(text)

                        if content:
                            return "\n".join(content[:100])  # Limit size

        return None

    async def search_companies(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for companies by name or ticker

        Args:
            query: Search query (company name or ticker)
            limit: Maximum results to return

        Returns:
            List of matching companies
        """
        await self._rate_limit()

        # Use SEC's company tickers JSON
        url = "https://www.sec.gov/files/company_tickers.json"

        try:
            async with self.session.get(url) as response:
                response.raise_for_status()
                data = await response.json()

                # Search companies
                results = []
                query_lower = query.lower()

                for entry in data.values():
                    title = entry.get("title", "").lower()
                    ticker = entry.get("ticker", "").lower()

                    if query_lower in title or query_lower in ticker:
                        results.append({
                            "cik": str(entry.get("cik_str")).zfill(10),
                            "ticker": entry.get("ticker"),
                            "title": entry.get("title")
                        })

                        if len(results) >= limit:
                            break

                logger.info(f"Found {len(results)} companies matching '{query}'")
                return results

        except aiohttp.ClientError as e:
            logger.error(f"Failed to search companies: {e}")
            raise


async def test_connector():
    """Test the SEC EDGAR connector"""
    async with SECEdgarConnector() as connector:
        # Search for Apple
        companies = await connector.search_companies("Apple", limit=5)
        print(f"Found companies: {companies}")

        if companies:
            # Fetch Apple's recent 10-K filings
            apple_cik = companies[0]["cik"]
            filings = await connector.fetch_company_filings(
                cik=apple_cik,
                form_type="10-K",
                count=2
            )
            print(f"Recent 10-K filings: {filings}")

            if filings:
                # Fetch and parse first filing
                content = await connector.fetch_filing_content(filings[0]["document_url"])
                parsed = await connector.parse_filing_content(content)
                print(f"Parsed sections: {list(parsed['sections'].keys())}")


if __name__ == "__main__":
    # Run test
    asyncio.run(test_connector())
