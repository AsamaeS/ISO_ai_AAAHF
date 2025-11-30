"""
ISO Section Parser

Parses ISO document structure using regex-based section detection.
Recognizes hierarchical sections like:
- 4 Contexte de l'organisme
- 4.1 Compréhension de l'organisme
- 4.1.2 Champ d'application
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Section:
    """Container for ISO section information."""
    section_id: str
    section_name: str
    text: str
    page_start: int
    page_end: int
    level: int  # Hierarchy depth (4=1, 4.1=2, 4.1.2=3)
    parent_id: Optional[str] = None


class ISOSectionParser:
    """
    Parser for ISO document sections.
    
    Detects sections using pattern: ^\d+(\.\d+)*\s+[A-Z]
    
    Examples:
    - "4 Contexte de l'organisme"
    - "4.1 Compréhension de l'organisme et de son contexte"
    - "4.1.2 Champ d'application du système de management"
    """
    
    # ISO section pattern: number(s) followed by space and capitalized text
    SECTION_PATTERN = r'^(\d+(?:\.\d+)*)\s+([A-ZÀ-ÿ][^\n]+?)(?:\s*\.{3,}|\s*$)'
    
    # Alternative pattern for sections without trailing dots
    SECTION_PATTERN_ALT = r'^(\d+(?:\.\d+)*)\s+([A-ZÀ-ÿ][^\n]*?)$'
    
    def __init__(self, strict_mode: bool = False):
        """
        Initialize section parser.
        
        Args:
            strict_mode: If True, only match sections starting with capital letter
        """
        self.strict_mode = strict_mode
    
    def parse_sections(
        self, 
        text: str, 
        page_info: Optional[List[Dict]] = None
    ) -> List[Section]:
        """
        Parse text into ISO sections.
        
        Args:
            text: Full document text
            page_info: Optional list of page metadata with char offsets
            
        Returns:
            List of Section objects
        """
        sections = []
        lines = text.split('\n')
        
        current_section = None
        current_text = []
        current_page = 1
        
        for i, line in enumerate(lines):
            # Check if line is a section header
            match = self._match_section_header(line)
            
            if match:
                # Save previous section if exists
                if current_section:
                    current_section.text = '\n'.join(current_text).strip()
                    sections.append(current_section)
                
                # Start new section
                section_id, section_name = match
                level = self._get_section_level(section_id)
                parent_id = self._get_parent_id(section_id)
                
                current_section = Section(
                    section_id=section_id,
                    section_name=section_name.strip(),
                    text="",
                    page_start=current_page,
                    page_end=current_page,
                    level=level,
                    parent_id=parent_id
                )
                current_text = []
                
                logger.debug(f"Found section: {section_id} {section_name}")
            else:
                # Add to current section text
                if current_section and line.strip():
                    current_text.append(line)
        
        # Save last section
        if current_section:
            current_section.text = '\n'.join(current_text).strip()
            sections.append(current_section)
        
        # Update page numbers if page_info provided
        if page_info:
            sections = self._update_page_numbers(sections, text, page_info)
        
        logger.info(f"Parsed {len(sections)} sections")
        return sections
    
    def _match_section_header(self, line: str) -> Optional[Tuple[str, str]]:
        """
        Check if line matches ISO section pattern.
        
        Args:
            line: Line to check
            
        Returns:
            Tuple of (section_id, section_name) or None
        """
        line = line.strip()
        
        # Try primary pattern
        match = re.match(self.SECTION_PATTERN, line, re.MULTILINE)
        if match:
            return match.group(1), match.group(2)
        
        # Try alternative pattern
        match = re.match(self.SECTION_PATTERN_ALT, line)
        if match:
            section_id = match.group(1)
            section_name = match.group(2).strip()
            
            # Validate: must have meaningful name
            if len(section_name) > 2:
                return section_id, section_name
        
        return None
    
    def _get_section_level(self, section_id: str) -> int:
        """
        Determine section hierarchy level.
        
        Args:
            section_id: Section ID like "4.1.2"
            
        Returns:
            Level (1 for "4", 2 for "4.1", 3 for "4.1.2")
        """
        return len(section_id.split('.'))
    
    def _get_parent_id(self, section_id: str) -> Optional[str]:
        """
        Get parent section ID.
        
        Args:
            section_id: Section ID like "4.1.2"
            
        Returns:
            Parent ID like "4.1" or None if top-level
        """
        parts = section_id.split('.')
        if len(parts) > 1:
            return '.'.join(parts[:-1])
        return None
    
    def _update_page_numbers(
        self, 
        sections: List[Section], 
        full_text: str,
        page_info: List[Dict]
    ) -> List[Section]:
        """
        Update page numbers based on character offsets.
        
        Args:
            sections: List of sections
            full_text: Complete document text
            page_info: Page metadata with char offsets
            
        Returns:
            Sections with updated page numbers
        """
        # Build character offset map for each section
        for section in sections:
            # Find section position in full text
            section_header = f"{section.section_id} {section.section_name}"
            section_pos = full_text.find(section_header)
            
            if section_pos >= 0:
                # Find which page this falls on
                for page in page_info:
                    if 'char_start' in page and 'char_end' in page:
                        if page['char_start'] <= section_pos < page['char_end']:
                            section.page_start = page['page_number']
                            section.page_end = page['page_number']
                            break
        
        return sections
    
    def get_section_hierarchy(self, sections: List[Section]) -> Dict:
        """
        Build hierarchical structure of sections.
        
        Args:
            sections: List of sections
            
        Returns:
            Nested dict representing section hierarchy
        """
        hierarchy = {}
        
        for section in sections:
            # Create path to this section
            parts = section.section_id.split('.')
            current = hierarchy
            
            for i, part in enumerate(parts):
                partial_id = '.'.join(parts[:i+1])
                if partial_id not in current:
                    current[partial_id] = {
                        'section': section if partial_id == section.section_id else None,
                        'children': {}
                    }
                current = current[partial_id]['children']
        
        return hierarchy
    
    def find_section(self, sections: List[Section], section_id: str) -> Optional[Section]:
        """
        Find section by ID.
        
        Args:
            sections: List of sections
            section_id: Section ID to find
            
        Returns:
            Section or None
        """
        for section in sections:
            if section.section_id == section_id:
                return section
        return None


def parse_sections(text: str, page_info: Optional[List[Dict]] = None) -> List[Dict]:
    """
    Convenience function to parse ISO sections.
    
    Args:
        text: Document text
        page_info: Optional page metadata
        
    Returns:
        List of section dictionaries
    """
    parser = ISOSectionParser()
    sections = parser.parse_sections(text, page_info)
    
    # Convert to dicts for easier serialization
    return [
        {
            'section_id': s.section_id,
            'section_name': s.section_name,
            'text': s.text,
            'page_start': s.page_start,
            'page_end': s.page_end,
            'level': s.level,
            'parent_id': s.parent_id
        }
        for s in sections
    ]


if __name__ == "__main__":
    # Example usage
    sample_text = """
4 Contexte de l'organisme

L'organisme doit déterminer les enjeux externes et internes pertinents...

4.1 Compréhension de l'organisme et de son contexte

L'organisme doit déterminer les enjeux externes et internes pertinents 
au regard de sa finalité et de son orientation stratégique...

4.1.2 Champ d'application du système de management

L'organisme doit déterminer les limites et l'applicabilité du système...

4.2 Besoins et attentes des parties intéressées

L'organisme doit déterminer les parties intéressées pertinentes...
    """
    
    sections = parse_sections(sample_text)
    print(f"Found {len(sections)} sections:\n")
    for section in sections:
        indent = "  " * (section['level'] - 1)
        print(f"{indent}{section['section_id']} - {section['section_name']}")
        print(f"{indent}  Level: {section['level']}, Parent: {section['parent_id']}")
        print(f"{indent}  Text preview: {section['text'][:80]}...")
        print()
