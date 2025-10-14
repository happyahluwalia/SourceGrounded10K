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
    DATA_SEC_BASE_URL = "https://data.sec.gov"

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

    def get_company_filings(
        self,
        ticker: str,
        filing_types: list = None,
        limit: int = 10,
    ) -> list:
    
        """
        Get recent filings for a company.

        Args:
            ticker: Stock ticker symbol (e.g., "AAPL")
            filing_types: List of form types to filter (e.g., ["10-K", "10-Q"])
                        If None, returns all filings
            limit: Maximum number of filings to return
        Returns:
            List of filing metadata (accession number, filing date, form type, etc.)
        Example:
        filings = client.get_company_filings("AAPL", filing_types=["10-K"], limit=5)
        """

        cik = self.ticker_to_cik(ticker)

        # Fetch submissions data
        self.rate_limit()
        url = f"{self.DATA_SEC_BASE_URL}/submissions/CIK{cik:010d}.json"

        response = self.session.get(url)
        response.raise_for_status()

        data = response.json()

        
        #Extract recent filings
        recent_filings = data.get("filings", {}).get("recent", [])

        # build list of filings
        filings = []
        num_filings = len(recent_filings.get("form",[]))

        for i in range(num_filings):
            form_type = recent_filings["form"][i]

            # filter by filing type if specified
            if filing_types and form_type not in filing_types:
                continue

            filing = {
                "form": form_type,
                "filingDate": recent_filings["filingDate"][i],
                "reportDate": recent_filings["reportDate"][i],
                "accessionNumber": recent_filings["accessionNumber"][i],
                "primaryDocument": recent_filings["primaryDocument"][i],
                "cik":cik,
                "ticker":ticker.upper(),
            }

            # construct document url
            filing["documentURL"] = self._build_document_url(
                cik,
                filing["accessionNumber"],
                filing["primaryDocument"],
            )

            filings.append(filing)

            # stop if we hit limit
            if len(filings) >=  limit:
                break

        return filings

    def _build_document_url(self, cik: int, accession_number : str, primary_document: str):
        """
        Build url to access the filing document

        SEC URL Format
            https://www.sec.gov/Archives/edgar/data/{CIK}/{AccessionNumber-no-dashes}/{filename}

        """

        # remove dashes from accession number
        acc_no_dashes = accession_number.replace("-","")

        return f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_no_dashes}/{primary_document}"


    # TODO: this does not download any images in the filing like charts etc
    def download_filing(self, filing: dict, output_dir: str="data/filings") -> str:
        """
        Download a filing document to disk.

        Args: 
            filing: Filing dict from get_company_filings()
            output_dir: Base directory for downloads
        Returns:
            Path to downloaded file
        
        File organization:
            data/filings/{ticker}/{year}-{form}-{report_date}.html
        
        Example:
            data/filings/AAPL/2024-10k-20240928.html
        """

        import os 
        from pathlib import Path

        # create directory structure
        ticker = filing["ticker"]
        ticker_dir = Path(output_dir) / ticker
        ticker_dir.mkdir(parents=True, exist_ok=True)

        # create filename: 2024-10k-20240928.html
        year = filing["reportDate"][:4]
        form = filing["form"]
        report_date = filing["reportDate"]
        filename = f"{year}-{form}-{report_date}.html"
        filepath = ticker_dir / filename

        # check if already downloaded
        if filepath.exists():
            print(f"  Already exists: {filepath}")
            return str(filepath)
        
        # download
        print(f"  Downloading: {filing['documentURL']}")
        self.rate_limit()

        response = self.session.get(filing["documentURL"])
        response.raise_for_status()

        # save to disk
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(response.text)

        print(f" ✅ Saved: {filepath}") 
        return str(filepath)
