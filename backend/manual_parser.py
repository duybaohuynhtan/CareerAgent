"""
Manual parsing utilities for LinkedIn job search results.

This module contains all the regex-based parsing logic for extracting
job information from Google Custom Search Engine results.
"""

import re
from typing import Dict, List, Optional


class LinkedInJobManualParser:
    """
    Manual parser for LinkedIn job search results using regex patterns.
    
    This class handles the extraction of job information from Google CSE
    search results when LLM parsing is not available or preferred.
    """
    
    def __init__(self):
        """Initialize the manual parser with predefined patterns."""
        pass
    
    def parse_search_results(self, search_data: Dict) -> List[Dict]:
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
                job_info = self.extract_job_info(item)
                if job_info:
                    jobs.append(job_info)
        
        return jobs
    
    def extract_job_info(self, item: Dict) -> Optional[Dict]:
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
            clean_title = self.clean_title(title)
            
            # Extract company name from title or snippet
            company = self.extract_company_name(clean_title, snippet)
            
            # Extract location from snippet
            location = self.extract_location(snippet)
            
            # Extract job type from snippet
            job_type = self.extract_job_type(snippet)
            
            # Extract salary info if any
            salary = self.extract_salary(snippet)
            
            # Extract posting date if any
            posted_date = self.extract_posted_date(snippet)
            
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
    
    def clean_title(self, title: str) -> str:
        """Cleans up title from Google search results"""
        # Remove common artifacts like " - LinkedIn"
        clean = re.sub(r'\s*-\s*LinkedIn.*$', '', title)
        clean = re.sub(r'\s*\|\s*LinkedIn.*$', '', clean)
        clean = re.sub(r'\s*–\s*LinkedIn.*$', '', clean)
        return clean.strip()
    
    def extract_company_name(self, title: str, snippet: str) -> str:
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
    
    def extract_location(self, snippet: str) -> str:
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
    
    def extract_job_type(self, snippet: str) -> str:
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
    
    def extract_salary(self, snippet: str) -> str:
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
    
    def extract_posted_date(self, snippet: str) -> str:
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