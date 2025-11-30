"""
PDF Text Extraction Module

Extracts text from PDF files with support for both text-based and scanned PDFs.
Uses pdfminer.six for text extraction and falls back to Tesseract/PaddleOCR for scanned pages.
"""

import logging
import io
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

try:
    from pdfminer.high_level import extract_pages, extract_text
    from pdfminer.layout import LTTextContainer, LTChar, LTFigure, LTImage
except ImportError:
    raise ImportError("pdfminer.six is required. Install: pip install pdfminer.six")

try:
    from PIL import Image
    import pytesseract
except ImportError:
    raise ImportError("Pytesseract and Pillow required. Install: pip install pytesseract Pillow")

try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False
    logging.warning("PaddleOCR not available. Install: pip install paddleocr")

import fitz  # PyMuPDF for image extraction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PageContent:
    """Container for page text and metadata."""
    page_number: int
    text: str
    is_scanned: bool
    char_count: int
    

@dataclass
class PDFExtractionResult:
    """Complete PDF extraction result."""
    pages: List[PageContent]
    total_pages: int
    total_chars: int
    scanned_pages: int
    extraction_method: str


class PDFExtractor:
    """
    PDF text extraction with OCR fallback.
    
    Workflow:
    1. Try to extract text using pdfminer
    2. If page has very little text (likely scanned), use OCR
    3. Support both Tesseract and PaddleOCR
    """
    
    def __init__(
        self, 
        use_paddleocr: bool = True,
        min_chars_threshold: int = 100,
        tesseract_lang: str = 'eng+fra'  # English + French for ISO docs
    ):
        """
        Initialize PDF extractor.
        
        Args:
            use_paddleocr: Use PaddleOCR if available (better accuracy)
            min_chars_threshold: Min chars to consider page as text-based
            tesseract_lang: Language for Tesseract OCR
        """
        self.min_chars_threshold = min_chars_threshold
        self.tesseract_lang = tesseract_lang
        self.use_paddleocr = use_paddleocr and PADDLEOCR_AVAILABLE
        
        # Initialize PaddleOCR if requested
        self.paddle_ocr = None
        if self.use_paddleocr:
            try:
                self.paddle_ocr = PaddleOCR(
                    use_angle_cls=True, 
                    lang='en',  # Can be changed to 'fr' for French
                    use_gpu=False,  # CPU only for Intel GPU compatibility
                    show_log=False
                )
                logger.info("PaddleOCR initialized successfully")
            except Exception as e:
                logger.warning(f"PaddleOCR init failed: {e}. Falling back to Tesseract")
                self.use_paddleocr = False
    
    def extract_from_pdf(self, pdf_path: str) -> PDFExtractionResult:
        """
        Extract text from PDF file.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            PDFExtractionResult with all extracted pages
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        logger.info(f"Starting extraction from: {pdf_path.name}")
        
        # Open PDF with PyMuPDF for page count and images
        pdf_doc = fitz.open(str(pdf_path))
        total_pages = len(pdf_doc)
        
        pages = []
        scanned_count = 0
        
        for page_num in range(total_pages):
            logger.info(f"Processing page {page_num + 1}/{total_pages}")
            
            # First try text extraction with pdfminer
            page_text = self._extract_text_from_page(str(pdf_path), page_num)
            
            is_scanned = len(page_text.strip()) < self.min_chars_threshold
            
            # If likely scanned, use OCR
            if is_scanned:
                logger.info(f"Page {page_num + 1} appears scanned, using OCR")
                page_text = self._ocr_page(pdf_doc, page_num)
                scanned_count += 1
            
            pages.append(PageContent(
                page_number=page_num + 1,
                text=page_text,
                is_scanned=is_scanned,
                char_count=len(page_text)
            ))
        
        pdf_doc.close()
        
        total_chars = sum(p.char_count for p in pages)
        extraction_method = "Mixed (Text + OCR)" if scanned_count > 0 else "Text-based"
        
        logger.info(f"Extraction complete: {total_pages} pages, {total_chars} chars, "
                   f"{scanned_count} scanned pages")
        
        return PDFExtractionResult(
            pages=pages,
            total_pages=total_pages,
            total_chars=total_chars,
            scanned_pages=scanned_count,
            extraction_method=extraction_method
        )
    
    def _extract_text_from_page(self, pdf_path: str, page_num: int) -> str:
        """Extract text from a specific page using pdfminer."""
        try:
            # Extract text for specific page
            text = ""
            for page_layout in extract_pages(pdf_path, page_numbers=[page_num]):
                for element in page_layout:
                    if isinstance(element, LTTextContainer):
                        text += element.get_text()
            return text
        except Exception as e:
            logger.error(f"Text extraction failed for page {page_num}: {e}")
            return ""
    
    def _ocr_page(self, pdf_doc: fitz.Document, page_num: int) -> str:
        """
        Perform OCR on a PDF page.
        
        Args:
            pdf_doc: PyMuPDF document
            page_num: Page number (0-indexed)
            
        Returns:
            Extracted text from OCR
        """
        try:
            page = pdf_doc[page_num]
            
            # Render page to image (higher DPI = better OCR)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x scale
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Try PaddleOCR first if available
            if self.use_paddleocr and self.paddle_ocr:
                return self._paddleocr_image(img)
            else:
                return self._tesseract_image(img)
                
        except Exception as e:
            logger.error(f"OCR failed for page {page_num}: {e}")
            return ""
    
    def _paddleocr_image(self, image: Image.Image) -> str:
        """Extract text using PaddleOCR."""
        try:
            import numpy as np
            img_array = np.array(image)
            result = self.paddle_ocr.ocr(img_array, cls=True)
            
            # Extract text from result
            if result and result[0]:
                text_lines = [line[1][0] for line in result[0]]
                return "\n".join(text_lines)
            return ""
        except Exception as e:
            logger.error(f"PaddleOCR error: {e}")
            return ""
    
    def _tesseract_image(self, image: Image.Image) -> str:
        """Extract text using Tesseract."""
        try:
            text = pytesseract.image_to_string(image, lang=self.tesseract_lang)
            return text
        except Exception as e:
            logger.error(f"Tesseract error: {e}")
            return ""


def extract_text_from_pdf(
    pdf_path: str, 
    use_paddleocr: bool = True,
    min_chars_threshold: int = 100
) -> Dict:
    """
    Convenience function to extract text from PDF.
    
    Args:
        pdf_path: Path to PDF file
        use_paddleocr: Use PaddleOCR if available
        min_chars_threshold: Minimum characters to consider page text-based
        
    Returns:
        Dictionary with extraction results
    """
    extractor = PDFExtractor(
        use_paddleocr=use_paddleocr,
        min_chars_threshold=min_chars_threshold
    )
    
    result = extractor.extract_from_pdf(pdf_path)
    
    # Convert to dict for easier usage
    return {
        "pages": [
            {
                "page_number": p.page_number,
                "text": p.text,
                "is_scanned": p.is_scanned,
                "char_count": p.char_count
            }
            for p in result.pages
        ],
        "total_pages": result.total_pages,
        "total_chars": result.total_chars,
        "scanned_pages": result.scanned_pages,
        "extraction_method": result.extraction_method,
        "full_text": "\n\n".join(p.text for p in result.pages)
    }


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]
        result = extract_text_from_pdf(pdf_file)
        print(f"\n=== Extraction Results ===")
        print(f"Total pages: {result['total_pages']}")
        print(f"Total characters: {result['total_chars']}")
        print(f"Scanned pages: {result['scanned_pages']}")
        print(f"Method: {result['extraction_method']}")
        print(f"\n=== First 500 characters ===")
        print(result['full_text'][:500])
    else:
        print("Usage: python pdf_to_text.py <pdf_file>")
