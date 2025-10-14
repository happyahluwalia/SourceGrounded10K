# Client to get company information from SEC website. We start with CIK lookup as ticker is not what is used
import requests
import time 
from typing import Optional, Dict 
from app.core.config import settings 

class SECClient:
    """
    Client for SEC EDGAR API.

    SEC requirements:
    - Must include User-Agent with company name and email
    - Rate limit : Max 10 requests per second
    """

    BASE_URL = "https://sec.gov"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": settings.sec_user_agent,
            "Accept-Encoding": "gzip, deflate"
        })

        self.last_request_time = 0

        # Cache for ticket -> CIK mapping
        # TODO: Persist this for later as on restart we lose everything
        self.__ticker_to_cik_cache = {}

    def rate_limit(self):
        """
        Enforce SEC's 10 requests/second rate limit.
        SEC will block IP if we excceed this.
        """

        elapsed = time.time() - self.last_request_time
        if elapsed < 0.1: #100ms = 10 req/sec
            time.sleep(0.1 - elapsed)
        
        self.last_request_time = time.time()

    def ticker_to_cik(self, ticker:str)-> int:
        """
        Convert stock ticker to CIK (Central Index Key) using SEC API.
        Example: "AAPL" -> 320193
        Caches results for faster lookups as they rarely change
        """

        ticker = ticker.upper()
        if ticker in self.__ticker_to_cik_cache:
            return self.__ticker_to_cik_cache[ticker]
        
        # Fetch from SEC
        self.rate_limit()
        url = f"{self.BASE_URL}/files/company_tickers.json"

        response = self.session.get(url)
        response.raise_for_status()

        data = response.json()

        # Data format: {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}, ...}
        for item in data.values():
            if item['ticker'].upper() == ticker:
                cik = int(item['cik_str'])
                self.__ticker_to_cik_cache[ticker] = cik
                return cik
        
        raise ValueError(f"Ticker '{ticker}' not found in SEC Database")