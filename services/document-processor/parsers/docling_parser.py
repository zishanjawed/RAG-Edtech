"""
Document parser for intelligent document processing.
Supports PDF, MD, TXT, and DOCX files.
"""
from PyPDF2 import PdfReader
from docx import Document as DocxDocument
import markdown
from pathlib import Path
from typing import Dict, Any, List
import tempfile
import os
import re

from shared.exceptions.custom_exceptions import ParsingError, DocumentProcessingError
from shared.logging.logger import get_logger

logger = get_logger("docling_parser")


class DoclingParser:
    """Parse documents using PyPDF2, python-docx, and markdown."""
    
    def __init__(self):
        """Initialize document parser."""
        logger.info("Document parser initialized")
    
    def parse_document(
        self,
        file_path: str,
        file_type: str
    ) -> Dict[str, Any]:
        """
        Parse a document using appropriate parser based on file type.
        
        Args:
            file_path: Path to the document file
            file_type: Type of file (pdf, md, txt, docx)
        
        Returns:
            Parsed document structure
        
        Raises:
            ParsingError: If parsing fails
        """
        try:
            logger.info(f"Parsing document: {file_path} (type: {file_type})")
            
            file_type_lower = file_type.lower()
            
            if file_type_lower == 'pdf':
                document_data = self._parse_pdf(file_path)
            elif file_type_lower in ['md', 'markdown']:
                document_data = self._parse_markdown(file_path)
            elif file_type_lower == 'txt':
                document_data = self._parse_txt(file_path)
            elif file_type_lower in ['docx', 'doc']:
                document_data = self._parse_docx(file_path)
            else:
                raise ParsingError(f"Unsupported file type: {file_type}")
            
            # Add common metadata
            document_data["metadata"]["file_type"] = file_type
            
            logger.info(f"Successfully parsed document: {file_path}")
            
            return document_data
            
        except Exception as e:
            logger.error(f"Failed to parse document {file_path}: {str(e)}")
            raise ParsingError(
                f"Failed to parse document: {str(e)}",
                details={"file_path": file_path, "file_type": file_type}
            )
    
    def _parse_pdf(self, file_path: str) -> Dict[str, Any]:
        """Parse PDF file using PyPDF2."""
        reader = PdfReader(file_path)
        
        # Extract text from all pages
        content_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                content_parts.append(text)
        
        content = "\n\n".join(content_parts)
        title = self._extract_title_from_content(content)
        structure = self._extract_structure_from_content(content)
        
        return {
            "title": title,
            "content": content,
            "metadata": {
                "page_count": len(reader.pages),
                "tables": [],
                "figures": []
            },
            "structure": structure
        }
    
    def _parse_markdown(self, file_path: str) -> Dict[str, Any]:
        """Parse Markdown file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        title = self._extract_title_from_content(content)
        structure = self._extract_structure_from_content(content)
        
        return {
            "title": title,
            "content": content,
            "metadata": {
                "page_count": 1,
                "tables": [],
                "figures": []
            },
            "structure": structure
        }
    
    def _parse_txt(self, file_path: str) -> Dict[str, Any]:
        """Parse plain text file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        title = self._extract_title_from_content(content)
        structure = self._extract_structure_from_content(content)
        
        return {
            "title": title,
            "content": content,
            "metadata": {
                "page_count": 1,
                "tables": [],
                "figures": []
            },
            "structure": structure
        }
    
    def _parse_docx(self, file_path: str) -> Dict[str, Any]:
        """Parse DOCX file using python-docx."""
        doc = DocxDocument(file_path)
        
        # Extract text from paragraphs
        content_parts = []
        for para in doc.paragraphs:
            if para.text.strip():
                content_parts.append(para.text)
        
        content = "\n\n".join(content_parts)
        title = self._extract_title_from_content(content)
        structure = self._extract_structure_from_content(content)
        
        return {
            "title": title,
            "content": content,
            "metadata": {
                "page_count": 1,  # DOCX doesn't have clear page breaks
                "tables": [],
                "figures": []
            },
            "structure": structure
        }
    
    def _extract_title_from_content(self, content: str) -> str:
        """Extract document title from content."""
        try:
            lines = content.strip().split('\n')
            
            # Look for markdown-style heading
            for line in lines:
                line = line.strip()
                if line.startswith('# '):
                    return line.replace('# ', '').strip()
                elif line:
                    # Use first non-empty line as title if no markdown heading found
                    return line[:100]  # Limit title length
            
            return "Untitled Document"
        except Exception:
            return "Untitled Document"
    
    def _extract_structure_from_content(self, content: str) -> List[Dict[str, Any]]:
        """Extract document structure (sections, headings) from content."""
        structure = []
        try:
            lines = content.split('\n')
            
            for idx, line in enumerate(lines):
                line_stripped = line.strip()
                if line_stripped.startswith('#'):
                    # It's a markdown heading
                    match = re.match(r'^(#+)\s+(.+)$', line_stripped)
                    if match:
                        level = len(match.group(1))
                        title = match.group(2).strip()
                        
                        structure.append({
                            "type": "heading",
                            "level": level,
                            "title": title,
                            "line": idx
                        })
        
        except Exception as e:
            logger.warning(f"Failed to extract structure: {str(e)}")
        
        return structure


def save_uploaded_file(file_content: bytes, filename: str) -> str:
    """
    Save uploaded file to temporary location.
    
    Args:
        file_content: File content as bytes
        filename: Original filename
    
    Returns:
        Path to saved file
    """
    try:
        # Create temp directory if it doesn't exist
        temp_dir = tempfile.gettempdir()
        
        # Create a unique filename
        file_path = os.path.join(temp_dir, f"upload_{filename}")
        
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        return file_path
        
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {str(e)}")
        raise DocumentProcessingError(
            f"Failed to save uploaded file: {str(e)}"
        )

