# BeautifulSoup for HTML parsing, typing for type hints, re for regex pattern matching
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import re 


class SECFilingParser:
    """
    Parse SEC Filings (10-k, 10-Q) from HTML

    SEC Filing has standard structure:
    - Item 1: Business
    - Item 1A: Risk Factors
    - Item 1B: Unresolved Staff Comments
    - Item 2: Properties
    - Item 3: Legal Proceedings
    - Item 4: Mine Safety Disclosures
    - Item 5: Market for Registrant's Common Equity
    - Item 6: [Reserved]
    - Item 7: Management's Discussion and Analysis (MD&A)
    - Item 7A: Quantitative & Qualitative Disclosures and market Risks
    - Item 8: Financial Statements and Supplementary Data
    - Item 9: Changes in and Disagreements with Accountants
    - Item 10: Directors, Executive officers & Corporate Governance
    .... and more
    """

    def __init__(self, filepath:str ):
        """
        Initialize parser with a filing html file

        Args:
            filepath: Path to HTML FILE to parse
        """
        # Read the HTML file from disk
        with open(filepath, 'r', encoding="utf-8") as f:
            html_content = f.read()
        
        # Parse HTML using lxml parser (faster and more robust than html.parser)
        self.soup = BeautifulSoup(html_content,'html.parser')
        self.filepath = filepath

        # Remove script and style elements to clean up the content
        # decompose() removes the element from the tree entirely
        for element in self.soup(['script','style']):
            element.decompose()
        
    
    def get_full_text(self) -> str:
        """
            Extract all text from the filing

            Returns:
                Clean text with normalized whitespace
        """

        # Extract all text from HTML, using newline as separator between elements
        text = self.soup.get_text(separator='\n', strip=True)

        # Normalize white space: strip each line and remove empty lines
        lines = [line.strip() for line in text.split('\n')]
        lines = [line for line in lines if line] # remove empty lines

        # Rejoin lines with single newlines
        return '\n'.join(lines)
    
    def extract_sections(self) -> Dict[str, str]:
        """
        Extract major sections from the filing.

        This is tricky because SEC filings have inconsistent formatting.
        We look for patterns like:
        - "Item 1. " or "Item 1:" or "ITEM 1."
        - "Item 1A" (with letter suffix)

        Returns:
            Dict mapping section name to text content
        """

        # Get the full text content of the filing
        full_text = self.get_full_text()

        # Pattern to match section headers
        # Matches: "Item 1.", "ITEM 1A:", "Item 7 -", etc.
        # ^ITEM - starts with ITEM (case insensitive)
        # \s+ - one or more whitespace
        # (\d+[A-Z]?) - capture group 1: digits followed by optional letter (e.g., "1A")
        # [\.\:\-\s]+ - one or more of: period, colon, dash, or whitespace
        # (.+?)$ - capture group 2: rest of line (section title)
        section_pattern = re.compile(
            r'^ITEM\s+(\d+[A-Z]?)[\.\:\-\s]+(.+?)$',
            re.IGNORECASE | re.MULTILINE
        )

        # Find all section headers in the document
        sections = {}
        matches = list(section_pattern.finditer(full_text))

        # Iterate through all matched section headers
        for i, match in enumerate(matches):
            # Extract section number (e.g., "1", "1A") and title from regex groups
            section_num = match.group(1)
            section_title = match.group(2).strip()
            raw_section_name = f"Item {section_num} : {section_title}"

            # Normalize it
            section_name = self.normalize_section_name(raw_section_name)
   

            # Extract text between this section and the next section
            # start_pos: right after the header line
            # end_pos: start of next section, or end of document if this is the last section
            start_pos = match.end()
            end_pos = matches[i + 1].start() if i+1 < len(matches) else len(full_text)

            section_text = full_text[start_pos:end_pos].strip()

            # Only keep sections with substantial content (filter out empty/tiny sections)
            if len(section_text) > 100: # atleast 100 characters
                sections[section_name] = section_text

        return sections

    def extract_tables(self) -> List[Dict[str,any]]:
        """
        Extract tables from the filing.

        Tables contain financial data - we want to preserve structure

        Returns:
            List of dicts with table data and metadata
        """

        tables = []

        # Iterate through all <table> elements in the HTML
        for idx, table in enumerate(self.soup.find_all('table')):
            # Skip very small tables (likely formatting/layout, not financial data)
            rows = table.find_all('tr')
            if len(rows) < 2: # need atleast header + 1 data row
                continue

        # Convert HTML table to structured list of lists
        table_data = []
        for row in rows:
            # Find all cells (both td and th tags)
            cells = row.find_all(['td','th'])
            # Extract text from each cell
            row_data = [cell.get_text(strip=True) for cell in cells]
            # Only add row if it has at least one non-empty cell
            if any(row_data):
                table_data.append(row_data)
            
            # Only keep tables with actual content (more than just header)
            if len(table_data) > 1:
                tables.append({
                    "table_index": idx,  # Position in document
                    "num_rows": len(table_data),
                    "num_cols": len(table_data[0]) if table_data else 0,
                    "data": table_data,  # Raw 2D array
                    "text": self._table_to_text(table_data)  # Text representation for search
                })
            
        return tables

    
    def _table_to_text(self, table_data: List[List[str]]) -> str:
        """
        Convert table data to text format

        This makes tables searchable in RAG while preserving structure
        """

        lines = []
        for row in table_data:
            # Join cells with pipe separator (creates markdown-like table format)
            lines.append(" | ".join(row))
        
        # Join all rows with newlines to create readable text representation
        return "\n".join(lines)

    def get_metadata(self) -> Dict[str,str]:
        """
        Extract metadata from filing (company name, filing date, etc)

        This is oftern in specific tags or patterns in the html.
        """

        metadata = {}

        # Try to find company name (often in <title> tag or specific div)
        title = self.soup.find('title')
        if title:
            metadata['title'] = title.get_text(strip=True)
        
        # Look for common metadata patterns
        # SEC filings often have metadata in specific formats (e.g., XBRL tags, specific divs)
        # TODO:: This is simplified - real implementation would be more robust
        # Could extract: filing date, CIK, fiscal year end, etc.
        
        return metadata
    
    @staticmethod
    def normalize_section_name(section_name: str) -> str:
        """
        Normalize section names for consistent matching.
        
        Examples:
            "Item 1A : Risk Factors" → "Item 1A: Risk Factors"
            "Item  7  -  MD&A" → "Item 7: MD&A"
            "ITEM 1A. Risk Factors" → "Item 1A: Risk Factors"
        
        Args:
            section_name: Raw section name from HTML
            
        Returns:
            Normalized section name
        """
        # Remove extra spaces around punctuation
        section_name = re.sub(r'\s+([:\.\-])\s+', r'\1 ', section_name)
        
        # Standardize separators to colon
        section_name = re.sub(r'[\.\-]\s', ': ', section_name)
        
        # Remove extra whitespace
        section_name = re.sub(r'\s+', ' ', section_name)
        
        # Standardize case: "Item" with capital I, number/letter stays as-is
        section_name = re.sub(r'(?i)^item\s+', 'Item ', section_name)
        
        return section_name.strip()
            

