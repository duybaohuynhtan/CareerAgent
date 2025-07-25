import requests
import json
import re
from urllib.parse import quote
from typing import Dict, List, Optional
import time
import os
from dotenv import load_dotenv

# Import for LLM parsing
from langchain.utils.openai_functions import convert_pydantic_to_openai_function
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_groq import ChatGroq
from parser import JobSchema

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
            extraction_functions = [convert_pydantic_to_openai_function(JobSchema)]
            extraction_model = self.llm_model.bind(
                functions=extraction_functions, 
                function_call={"name": "JobSchema"}
            )
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a structured data extraction assistant. Your task is to read a LinkedIn search result and extract exactly the relevant information. Only extract information explicitly present; do not guess or infer. If a field is missing, set it to \"None\" string (never null)."),
                ("human", "Title: {title}\nURL: {url}\nSnippet: {snippet}")
            ])
            
            self.extraction_chain = prompt | extraction_model | JsonOutputFunctionsParser()
        except Exception as e:
            print(f"Error setting up LLM extraction chain: {e}")
            self.llm_available = False
    
    def search_linkedin_jobs(self, 
                           keyword: str, 
                           location: str = "", 
                           job_type: str = "",
                           experience_level: str = "",
                           num_results: int = 10,
                           parsing_method: str = "manual") -> Dict:
        """
        Searches for jobs on LinkedIn using Google Custom Search Engine
        
        Args:
            keyword (str): Search keyword (location, company, skill)
            location (str): Work location
            job_type (str): Job type (full-time, part-time, contract, etc.)
            experience_level (str): Experience level (entry, mid, senior)
            num_results (int): Number of results to fetch
            parsing_method (str): "manual" for regex parsing or "llm" for LLM parsing
            
        Returns:
            Dict: Search result with job information
        """
        try:
            # Validate parsing method
            if parsing_method == "llm" and not self.llm_available:
                print("Warning: LLM parsing requested but not available. Using manual parsing.")
                parsing_method = "manual"
            
            # Build query string for LinkedIn
            query_parts = [keyword]
            
            if location:
                query_parts.append(location)
            
            if job_type:
                query_parts.append(job_type)
                
            if experience_level:
                query_parts.append(experience_level)
            
            # Create query with site restriction
            query = f"site:linkedin.com/jobs {' '.join(query_parts)}"
            
            all_jobs = []
            start_index = 1
            
            # Google CSE only allows 10 results per request, max 100 results total
            while len(all_jobs) < num_results and start_index <= 91:  # 91 to ensure not to exceed 100
                batch_size = min(10, num_results - len(all_jobs))
                
                # Parameters for Google CSE API
                params = {
                    'key': self.api_key,
                    'cx': self.search_engine_id,
                    'q': query,
                    'num': batch_size,
                    'start': start_index,
                    'dateRestrict': 'm1',  # Last month
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
                    batch_jobs = self._parse_search_results(search_data)
                
                if not batch_jobs:  # No more results
                    break
                    
                all_jobs.extend(batch_jobs)
                start_index += 10
                
                # Rate limiting to avoid hitting API limits
                time.sleep(0.1)
            
            # Trim to exact number requested
            final_jobs = all_jobs[:num_results]
            
            return {
                "success": True,
                "query": query,
                "total_found": len(final_jobs),
                "jobs": final_jobs,
                "parsing_method": parsing_method,
                "source": "google_cse_api"
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"API request failed: {str(e)}",
                "jobs": []
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "jobs": []
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
                    manual_job = self._extract_job_info(item)
                    if manual_job:
                        jobs.append(manual_job)
        
        return jobs

    def _parse_search_results(self, search_data: Dict) -> List[Dict]:
        """
        Parses results from Google CSE API using manual methods
        
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
                job_info = self._extract_job_info(item)
                if job_info:
                    jobs.append(job_info)
        
        return jobs
    
    def _extract_job_info(self, item: Dict) -> Optional[Dict]:
        """
        Extracts job information from Google CSE search result
        
        Args:
            item (Dict): An item from Google CSE results
            
        Returns:
            Optional[Dict]: Job information or None if not valid
        """
        try:
            url = item.get('link', '')
            title = item.get('title', '')
            snippet = item.get('snippet', '')
            
            # Extract job ID from URL
            job_id_match = re.search(r'/jobs/view/(\d+)', url)
            job_id = job_id_match.group(1) if job_id_match else None
            
            # Clean title (remove common Google search artifacts)
            clean_title = self._clean_title(title)
            
            # Extract company name from title or snippet
            company = self._extract_company_name(clean_title, snippet)
            
            # Extract location from snippet
            location = self._extract_location(snippet)
            
            # Extract job type from snippet
            job_type = self._extract_job_type(snippet)
            
            # Extract salary info if any
            salary = self._extract_salary(snippet)
            
            # Extract posting date if any
            posted_date = self._extract_posted_date(snippet)
            
            return {
                "job_id": job_id,
                "title": clean_title,
                "company": company,
                "location": location,
                "job_type": job_type,
                "salary": salary,
                "posted_date": posted_date,
                "description": snippet,
                "url": url,
                "source": "linkedin"
            }
            
        except Exception as e:
            print(f"Error extracting job info: {e}")
            return None
    
    def _clean_title(self, title: str) -> str:
        """Cleans up title from Google search results"""
        # Remove common artifacts like " - LinkedIn"
        clean = re.sub(r'\s*-\s*LinkedIn.*$', '', title)
        clean = re.sub(r'\s*\|\s*LinkedIn.*$', '', clean)
        clean = re.sub(r'\s*–\s*LinkedIn.*$', '', clean)
        return clean.strip()
    
    def _extract_company_name(self, title: str, snippet: str) -> str:
        """Extracts company name from title or snippet"""
        # Patterns for company names in LinkedIn job titles
        company_patterns = [
            r'at\s+([^·\-\|]+?)(?:\s*[·\-\|]|\s*$)',
            r'·\s*([^·\-\|]+?)(?:\s*[·\-\|]|\s*$)',
            r'-\s*([^·\-\|]+?)(?:\s*[·\-\|]|\s*$)',
            r'\|\s*([^·\-\|]+?)(?:\s*[·\-\|]|\s*$)',
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                if len(company) > 2 and not any(word in company.lower() for word in ['job', 'career', 'hiring', 'posted']):
                    return company
        
        # Look in snippet for company info
        snippet_patterns = [
            r'Company:\s*([^\n\.\,]+)',
            r'Organization:\s*([^\n\.\,]+)',
            r'Employer:\s*([^\n\.\,]+)',
            r'Job at\s+([^\n\.\,]+)',
            r'Position at\s+([^\n\.\,]+)',
        ]
        
        for pattern in snippet_patterns:
            match = re.search(pattern, snippet, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                if len(company) > 2:
                    return company
        
        return "Unknown Company"
    
    def _extract_location(self, snippet: str) -> str:
        """Extracts location from snippet"""
        location_patterns = [
            r'Location:\s*([^\n\.\,]+)',
            r'Based in:\s*([^\n\.\,]+)',
            r'Office location:\s*([^\n\.\,]+)',
            r'([A-Za-z\s]+,\s*[A-Za-z\s]+(?:,\s*[A-Za-z\s]+)?)',  # City, State/Country pattern
            r'Remote\s*-\s*([^\n\.\,]+)',
            r'Hybrid\s*-\s*([^\n\.\,]+)',
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, snippet, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    location = match[0] if match else ""
                else:
                    location = match
                    
                location = location.strip()
                
                # Filter out common non-location text
                if (len(location) > 2 and 
                    not any(word in location.lower() for word in ['experience', 'years', 'apply', 'job', 'position', 'role'])):
                    return location
        
        # Check for remote/hybrid work
        if re.search(r'\b(remote|work from home|wfh)\b', snippet, re.IGNORECASE):
            return "Remote"
        if re.search(r'\bhybrid\b', snippet, re.IGNORECASE):
            return "Hybrid"
        
        return "Location not specified"
    
    def _extract_job_type(self, snippet: str) -> str:
        """Extracts job type from snippet"""
        job_type_patterns = [
            r'\b(Full[- ]time|Part[- ]time|Contract|Freelance|Internship|Temporary|Permanent)\b',
            r'Employment Type:\s*([^\n\.\,]+)',
            r'Job Type:\s*([^\n\.\,]+)',
            r'Position Type:\s*([^\n\.\,]+)',
        ]
        
        for pattern in job_type_patterns:
            match = re.search(pattern, snippet, re.IGNORECASE)
            if match:
                job_type = match.group(1).strip() if len(match.groups()) >= 1 else match.group(0).strip()
                return job_type
        
        return "Not specified"
    
    def _extract_salary(self, snippet: str) -> str:
        """Extracts salary info from snippet"""
        salary_patterns = [
            r'\$[\d,]+(?:\s*-\s*\$[\d,]+)?(?:\s*(?:per\s+)?(?:year|month|hour|annually))?',
            r'[\d,]+\s*-\s*[\d,]+\s*(?:USD|VND|EUR|GBP)',
            r'Salary:\s*([^\n\.\,]+)',
            r'Compensation:\s*([^\n\.\,]+)',
            r'Pay:\s*([^\n\.\,]+)',
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, snippet, re.IGNORECASE)
            if match:
                return match.group(0) if pattern.startswith(r'\$') or pattern.startswith(r'[\d,]+') else match.group(1)
        
        return "Not specified"
    
    def _extract_posted_date(self, snippet: str) -> str:
        """Extracts posted date from snippet"""
        date_patterns = [
            r'Posted:\s*([^\n\.\,]+)',
            r'Published:\s*([^\n\.\,]+)',
            r'(\d+)\s+(?:days?|hours?|weeks?|months?)\s+ago',
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{4}-\d{2}-\d{2})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, snippet, re.IGNORECASE)
            if match:
                return match.group(1) if len(match.groups()) >= 1 else match.group(0)
        
        return "Date not specified"
    
    def search_with_filters(self, 
                          keyword: str,
                          company: str = "",
                          location: str = "",
                          job_level: str = "",
                          date_range: str = "m1",  # m1=1 month, w1=1 week, d1=1 day
                          num_results: int = 10,
                          parsing_method: str = "manual") -> Dict:
        """
        Searches with advanced filters
        
        Args:
            keyword (str): Main keyword
            company (str): Specific company name
            location (str): Location
            job_level (str): Job level
            date_range (str): Time range (m1, w1, d1)
            num_results (int): Number of results
            parsing_method (str): "manual" for regex parsing or "llm" for LLM parsing
            
        Returns:
            Dict: Search result
        """
        # Validate parsing method
        if parsing_method == "llm" and not self.llm_available:
            print("Warning: LLM parsing requested but not available. Using manual parsing.")
            parsing_method = "manual"
        
        query_parts = [keyword]
        
        if company:
            query_parts.append(f'"{company}"')
        if location:
            query_parts.append(f'"{location}"')
        if job_level:
            query_parts.append(f'"{job_level}"')
            
        query = f"site:linkedin.com/jobs {' '.join(query_parts)}"
        
        try:
            params = {
                'key': self.api_key,
                'cx': self.search_engine_id,
                'q': query,
                'num': min(num_results, 10),
                'dateRestrict': date_range,
                'safe': 'medium'
            }
            
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            search_data = response.json()
            
            # Parse results based on chosen method
            if parsing_method == "llm":
                jobs = self._parse_search_results_llm(search_data)
            else:
                jobs = self._parse_search_results(search_data)
            
            return {
                "success": True,
                "query": query,
                "filters": {
                    "company": company,
                    "location": location,
                    "job_level": job_level,
                    "date_range": date_range
                },
                "total_found": len(jobs),
                "jobs": jobs,
                "parsing_method": parsing_method,
                "source": "google_cse_api"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "jobs": []
            }


def search_linkedin_jobs_google(api_key: str, 
                              search_engine_id: str,
                              keyword: str, 
                              location: str = "", 
                              job_type: str = "",
                              experience_level: str = "",
                              num_results: int = 10,
                              parsing_method: str = "manual",
                              ) -> Dict:
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
        
    Returns:
        Dict: Search result
    """
    searcher = GoogleCSELinkedInSearcher(api_key, search_engine_id)
    return searcher.search_linkedin_jobs(
        keyword=keyword,
        location=location,
        job_type=job_type,
        experience_level=experience_level,
        num_results=num_results,
        parsing_method=parsing_method
    )