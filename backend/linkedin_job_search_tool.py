"""
LinkedIn Job Search Tool for the Job Search Agent.

This module provides the LinkedIn job search functionality
as a standalone tool that can be used by the agent.
"""

from langchain.tools import tool
from typing import Dict
import os
from dotenv import load_dotenv

# Import GoogleCSELinkedInSearcher and schema
from google_cse_linkedin_search import GoogleCSELinkedInSearcher
from schema import LinkedInJobSearchInput
from config import MODEL_NAME


@tool(args_schema=LinkedInJobSearchInput)
def search_linkedin_jobs(
    keyword: str,
    location: str = "",
    job_type: str = "",
    experience_level: str = "",
    company: str = "",
    industry: str = "",
    date_range: str = "m6",
    num_results: int = 5,
    parsing_method: str = "llm",
    salary_range: str = "",
    work_arrangement: str = "",
    job_function: str = "",
    include_similar: bool = True,
    exact_match_company: bool = False
) -> Dict:
    """
    Comprehensive LinkedIn job search with advanced filtering capabilities.
    
    Searches for jobs on LinkedIn using Google Custom Search Engine with support for:
    - Basic filters: location, job type, experience level
    - Advanced filters: company, industry, salary range, work arrangement
    - Time filters: date range for job posting recency
    - Search behavior: similar jobs, exact matching
    
    Returns structured job information including title, company, location, salary, 
    requirements, skills, and more extracted using AI parsing.
    
    IMPORTANT: Leave any filter empty if you don't want to apply it. The AI will not
    make up or guess values for empty parameters.
    
    Example use cases:
    - Basic search: keyword="Python Developer", location="San Francisco, CA"
    - Company-specific: keyword="Software Engineer", company="Google"
    - Remote jobs: keyword="Data Scientist", work_arrangement="remote"
    - Entry-level: keyword="Junior Developer", experience_level="entry"
    - Recent postings: keyword="DevOps Engineer", date_range="w1"
    
    Args:
        keyword: Main search keyword (job title, skills, technology, or company name)
        location: Work location (city, state, country, or 'remote'). Leave empty for all locations
        job_type: Employment type (full-time, part-time, contract, internship, temporary, freelance)
        experience_level: Experience level (entry, junior, mid, senior, lead, principal, director, executive)
        company: Specific company name to search within (e.g., 'Google', 'Microsoft')
        industry: Industry sector (e.g., 'technology', 'healthcare', 'finance')
        date_range: Job posting recency (d1, w1, m1, m2, m3, m6 for day/week/month ranges)
        num_results: Number of job results to return (1-50)
        parsing_method: Data extraction method ('llm' for AI-powered, 'manual' for regex-based)
        salary_range: Salary range filter (e.g., '$100k-150k', '80000-120000')
        work_arrangement: Work arrangement (remote, hybrid, on-site, flexible)
        job_function: Job function category (e.g., 'engineering', 'marketing', 'sales', 'design')
        include_similar: Include similar/related job titles in search results
        exact_match_company: Require exact company name match

    
    Returns:
        Dict: Search results with job listings and metadata
    """
    
    # Load environment variables
    load_dotenv()
    
    # Get API credentials from environment
    api_key = os.getenv('CUSTOM_SEARCH_API_KEY')
    search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
    
    if not api_key or not search_engine_id:
        return {
            "success": False,
            "error": "Missing Google API credentials. Please set CUSTOM_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID environment variables.",
            "jobs": []
        }
    
    # Create searcher instance
    searcher = GoogleCSELinkedInSearcher(api_key, search_engine_id)
    
    # Use the unified search_jobs method with all parameters
    result = searcher.search_jobs(
        keyword=keyword,
        location=location,
        job_type=job_type,
        experience_level=experience_level,
        company=company,
        industry=industry,
        date_range=date_range,
        num_results=num_results,
        parsing_method=parsing_method,
        salary_range=salary_range,
        work_arrangement=work_arrangement,
        job_function=job_function,
        include_similar=include_similar,
        exact_match_company=exact_match_company
    )
    
    return result