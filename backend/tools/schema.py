from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any, Union
from langchain.tools import tool
from PyPDF2 import PdfReader
from dotenv import load_dotenv

def read_pdf(path):
    reader = PdfReader(path)
    text = []
    for page in reader.pages:
        text.append(page.extract_text())
    return "\n".join(text)

class ContactInfo(BaseModel):
    """Contact information structure"""
    email: str = Field(default="None", description="Email address")
    phone: str = Field(default="None", description="Phone number")
    address: str = Field(default="None", description="Full address")
    city: str = Field(default="None", description="City")
    state: str = Field(default="None", description="State/Province")
    country: str = Field(default="None", description="Country")
    postal_code: str = Field(default="None", description="Postal/ZIP code")
    linkedin: str = Field(default="None", description="LinkedIn profile URL")
    github: str = Field(default="None", description="GitHub profile URL")
    portfolio: str = Field(default="None", description="Portfolio website URL")
    other_profiles: List[str] = Field(default_factory=list, description="Other social/professional profiles")

class Experience(BaseModel):
    """Work experience structure"""
    job_title: str = Field(default="None", description="Job title/position")
    company: str = Field(default="None", description="Company name")
    location: str = Field(default="None", description="Work location")
    start_date: str = Field(default="None", description="Start date")
    end_date: str = Field(default="None", description="End date or 'Present'")
    duration: str = Field(default="None", description="Duration of employment")
    employment_type: str = Field(default="None", description="Full-time, Part-time, Contract, Internship, etc.")
    description: str = Field(default="None", description="Job description and responsibilities")
    achievements: List[str] = Field(default_factory=list, description="Key achievements and accomplishments")
    technologies_used: List[str] = Field(default_factory=list, description="Technologies, tools, frameworks used")
    industry: str = Field(default="None", description="Industry sector")

class Education(BaseModel):
    """Education structure"""
    institution: str = Field(default="None", description="School/University name")
    degree: str = Field(default="None", description="Degree type (Bachelor's, Master's, PhD, etc.)")
    major: str = Field(default="None", description="Major/Field of study")
    minor: str = Field(default="None", description="Minor field of study")
    gpa: str = Field(default="None", description="GPA or grade")
    start_date: str = Field(default="None", description="Start date")
    end_date: str = Field(default="None", description="Graduation date or expected")
    location: str = Field(default="None", description="Institution location")
    honors: List[str] = Field(default_factory=list, description="Academic honors, dean's list, etc.")
    relevant_coursework: List[str] = Field(default_factory=list, description="Relevant courses")
    thesis_project: str = Field(default="None", description="Thesis or capstone project title")

class Skill(BaseModel):
    """Skill with proficiency level"""
    name: str = Field(description="Skill name")
    category: str = Field(default="None", description="Skill category (Technical, Soft, Language, etc.)")
    proficiency_level: str = Field(default="None", description="Proficiency level (Beginner, Intermediate, Advanced, Expert)")
    years_of_experience: str = Field(default="None", description="Years of experience with this skill")

class Certification(BaseModel):
    """Certification structure"""
    name: str = Field(description="Certification name")
    issuing_organization: str = Field(default="None", description="Organization that issued the certification")
    issue_date: str = Field(default="None", description="Date when certification was issued")
    expiration_date: str = Field(default="None", description="Expiration date if applicable")
    credential_id: str = Field(default="None", description="Credential ID or badge number")
    verification_url: str = Field(default="None", description="URL to verify certification")

class Project(BaseModel):
    """Project structure"""
    name: str = Field(description="Project name")
    description: str = Field(default="None", description="Project description")
    role: str = Field(default="None", description="Your role in the project")
    start_date: str = Field(default="None", description="Project start date")
    end_date: str = Field(default="None", description="Project end date or 'Ongoing'")
    technologies: List[str] = Field(default_factory=list, description="Technologies used")
    url: str = Field(default="None", description="Project URL or demo link")
    repository: str = Field(default="None", description="Code repository link")
    achievements: List[str] = Field(default_factory=list, description="Key achievements and results")

class Language(BaseModel):
    """Language proficiency structure"""
    language: str = Field(description="Language name")
    proficiency: str = Field(default="None", description="Proficiency level (Native, Fluent, Intermediate, Basic)")
    certification: str = Field(default="None", description="Language certification if any")

class ResumeSchema(BaseModel):
    """
    Comprehensive schema for parsing resume information.
    """
    # Personal Information
    full_name: str = Field(default="None", description="Full name of the candidate")
    professional_title: str = Field(default="None", description="Current professional title or desired position")
    
    # Contact Information
    contact_info: ContactInfo = Field(default_factory=ContactInfo, description="Contact information")
    
    # Professional Summary
    summary: str = Field(default="None", description="Professional summary or objective statement")
    
    # Work Experience
    experiences: List[Experience] = Field(default_factory=list, description="Work experience history")
    
    # Education
    education: List[Education] = Field(default_factory=list, description="Educational background")
    
    # Skills
    technical_skills: List[Skill] = Field(default_factory=list, description="Technical skills with proficiency")
    soft_skills: List[str] = Field(default_factory=list, description="Soft skills and interpersonal abilities")
    
    # Languages
    languages: List[Language] = Field(default_factory=list, description="Language proficiencies")
    
    # Certifications
    certifications: List[Certification] = Field(default_factory=list, description="Professional certifications")
    
    # Projects
    projects: List[Project] = Field(default_factory=list, description="Notable projects")
    
    # Additional Information
    awards: List[str] = Field(default_factory=list, description="Awards and recognitions")
    publications: List[str] = Field(default_factory=list, description="Publications and papers")
    volunteer_experience: List[str] = Field(default_factory=list, description="Volunteer work and community service")
    interests: List[str] = Field(default_factory=list, description="Personal interests and hobbies")
    
    # Career Information
    total_years_experience: str = Field(default="None", description="Total years of professional experience")
    current_salary: str = Field(default="None", description="Current salary if mentioned")
    expected_salary: str = Field(default="None", description="Expected salary if mentioned")
    availability: str = Field(default="None", description="Availability (Immediately, 2 weeks notice, etc.)")
    preferred_work_type: str = Field(default="None", description="Preferred work arrangement (Remote, Hybrid, On-site)")
    
    @validator('*', pre=True)
    def empty_str_to_none(cls, v):
        if v == '' or v is None:
            return "None"
        return v

class JobRequirement(BaseModel):
    """Job requirement structure"""
    category: str = Field(default="None", description="Requirement category (Education, Experience, Skills, etc.)")
    requirement: str = Field(description="Specific requirement")
    priority: str = Field(default="None", description="Priority level (Required, Preferred, Nice-to-have)")

class CompanyInfo(BaseModel):
    """Company information structure"""
    name: str = Field(default="None", description="Company name")
    industry: str = Field(default="None", description="Industry sector")
    size: str = Field(default="None", description="Company size (employees count or category)")
    description: str = Field(default="None", description="Company description")
    website: str = Field(default="None", description="Company website")
    headquarters: str = Field(default="None", description="Company headquarters location")

class JobSchema(BaseModel):
    """
    Comprehensive schema for parsing job information from LinkedIn and other job platforms.
    """
    # Basic Job Information
    job_id: str = Field(default="None", description="Unique job identifier")
    title: str = Field(default="None", description="Job title")
    seniority_level: str = Field(default="None", description="Seniority level (Entry, Mid, Senior, Lead, Director, etc.)")
    
    # Company Information
    company_info: CompanyInfo = Field(default_factory=CompanyInfo, description="Company information")
    
    # Job Details
    location: str = Field(default="None", description="Job location (city, state, country)")
    work_arrangement: str = Field(default="None", description="Work arrangement (Remote, Hybrid, On-site)")
    job_type: str = Field(default="None", description="Employment type (Full-time, Part-time, Contract, Internship, etc.)")
    department: str = Field(default="None", description="Department or team")
    
    # Compensation
    salary_min: str = Field(default="None", description="Minimum salary")
    salary_max: str = Field(default="None", description="Maximum salary")
    salary_currency: str = Field(default="None", description="Salary currency")
    salary_period: str = Field(default="None", description="Salary period (yearly, monthly, hourly)")
    equity: str = Field(default="None", description="Equity/stock options information")
    benefits: List[str] = Field(default_factory=list, description="Benefits and perks")
    
    # Job Description
    description: str = Field(default="None", description="Full job description")
    responsibilities: List[str] = Field(default_factory=list, description="Key responsibilities and duties")
    
    # Requirements
    required_skills: List[str] = Field(default_factory=list, description="Required technical skills")
    preferred_skills: List[str] = Field(default_factory=list, description="Preferred technical skills")
    soft_skills: List[str] = Field(default_factory=list, description="Required soft skills")
    
    education_requirements: List[str] = Field(default_factory=list, description="Education requirements")
    experience_requirements: List[str] = Field(default_factory=list, description="Experience requirements")
    certifications_required: List[str] = Field(default_factory=list, description="Required certifications")
    
    languages_required: List[str] = Field(default_factory=list, description="Language requirements")
    
    # Technologies
    technologies: List[str] = Field(default_factory=list, description="Technologies, frameworks, tools mentioned")
    programming_languages: List[str] = Field(default_factory=list, description="Programming languages required")
    
    # Application Information
    posted_date: str = Field(default="None", description="Job posting date")
    application_deadline: str = Field(default="None", description="Application deadline")
    application_url: str = Field(default="None", description="Direct application URL")
    recruiter_contact: str = Field(default="None", description="Recruiter or HR contact information")
    
    # Additional Information
    travel_requirements: str = Field(default="None", description="Travel requirements percentage")
    security_clearance: str = Field(default="None", description="Security clearance requirements")
    visa_sponsorship: str = Field(default="None", description="Visa sponsorship availability")
    
    # Metadata
    url: str = Field(default="None", description="URL to the job posting")
    source: str = Field(default="linkedin", description="Source platform (LinkedIn, Indeed, etc.)")
    job_function: str = Field(default="None", description="Job function category")
    
    @validator('*', pre=True)
    def empty_str_to_none(cls, v):
        if v == '' or v is None:
            return "None"
        return v


class CVParser:
    """
    CV/Resume parser using LLM for structured data extraction
    """
    def __init__(self):
        try:
            load_dotenv()
            from langchain_groq import ChatGroq
            from langchain.utils.openai_functions import convert_pydantic_to_openai_function
            from langchain.prompts import ChatPromptTemplate
            from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
            
            self.llm_model = ChatGroq(
                model="llama-3.3-70b-versatile",
                temperature=0,
            )
            self._setup_resume_extraction_chain()
            self.llm_available = True
        except Exception as e:
            print(f"Warning: LLM setup failed for CV parser: {e}")
            self.llm_available = False
    
    def _setup_resume_extraction_chain(self):
        """Setup LLM extraction chain for resume parsing"""
        try:
            from langchain.utils.openai_functions import convert_pydantic_to_openai_function
            from langchain.prompts import ChatPromptTemplate
            from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
            
            extraction_functions = [convert_pydantic_to_openai_function(ResumeSchema)]
            extraction_model = self.llm_model.bind(
                functions=extraction_functions, 
                function_call={"name": "ResumeSchema"}
            )
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert resume/CV parser that extracts structured information from resumes. 

CRITICAL INSTRUCTIONS:
1. Extract ONLY information explicitly present in the resume text
2. DO NOT guess, infer, or make up any information
3. For ANY missing information, you MUST use the string "None" (never null, never empty string)
4. Be thorough and comprehensive in extracting all available details
5. Parse work experience chronologically with all details
6. Extract all skills mentioned, categorizing them appropriately
7. Identify education details including dates, degrees, institutions
8. Parse contact information carefully from headers/footers
9. Extract projects, certifications, awards, and other achievements
10. Determine experience level and skills proficiency from context
11. Parse salary expectations if mentioned
12. Identify preferred work arrangements (Remote/Hybrid/On-site)

PARSING GUIDELINES:
- For experiences: extract job titles, companies, dates, responsibilities, achievements
- For skills: categorize as technical vs soft skills, note proficiency if mentioned
- For education: get degree type, major, institution, graduation dates, GPA if present
- For projects: extract names, descriptions, technologies used, your role
- For certifications: get certification names, issuing bodies, dates, credential IDs
- For contact info: extract all contact methods, social profiles, portfolios

Remember: Use "None" string for any field where information is not explicitly available."""),
                ("human", "Resume/CV Content:\n{resume_text}")
            ])
            
            self.extraction_chain = prompt | extraction_model | JsonOutputFunctionsParser()
        except Exception as e:
            print(f"Error setting up resume extraction chain: {e}")
            self.llm_available = False
    
    def parse_resume_from_text(self, resume_text: str) -> dict:
        """
        Parse resume from text content using LLM
        
        Args:
            resume_text (str): The full text content of the resume
            
        Returns:
            dict: Parsed resume data according to ResumeSchema
        """
        if not self.llm_available:
            return {
                "success": False,
                "error": "LLM not available for resume parsing",
                "data": None
            }
        
        try:
            # Extract resume information using LLM
            resume_data = self.extraction_chain.invoke({
                "resume_text": resume_text
            })
            
            return {
                "success": True,
                "data": resume_data,
                "parsing_method": "llm",
                "source": "text_input"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error parsing resume: {str(e)}",
                "data": None
            }
    
    def parse_resume_from_pdf(self, pdf_path: str) -> dict:
        """
        Parse resume from PDF file
        
        Args:
            pdf_path (str): Path to the PDF file
            
        Returns:
            dict: Parsed resume data according to ResumeSchema
        """
        try:
            # Extract text from PDF
            resume_text = read_pdf(pdf_path)
            
            if not resume_text or resume_text.strip() == "":
                return {
                    "success": False,
                    "error": "Could not extract text from PDF or PDF is empty",
                    "data": None
                }
            
            # Parse the extracted text
            result = self.parse_resume_from_text(resume_text)
            result["source"] = "pdf_file"
            result["file_path"] = pdf_path
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error processing PDF: {str(e)}",
                "data": None
            }

def parse_resume_text(resume_text: str) -> dict:
    """
    Utility function to parse resume from text
    
    Args:
        resume_text (str): Resume text content
        
    Returns:
        dict: Parsed resume data
    """
    parser = CVParser()
    return parser.parse_resume_from_text(resume_text)

def parse_resume_pdf(pdf_path: str) -> dict:
    """
    Utility function to parse resume from PDF file
    
    Args:
        pdf_path (str): Path to PDF file
        
    Returns:
        dict: Parsed resume data
    """
    parser = CVParser()
    return parser.parse_resume_from_pdf(pdf_path)


# =============================================================================
# LinkedIn Job Search Schema
# =============================================================================

class LinkedInJobSearchInput(BaseModel):
    """
    Comprehensive input schema for LinkedIn job search with all possible filters.
    Handles both basic and advanced search scenarios in a single tool.
    """
    # Required fields
    keyword: str = Field(..., description="Main search keyword (job title, skills, technology, or company name)")
    
    # Location filters
    location: str = Field(default="", description="Work location (city, state, country, or 'remote'). Leave empty for all locations")
    
    # Job specifics  
    job_type: str = Field(default="", description="Employment type: full-time, part-time, contract, internship, temporary, freelance. Leave empty for all types")
    experience_level: str = Field(default="", description="Experience level: entry, junior, mid, senior, lead, principal, director, executive. Leave empty for all levels")
    
    # Company and industry filters
    company: str = Field(default="", description="Specific company name to search within (e.g., 'Google', 'Microsoft'). Leave empty to search all companies")
    industry: str = Field(default="", description="Industry sector (e.g., 'technology', 'healthcare', 'finance'). Leave empty for all industries")
    
    # Time and date filters
    date_range: str = Field(default="m1", description="Job posting recency: 'd1' (past day), 'w1' (past week), 'm1' (past month), 'm2' (past 2 months), 'm3' (past 3 months), 'm6' (past 6 months)")
    
    # Search parameters
    num_results: int = Field(default=10, description="Number of job results to return (1-50)", ge=1, le=50)
    parsing_method: str = Field(default="llm", description="Data extraction method: 'llm' for AI-powered parsing (recommended) or 'manual' for regex-based parsing")
    
    # Advanced filters
    salary_range: str = Field(default="", description="Salary range filter (e.g., '$100k-150k', '80000-120000'). Leave empty to ignore salary")
    work_arrangement: str = Field(default="", description="Work arrangement: remote, hybrid, on-site, flexible. Leave empty for all arrangements")
    job_function: str = Field(default="", description="Job function category (e.g., 'engineering', 'marketing', 'sales', 'design'). Leave empty for all functions")
    
    # Search behavior
    include_similar: bool = Field(default=True, description="Include similar/related job titles in search results")
    exact_match_company: bool = Field(default=False, description="Require exact company name match (useful for targeting specific companies)")
    
    @validator('date_range')
    def validate_date_range(cls, v):
        valid_ranges = ['d1', 'w1', 'm1', 'm2', 'm3', 'm6', 'y1']
        if v and v not in valid_ranges:
            return 'm1'  # Default to 1 month
        return v
    
    @validator('parsing_method')
    def validate_parsing_method(cls, v):
        if v not in ['llm', 'manual']:
            return 'llm'  # Default to LLM parsing
        return v
    
    @validator('*', pre=True)
    def empty_str_to_default(cls, v, field):
        """Ensure empty strings are handled appropriately"""
        if v == '' or v is None:
            if field.name in ['keyword']:  # Required fields should not be empty
                return v  # Let validation handle required fields
            return ""  # Optional fields can be empty
        return v

