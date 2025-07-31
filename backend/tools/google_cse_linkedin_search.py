import requests
import json
import re
from urllib.parse import quote
from typing import Dict, List, Optional
import time
import os
from dotenv import load_dotenv

# Import for LLM parsing
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_groq import ChatGroq
from schema import JobSchema
from manual_parser import LinkedInJobManualParser

class GoogleCSELinkedInSearcher:
    def __init__(self, api_key: str, search_engine_id: str):
        """
        Initializes Google CSE LinkedIn Searcher
        
        Args:
            api_key (str): Google API key
            search_engine_id (str): Custom Search Engine ID
        """
        self.api_key = api_key
        self.search_engine_id = search_engine_id
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        
        # Initialize manual parser
        self.manual_parser = LinkedInJobManualParser()
                
        try:
            load_dotenv()
            self.llm_model = ChatGroq(
                model="llama-3.3-70b-versatile",
                temperature=0,
            )
            self._setup_llm_extraction_chain()
            self.llm_available = True
        except Exception as e:
            print(f"Warning: LLM setup failed: {e}")
            self.llm_available = False
    
    def _setup_llm_extraction_chain(self):
        """Setup LLM extraction chain for job parsing"""
        try:
            extraction_functions = [convert_to_openai_function(JobSchema)]
            extraction_model = self.llm_model.bind(
                functions=extraction_functions, 
                function_call={"name": "JobSchema"}
            )
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a structured data extraction assistant specialized in parsing LinkedIn job postings. 

CRITICAL INSTRUCTIONS:
1. Extract ONLY information explicitly present in the provided content
2. DO NOT guess, infer, or make up any information
3. For missing STRING fields, use the string "None" (never null, never empty string)
4. For missing ARRAY/LIST fields, use an empty array [] (never string "None" or null)
5. Be thorough in extracting all available details about job requirements, skills, company info, etc.
6. Parse salary information carefully, separating min/max if range is provided
7. Extract all mentioned technologies, programming languages, and skills into appropriate lists
8. Identify work arrangement (Remote/Hybrid/On-site) from location or description
9. Parse seniority level from job title or description (Entry/Mid/Senior/Lead/Director)

FIELD TYPE RULES:
- String fields (title, location, etc.): Use "None" if missing
- Array fields (skills, technologies, requirements, etc.): Use [] if missing, never "None"
- Always return arrays for: soft_skills, education_requirements, benefits, certifications_required, languages_required, technologies, responsibilities, preferred_skills, experience_requirements

EXAMPLE CORRECT FORMAT:
- required_skills: ["Python", "Django"] (if skills found) or [] (if no skills found)
- technologies: ["React", "Node.js"] (if found) or [] (if not found)  
- responsibilities: ["Develop APIs", "Code review"] (if found) or [] (if not found)

Remember: Arrays must always be arrays [], never string "None"."""),
                ("human", "Title: {title}\nURL: {url}\nSnippet: {snippet}")
            ])
            
            self.extraction_chain = prompt | extraction_model | JsonOutputFunctionsParser()
        except Exception as e:
            print(f"Error setting up LLM extraction chain: {e}")
            self.llm_available = False
    
    def search_jobs(self, 
                    keyword: str,
                    location: str = "",
                    job_type: str = "",
                    experience_level: str = "",
                    company: str = "",
                    industry: str = "",
                    date_range: str = "m1",
                    num_results: int = 10,
                    parsing_method: str = "llm",
                    salary_range: str = "",
                    work_arrangement: str = "",
                    job_function: str = "",
                    include_similar: bool = True,
                    exact_match_company: bool = False) -> Dict:
        """
        Unified search method for LinkedIn jobs with comprehensive filtering capabilities.
        
        This method combines both basic and advanced search functionality into a single
        comprehensive search interface.
        
        Args:
            keyword (str): Main search keyword (job title, skills, technology, company name)
            location (str): Work location (city, state, country, or 'remote')
            job_type (str): Employment type (full-time, part-time, contract, internship, etc.)
            experience_level (str): Experience level (entry, junior, mid, senior, lead, director, etc.)
            company (str): Specific company name to search within
            industry (str): Industry sector (technology, healthcare, finance, etc.)
            date_range (str): Job posting recency (d1, w1, m1, m2, m3, m6)
            num_results (int): Number of job results to return (1-50)
            parsing_method (str): Data extraction method ('llm' or 'manual')
            salary_range (str): Salary range filter (e.g., '$100k-150k')
            work_arrangement (str): Work arrangement (remote, hybrid, on-site, flexible)
            job_function (str): Job function category (engineering, marketing, sales, design)
            include_similar (bool): Include similar/related job titles
            exact_match_company (bool): Require exact company name match
            
        Returns:
            Dict: Comprehensive search result with job information and metadata
        """
        try:
            # Validate and adjust parameters
            if parsing_method == "llm" and not self.llm_available:
                print("Warning: LLM parsing requested but not available. Using manual parsing.")
                parsing_method = "manual"
            
            # Validate date range
            valid_date_ranges = ['d1', 'w1', 'm1', 'm2', 'm3', 'm6', 'y1']
            if date_range not in valid_date_ranges:
                date_range = 'm1'
            
            # Validate num_results
            num_results = max(1, min(num_results, 50))
            
            # Build comprehensive query string
            query_parts = [keyword]
            
            # Add filters to query if they're specified
            filters_added = []
            
            if location.strip():
                query_parts.append(location.strip())
                filters_added.append(f"location: {location}")
            
            if job_type.strip():
                query_parts.append(job_type.strip())
                filters_added.append(f"job_type: {job_type}")
                
            if experience_level.strip():
                query_parts.append(experience_level.strip())
                filters_added.append(f"experience: {experience_level}")
            
            if work_arrangement.strip():
                query_parts.append(work_arrangement.strip())
                filters_added.append(f"work_arrangement: {work_arrangement}")
            
            if job_function.strip():
                query_parts.append(job_function.strip())
                filters_added.append(f"function: {job_function}")
            
            if industry.strip():
                query_parts.append(industry.strip())
                filters_added.append(f"industry: {industry}")
            
            # Handle company search with exact matching
            if company.strip():
                if exact_match_company:
                    query_parts.append(f'\"{company.strip()}\"')
                    filters_added.append(f"exact_company: {company}")
                else:
                    query_parts.append(company.strip())
                    filters_added.append(f"company: {company}")
            
            # Add salary-related terms if specified
            if salary_range.strip():
                query_parts.append("salary")
                filters_added.append(f"salary_filter: {salary_range}")
            
            # Create final query with site restriction
            query = f"site:linkedin.com/jobs {' '.join(query_parts)}"
            
            # Collect all jobs from multiple API calls
            all_jobs = []
            start_index = 1
            
            # Google CSE allows max 100 results total, 10 per request
            while len(all_jobs) < num_results and start_index <= 91:  # 91 to ensure not to exceed 100
                batch_size = min(10, num_results - len(all_jobs))
                
                # Parameters for Google CSE API
                params = {
                    'key': self.api_key,
                    'cx': self.search_engine_id,
                    'q': query,
                    'num': batch_size,
                    'start': start_index,
                    'dateRestrict': date_range,
                    'safe': 'medium',
                    'fields': 'items(title,link,snippet,displayLink)'
                }
                
                # Call Google CSE API
                response = requests.get(self.base_url, params=params)
                response.raise_for_status()
                
                search_data = response.json()
                
                # Parse current batch result based on chosen method
                if parsing_method == "llm":
                    batch_jobs = self._parse_search_results_llm(search_data)
                else:
                    batch_jobs = self.manual_parser.parse_search_results(search_data)
                
                if not batch_jobs:  # No more results available
                    break
                    
                all_jobs.extend(batch_jobs)
                start_index += 10
                
                # Rate limiting to avoid hitting API limits
                time.sleep(0.1)
            
            # Trim to exact number requested
            final_jobs = all_jobs[:num_results]
            
            # Build comprehensive result metadata
            result = {
                "success": True,
                "query": query,
                "total_found": len(final_jobs),
                "jobs": final_jobs,
                "parsing_method": parsing_method,
                "source": "google_cse_api",
                "search_metadata": {
                    "filters_applied": filters_added,
                    "date_range": date_range,
                    "include_similar": include_similar,
                    "exact_company_match": exact_match_company,
                    "requested_results": num_results,
                    "actual_results": len(final_jobs)
                }
            }
            
            # Add detailed filter information for better transparency
            result["applied_filters"] = {
                "keyword": keyword,
                "location": location if location.strip() else "all locations",
                "job_type": job_type if job_type.strip() else "all types",
                "experience_level": experience_level if experience_level.strip() else "all levels",
                "company": company if company.strip() else "all companies",
                "industry": industry if industry.strip() else "all industries",
                "date_range": date_range,
                "work_arrangement": work_arrangement if work_arrangement.strip() else "all arrangements",
                "job_function": job_function if job_function.strip() else "all functions",
                "salary_filter": "applied" if salary_range.strip() else "not applied",
                "exact_company_match": exact_match_company,
                "include_similar_jobs": include_similar
            }
            
            # Add salary filter note if applied
            if salary_range.strip():
                result["salary_filter_note"] = f"Searched with salary consideration: {salary_range}"
            
            return result
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"API request failed: {str(e)}",
                "jobs": [],
                "query": f"site:linkedin.com/jobs {keyword}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "jobs": [],
                "query": f"site:linkedin.com/jobs {keyword}"
            }
    
    def _parse_search_results_llm(self, search_data: Dict) -> List[Dict]:
        """
        Parses results from Google CSE API using LLM
        
        Args:
            search_data (Dict): Data returned from the API
            
        Returns:
            List[Dict]: List of parsed jobs
        """
        jobs = []
        
        if 'items' not in search_data:
            return jobs
        
        for item in search_data['items']:
            if 'linkedin.com/jobs' in item.get('link', ''):
                try:
                    # Prepare input for LLM
                    title = item.get('title', '')
                    url = item.get('link', '')
                    snippet = item.get('snippet', '')
                    
                    # Use LLM to extract job information
                    job_info = self.extraction_chain.invoke({
                        "title": title,
                        "url": url,
                        "snippet": snippet
                    })
                    
                    # Extract job ID from URL
                    job_id_match = re.search(r'/jobs/view/(\d+)', url)
                    job_id = job_id_match.group(1) if job_id_match else None
                    
                    # Add additional fields
                    job_info["job_id"] = job_id
                    job_info["source"] = "linkedin"
                    
                    jobs.append(job_info)
                    
                except Exception as e:
                    print(f"Error parsing job with LLM: {e}")
                    # Fallback to manual parsing for this item
                    manual_job = self.manual_parser.extract_job_info(item)
                    if manual_job:
                        jobs.append(manual_job)
        
        return jobs


def search_linkedin_jobs_google(api_key: str, 
                              search_engine_id: str,
                              keyword: str, 
                              location: str = "", 
                              job_type: str = "",
                              experience_level: str = "",
                              num_results: int = 10,
                              parsing_method: str = "llm",
                              **kwargs) -> Dict:
    """
    Utility function to search LinkedIn jobs using Google CSE API
    
    Args:
        api_key (str): Google API key
        search_engine_id (str): Custom Search Engine ID
        keyword (str): Search keyword
        location (str): Work location
        job_type (str): Job type
        experience_level (str): Experience level
        num_results (int): Number of results
        parsing_method (str): "manual" for regex parsing or "llm" for LLM parsing
        **kwargs: Additional parameters for advanced search
        
    Returns:
        Dict: Search result
    """
    searcher = GoogleCSELinkedInSearcher(api_key, search_engine_id)
    return searcher.search_jobs(
        keyword=keyword,
        location=location,
        job_type=job_type,
        experience_level=experience_level,
        num_results=num_results,
        parsing_method=parsing_method,
        **kwargs
    )