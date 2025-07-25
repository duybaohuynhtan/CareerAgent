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

class JobSchema(BaseModel):
    """
    A schema for parsing job information from LinkedIn search results.
    """
    title: str = Field(description="The job title")
    company: str = Field(description="The company name offering the job")
    location: str = Field(description="The job location (city, state, country or remote/hybrid)")
    job_type: str = Field(description="The type of employment (full-time, part-time, contract, etc.)")
    salary: Optional[str] = Field(description="Salary information if mentioned")
    posted_date: Optional[str] = Field(description="When the job was posted")
    experience_level: Optional[str] = Field(description="Required experience level (entry, mid, senior, etc.)")
    description: str = Field(description="Job description or summary")
    url: str = Field(description="URL to the job posting")

