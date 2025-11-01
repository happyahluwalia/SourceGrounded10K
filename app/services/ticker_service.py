#!/usr/bin/env python3
"""
Provides a fast, local lookup service for mapping company names to tickers.
"""

import requests
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

class TickerService:
    """
    Loads the SEC's company ticker data and provides a lookup method.
    
    This service downloads the entire ticker/CIK mapping from the SEC
    and caches it in memory for fast, local lookups.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(TickerService, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        # Prevent re-initialization
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Gemini Agent contact@example.com",
            "Accept-Encoding": "gzip, deflate"
        })
        self._ticker_map = self._load_ticker_map()
        self._initialized = True

    def _load_ticker_map(self) -> dict:
        """
        Downloads and processes the SEC company ticker JSON file.
        Returns a dictionary mapping lowercase names/tickers to official tickers.
        """
        logger.info("Initializing TickerService: downloading SEC ticker data...")
        url = "https://www.sec.gov/files/company_tickers.json"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            
            ticker_map = {}
            # Data format: {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}, ...}
            for item in data.values():
                ticker = item['ticker']
                title = item['title']
                # Map lowercase ticker to official ticker
                ticker_map[ticker.lower()] = ticker
                # Map lowercase title (company name) to official ticker
                ticker_map[title.lower()] = ticker
            
            logger.info(f"SUCCESS: TickerService initialized with {len(ticker_map)} mappings.")
            return ticker_map
        except Exception as e:
            logger.error(f"FATAL: Failed to initialize TickerService. Could not load SEC ticker data: {e}")
            return {}

    def get_ticker(self, name_or_ticker: str) -> str | None:
        """
        Finds the official ticker for a given company name or ticker symbol.

        Args:
            name_or_ticker: The company name or ticker to look up.

        Returns:
            The official ticker symbol (e.g., 'HOOD') or None if not found.
        """
        if not self._ticker_map:
            logger.error("TickerService is not initialized. Cannot perform lookup.")
            return None
            
        return self._ticker_map.get(name_or_ticker.lower())

# Singleton instance for easy use across the application
@lru_cache(maxsize=1)
def get_ticker_service():
    return TickerService()
