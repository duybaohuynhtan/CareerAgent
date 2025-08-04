"""
CV Parser Tool for the Job Search Agent.

This module provides tools to parse CV/resume from text or PDF files
and extract structured information using LLM.
"""

from langchain.tools import tool
from typing import Dict, Union
import os
from cv_parser import CVParser, read_pdf
from schema import CVParseInput
from config import MODEL_NAME


@tool(args_schema=CVParseInput)
def parse_cv_content(
    content: str,
    content_type: str = "text"
) -> Dict:
    """
    Parse CV/resume from text content or PDF file and extract structured information.
    
    This tool can analyze resumes and extract comprehensive information including:
    - Personal information and contact details
    - Work experience with detailed job history
    - Education background
    - Technical and soft skills
    - Certifications and achievements
    - Projects and portfolio information
    - Career preferences and availability
    
    Args:
        content: CV content as text OR file path to PDF file
        content_type: 'text' for direct text input or 'pdf' for PDF file path

    
    Returns:
        Dict: Structured CV information according to ResumeSchema with parsing status
    """
    try:
        # Initialize CV parser
        parser = CVParser()
        
        if content_type.lower() == "pdf":
            # Parse from PDF file
            if not os.path.exists(content):
                return {
                    "success": False,
                    "error": f"PDF file not found: {content}",
                    "data": None
                }
            
            result = parser.parse_resume_from_pdf(content)
        
        elif content_type.lower() == "text":
            # Parse from text content
            if not content or content.strip() == "":
                return {
                    "success": False,
                    "error": "CV text content is empty",
                    "data": None
                }
            
            result = parser.parse_resume_from_text(content)
        
        else:
            return {
                "success": False,
                "error": f"Invalid content_type: {content_type}. Must be 'text' or 'pdf'",
                "data": None
            }
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error parsing CV: {str(e)}",
            "data": None
        }