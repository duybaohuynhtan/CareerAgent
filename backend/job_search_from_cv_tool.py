"""
Job Search from CV Tool for the Job Search Agent.

This module provides a tool that automatically analyzes a CV/resume
and searches for relevant job opportunities based on the extracted information.
"""

from langchain.tools import tool
from typing import Dict, List
import os
from dotenv import load_dotenv

# Import required modules
from cv_parser import CVParser
from google_cse_linkedin_search import GoogleCSELinkedInSearcher
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from schema import JobSearchFromCVInput
from config import MODEL_NAME


@tool(args_schema=JobSearchFromCVInput)
def search_jobs_from_cv(
    cv_content: str,
    cv_content_type: str = "text",
    location: str = "",
    job_type: str = "",
    work_arrangement: str = "",
    num_results: int = 10,
    include_entry_level: bool = False
) -> Dict:
    """
    Automatically analyze a CV/resume and search for relevant job opportunities.
    
    This tool performs the following steps:
    1. Parses the CV to extract structured information (experience, skills, education, etc.)
    2. Analyzes the candidate's profile to determine appropriate job search parameters
    3. Generates targeted search queries based on the candidate's background
    4. Searches for relevant job opportunities on LinkedIn
    5. Returns both the CV analysis and matching job opportunities
    
    The tool intelligently determines:
    - Relevant job titles and keywords based on experience
    - Appropriate experience level based on work history
    - Technical skills and technologies to include in search
    - Industries and companies that match the candidate's background
    
    Args:
        cv_content: CV content as text OR file path to PDF file
        cv_content_type: 'text' for direct text input or 'pdf' for PDF file path  
        location: Preferred job location (overrides CV location if provided)
        job_type: Preferred employment type (overrides CV preference if provided)
        work_arrangement: Preferred work arrangement (overrides CV preference if provided)
        num_results: Number of job results to return
        include_entry_level: Include entry-level positions even for experienced candidates

    
    Returns:
        Dict: CV analysis results and matching job opportunities
    """
    
    try:
        # Load environment variables
        load_dotenv()
        
        # Step 1: Parse the CV
        cv_parser = CVParser()
        
        if cv_content_type.lower() == "pdf":
            if not os.path.exists(cv_content):
                return {
                    "success": False,
                    "error": f"PDF file not found: {cv_content}",
                    "cv_analysis": None,
                    "jobs": []
                }
            cv_result = cv_parser.parse_resume_from_pdf(cv_content)
        elif cv_content_type.lower() == "text":
            if not cv_content or cv_content.strip() == "":
                return {
                    "success": False,
                    "error": "CV text content is empty",
                    "cv_analysis": None,
                    "jobs": []
                }
            cv_result = cv_parser.parse_resume_from_text(cv_content)
        else:
            return {
                "success": False,
                "error": f"Invalid cv_content_type: {cv_content_type}. Must be 'text' or 'pdf'",
                "cv_analysis": None,
                "jobs": []
            }
        
        if not cv_result.get("success", False):
            return {
                "success": False,
                "error": f"Failed to parse CV: {cv_result.get('error', 'Unknown error')}",
                "cv_analysis": cv_result,
                "jobs": []
            }
        
        cv_data = cv_result.get("data", {})
        
        # Step 2: Generate job search parameters from CV data
        search_params = _generate_search_parameters(cv_data, location, job_type, work_arrangement, include_entry_level)
        
        if not search_params.get("success", False):
            return {
                "success": False,
                "error": f"Failed to generate search parameters: {search_params.get('error', 'Unknown error')}",
                "cv_analysis": cv_result,
                "jobs": []
            }
        
        # Step 3: Perform job search with generated parameters
        jobs_result = _search_jobs_with_params(search_params["parameters"], num_results)
        
        # Step 4: Return combined results
        return {
            "success": True,
            "cv_analysis": cv_result,
            "search_strategy": search_params["parameters"],
            "reasoning": search_params.get("reasoning", ""),
            "jobs_found": len(jobs_result.get("jobs", [])),
            "jobs": jobs_result.get("jobs", []),
            "job_search_success": jobs_result.get("success", False),
            "job_search_error": jobs_result.get("error", None)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error in CV-based job search: {str(e)}",
            "cv_analysis": None,
            "jobs": []
        }


def _generate_search_parameters(cv_data: Dict, user_location: str = "", user_job_type: str = "", user_work_arrangement: str = "", include_entry_level: bool = False) -> Dict:
    """
    Generate job search parameters based on parsed CV data using LLM analysis.
    """
    try:
        # Initialize LLM
        llm = ChatGroq(model=MODEL_NAME, temperature=0)
        
        # Create prompt for generating search parameters
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert career advisor and job search strategist. 
            
Your task is to analyze a parsed CV/resume and generate optimal LinkedIn job search parameters.

CRITICAL INSTRUCTIONS:
1. Base your analysis ONLY on the information provided in the CV data
2. Generate realistic and relevant search parameters
3. Consider the candidate's experience level, skills, and career progression
4. Create multiple targeted search strategies if the candidate has diverse experience
5. Prioritize recent experience and strongest skills
6. DO NOT make assumptions about preferences not mentioned in the CV

ANALYSIS GUIDELINES:
- Extract the most relevant job titles from recent experience
- Identify key technical skills and technologies that should be in job requirements
- Determine appropriate experience level based on work history
- Consider industry sectors from past experience
- Use actual location from CV unless user override is provided
- Consider work arrangement preferences if mentioned

OUTPUT FORMAT:
Return a JSON object with the following structure:
{
    "primary_search": {
        "keyword": "primary job title or skill",
        "location": "location to search",
        "experience_level": "entry/mid/senior/lead",
        "industry": "relevant industry if applicable"
    },
    "secondary_searches": [
        {
            "keyword": "alternative job title or skill combination",
            "focus": "reason for this search variant"
        }
    ],
    "reasoning": "explanation of the search strategy",
    "candidate_summary": "brief summary of candidate profile"
}"""),
            ("human", """CV Data to analyze:
{cv_data}

User preferences (override CV if provided):
- Location preference: {user_location}
- Job type preference: {user_job_type}  
- Work arrangement preference: {user_work_arrangement}
- Include entry level: {include_entry_level}

Generate optimal job search parameters for this candidate.""")
        ])
        
        # Generate search strategy
        response = llm.invoke(prompt.format_messages(
            cv_data=str(cv_data),
            user_location=user_location or "from CV",
            user_job_type=user_job_type or "from CV",
            user_work_arrangement=user_work_arrangement or "from CV",
            include_entry_level=include_entry_level
        ))
        
        # Parse LLM response (assuming it returns structured JSON)
        import json
        try:
            content = response.content if isinstance(response.content, str) else str(response.content)
            strategy = json.loads(content)
        except:
            # Fallback to basic parameter extraction if JSON parsing fails
            strategy = _extract_basic_search_params(cv_data, user_location, user_job_type, user_work_arrangement, include_entry_level)
        
        # Convert strategy to actual search parameters
        search_params = _convert_strategy_to_params(strategy, cv_data, user_location, user_job_type, user_work_arrangement)
        
        return {
            "success": True,
            "parameters": search_params,
            "reasoning": strategy.get("reasoning", "Generated search parameters based on CV analysis"),
            "strategy": strategy
        }
        
    except Exception as e:
        # Fallback to basic parameter extraction
        basic_params = _extract_basic_search_params(cv_data, user_location, user_job_type, user_work_arrangement, include_entry_level)
        return {
            "success": True,
            "parameters": basic_params,
            "reasoning": f"Used basic parameter extraction due to LLM error: {str(e)}",
            "strategy": "fallback"
        }


def _extract_basic_search_params(cv_data: Dict, user_location: str = "", user_job_type: str = "", user_work_arrangement: str = "", include_entry_level: bool = False) -> Dict:
    """
    Extract basic search parameters from CV data without LLM analysis (fallback method).
    """
    params = {}
    
    # Extract keyword from most recent job title or professional title
    keyword = ""
    if cv_data.get("professional_title") and cv_data["professional_title"] != "None":
        keyword = cv_data["professional_title"]
    elif cv_data.get("experiences") and len(cv_data["experiences"]) > 0:
        latest_job = cv_data["experiences"][0]
        if latest_job.get("job_title") and latest_job["job_title"] != "None":
            keyword = latest_job["job_title"]
    
    if not keyword:
        # Fallback to technical skills
        if cv_data.get("technical_skills") and len(cv_data["technical_skills"]) > 0:
            keyword = cv_data["technical_skills"][0].get("name", "software engineer")
        else:
            keyword = "software engineer"  # Default fallback
    
    params["keyword"] = keyword
    
    # Location
    if user_location:
        params["location"] = user_location
    elif cv_data.get("contact_info", {}).get("city") != "None":
        city = cv_data.get("contact_info", {}).get("city", "")
        state = cv_data.get("contact_info", {}).get("state", "")
        if city and state:
            params["location"] = f"{city}, {state}"
        elif city:
            params["location"] = city
        else:
            params["location"] = ""
    else:
        params["location"] = ""
    
    # Job type
    params["job_type"] = user_job_type or ""
    
    # Work arrangement  
    if user_work_arrangement:
        params["work_arrangement"] = user_work_arrangement
    elif cv_data.get("preferred_work_type") and cv_data["preferred_work_type"] != "None":
        params["work_arrangement"] = cv_data["preferred_work_type"].lower()
    else:
        params["work_arrangement"] = ""
    
    # Experience level based on years of experience
    total_exp = cv_data.get("total_years_experience", "None")
    if total_exp != "None" and total_exp:
        try:
            years = int(''.join(filter(str.isdigit, total_exp)))
            if include_entry_level or years <= 2:
                params["experience_level"] = "entry"
            elif years <= 5:
                params["experience_level"] = "mid"
            elif years <= 10:
                params["experience_level"] = "senior"
            else:
                params["experience_level"] = "lead"
        except:
            params["experience_level"] = ""
    else:
        params["experience_level"] = ""
    
    return params


def _convert_strategy_to_params(strategy: Dict, cv_data: Dict, user_location: str = "", user_job_type: str = "", user_work_arrangement: str = "") -> Dict:
    """
    Convert LLM-generated strategy to actual search parameters.
    """
    params = {}
    
    primary = strategy.get("primary_search", {})
    
    params["keyword"] = primary.get("keyword", "software engineer")
    params["location"] = user_location or primary.get("location", "")
    params["job_type"] = user_job_type or ""
    params["experience_level"] = primary.get("experience_level", "")
    params["work_arrangement"] = user_work_arrangement or ""
    params["industry"] = primary.get("industry", "")
    
    return params


def _search_jobs_with_params(search_params: Dict, num_results: int) -> Dict:
    """
    Perform job search with the generated parameters.
    """
    try:
        # Get API credentials
        api_key = os.getenv('CUSTOM_SEARCH_API_KEY')
        search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
        
        if not api_key or not search_engine_id:
            return {
                "success": False,
                "error": "Missing Google API credentials",
                "jobs": []
            }
        
        # Create searcher and perform search
        searcher = GoogleCSELinkedInSearcher(api_key, search_engine_id)
        
        result = searcher.search_jobs(
            keyword=search_params.get("keyword", ""),
            location=search_params.get("location", ""),
            job_type=search_params.get("job_type", ""),
            experience_level=search_params.get("experience_level", ""),
            industry=search_params.get("industry", ""),
            work_arrangement=search_params.get("work_arrangement", ""),
            num_results=num_results,
            parsing_method="llm"
        )
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error searching jobs: {str(e)}",
            "jobs": []
        }