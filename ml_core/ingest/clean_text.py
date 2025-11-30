"""
Text Cleaning Module

Professional text cleaning for ISO documents.
Removes page numbers, headers, footers while preserving ISO section structure.
"""

import re
import unicodedata
import logging
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextCleaner:
    """
    Comprehensive text cleaning for ISO documents.
    
    Cleaning operations:
    - Remove page numbers (multiple patterns)
    - Strip headers/footers
    - Normalize whitespace
    - Unicode normalization
    - Preserve ISO section numbering
    """
    
    # Page number patterns to remove
    PAGE_NUMBER_PATTERNS = [
        r'^\s*Page\s+\d+\s*/\s*\d+\s*$',  # "Page 1/30"
        r'^\s*Page\s+\d+\s*$',             # "Page 1"
        r'^\s*p\.\s*\d+\s*$',              # "p.12"
        r'^\s*-\s*\d+\s*-\s*$',            # "- 12 -"
        r'^\s*\d+\s*/\s*\d+\s*$',          # "1/30"
        r'^\s*\[\s*\d+\s*\]\s*$',          # "[12]"
    ]
    
    # Header/footer patterns (customizable)
    HEADER_FOOTER_PATTERNS = [
        r'©\s*ISO\s+\d{4}',                              # © ISO 2015
        r'ISO\s+\d+:\d{4}',                              # ISO 9001:2015
        r'^\s*Draft\s*$',                                # Draft
        r'^\s*Confidential\s*$',                         # Confidential
        r'^\s*Internal\s+use\s+only\s*$',               # Internal use only
    ]
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize text cleaner.
        
        Args:
            config: Optional configuration dict with custom patterns
        """
        self.config = config or {}
        
        # Add custom patterns if provided
        if 'custom_page_patterns' in self.config:
            self.PAGE_NUMBER_PATTERNS.extend(self.config['custom_page_patterns'])
        
        if 'custom_header_patterns' in self.config:
            self.HEADER_FOOTER_PATTERNS.extend(self.config['custom_header_patterns'])
    
    def clean_text(self, text: str) -> str:
        """
        Apply complete cleaning pipeline.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Step 1: Unicode normalization
        text = self._normalize_unicode(text)
        
        # Step 2: Remove page numbers
        text = self._remove_page_numbers(text)
        
        # Step 3: Remove headers/footers
        text = self._remove_headers_footers(text)
        
        # Step 4: Normalize whitespace
        text = self._normalize_whitespace(text)
        
        # Step 5: Clean punctuation
        text = self._normalize_punctuation(text)
        
        # Step 6: Remove empty lines
        text = self._remove_excessive_newlines(text)
        
        return text.strip()
    
    def _normalize_unicode(self, text: str) -> str:
        """Normalize Unicode characters (NFKC normalization)."""
        return unicodedata.normalize('NFKC', text)
    
    def _remove_page_numbers(self, text: str) -> str:
        """
        Remove page numbers using multiple patterns.
        
        Works line-by-line to avoid removing valid numbered sections.
        """
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            is_page_number = False
            
            # Check against all page number patterns
            for pattern in self.PAGE_NUMBER_PATTERNS:
                if re.match(pattern, line.strip(), re.IGNORECASE):
                    is_page_number = True
                    break
            
            # Special case: standalone numbers (but not ISO sections)
            # ISO sections: "4.1.2 Title" - keep these
            # Page numbers: just "12" - remove these
            if re.match(r'^\s*\d+\s*$', line) and not re.match(r'^\s*\d+(\.\d+)+', line):
                is_page_number = True
            
            if not is_page_number:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _remove_headers_footers(self, text: str) -> str:
        """Remove common headers and footers."""
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            is_header_footer = False
            
            for pattern in self.HEADER_FOOTER_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    is_header_footer = True
                    break
            
            if not is_header_footer:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace.
        
        - Convert tabs to spaces
        - Remove trailing whitespace
        - Normalize spaces (multiple → single)
        """
        # Convert tabs to spaces
        text = text.replace('\t', ' ')
        
        # Remove trailing whitespace from each line
        lines = [line.rstrip() for line in text.split('\n')]
        
        # Remove leading whitespace but preserve indentation for lists
        cleaned_lines = []
        for line in lines:
            # Preserve bullet points and numbered lists
            if re.match(r'^\s*[-•*]\s+', line) or re.match(r'^\s*\d+[\.)]\s+', line):
                cleaned_lines.append(line)
            else:
                # For other lines, normalize but keep ISO section numbering
                cleaned_lines.append(line.lstrip())
        
        text = '\n'.join(cleaned_lines)
        
        # Normalize multiple spaces to single space (but not across lines)
        text = re.sub(r' +', ' ', text)
        
        return text
    
    def _normalize_punctuation(self, text: str) -> str:
        """
        Normalize punctuation.
        
        - Fix spacing around punctuation
        - Normalize quotes
        - Clean up special characters
        """
        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        # Fix spacing around punctuation (no space before, one space after)
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)  # Remove space before
        text = re.sub(r'([.,;:!?])([^\s\d])', r'\1 \2', text)  # Add space after
        
        # Fix parentheses spacing
        text = re.sub(r'\(\s+', '(', text)
        text = re.sub(r'\s+\)', ')', text)
        
        return text
    
    def _remove_excessive_newlines(self, text: str) -> str:
        """
        Remove excessive newlines.
        
        - Multiple newlines → maximum 2 (paragraph break)
        """
        # Replace 3+ newlines with 2 newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text
    
    def clean_for_iso_sections(self, text: str) -> str:
        """
        Special cleaning mode that aggressively preserves ISO section structure.
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text with ISO sections preserved
        """
        # Standard cleaning
        text = self.clean_text(text)
        
        # Additional: Ensure ISO sections start on new lines
        # Pattern: "4.1.2 Title" should be on its own line
        text = re.sub(
            r'([^\n])(\d+\.\d+(\.\d+)*\s+[A-Z])', 
            r'\1\n\n\2', 
            text
        )
        
        return text


def clean_text(text: str, config: Optional[Dict] = None) -> str:
    """
    Convenience function for text cleaning.
    
    Args:
        text: Text to clean
        config: Optional configuration
        
    Returns:
        Cleaned text
    """
    cleaner = TextCleaner(config)
    return cleaner.clean_text(text)


def clean_iso_text(text: str) -> str:
    """
    Clean text while preserving ISO structure.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text optimized for ISO sections
    """
    cleaner = TextCleaner()
    return cleaner.clean_for_iso_sections(text)


if __name__ == "__main__":
    # Example usage
    sample_text = """
    Page 1/30
    
    ISO 9001:2015
    
    4 Contexte de l'organisme
    
    4.1 Compréhension de l'organisme
    
    L'organisme   doit   déterminer   les   enjeux...
    
    
    
    Page 2/30
    
    © ISO 2015
    
    4.1.2 Champ d'application
    
    Text here...
    """
    
    cleaned = clean_iso_text(sample_text)
    print("=== Original ===")
    print(sample_text)
    print("\n=== Cleaned ===")
    print(cleaned)
