from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from langchain.tools import tool
from PyPDF2 import PdfReader

def read_pdf(path):
    reader = PdfReader(path)
    text = []
    for page in reader.pages:
        text.append(page.extract_text())
    return "\n".join(text)

class ResumeSchema(BaseModel):
    """
    A schema for parsing resume information.
    """
    name: str = Field(description="The name of the candidate")
    email: EmailStr = Field(description="The email address of the candidate")
    phone: str = Field(description="The phone number of the candidate")
    skills: List[str] = Field(description="The skills of the candidate")
    experiences: List[Dict[str, Any]] = Field(description="The experiences of the candidate")
    education: List[Dict[str, Any]] = Field(description="The education of the candidate")

