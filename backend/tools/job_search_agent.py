from langchain.tools import tool
from typing import Dict
import os
from dotenv import load_dotenv

# Import GoogleCSELinkedInSearcher and schema
from google_cse_linkedin_search import GoogleCSELinkedInSearcher
from schema import LinkedInJobSearchInput

from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.output_parsers.tools import ToolsAgentOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain.agents import AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain.agents.format_scratchpad import format_to_openai_functions

@tool(args_schema=LinkedInJobSearchInput)
def search_linkedin_jobs(
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
    exact_match_company: bool = False,
    model_name: str = "deepseek-r1-distill-llama-70b"
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
    searcher = GoogleCSELinkedInSearcher(api_key, search_engine_id, model_name=model_name)
    
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

# List of available tools
tools = [search_linkedin_jobs]

# Setup conversation model with LinkedIn job search capabilities
def create_linkedin_job_agent(model_name: str = "deepseek-r1-distill-llama-70b"):
    """Creates a conversational agent with LinkedIn job search capabilities
    
    Args:
        model_name (str): LLM model name to use for the agent
    """

    # Load environment variables
    load_dotenv()
    
    # Initialize model
    model = ChatGroq(
        model=model_name,
        temperature=0
    ).bind_tools(tools=tools)
    
    # Create prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful AI assistant specialized in LinkedIn job searching and career guidance.

CAPABILITIES:
- Comprehensive LinkedIn job search with advanced filtering capabilities
- Search by keywords, location, job type, experience level, company, industry
- Time-based filtering (recent postings)
- Work arrangement filtering (remote, hybrid, on-site)
- Salary range considerations
- Job function and industry targeting
- Analyze job requirements and match them with candidate profiles
- Provide career advice and job search strategies

CRITICAL INSTRUCTION FOR SEARCH PARAMETERS:
- NEVER make up or guess values for search parameters
- ONLY use information explicitly provided by the user
- Leave parameters empty if the user doesn't specify them
- If user says "any" or "doesn't matter", leave that parameter empty
- Don't infer location, company, or other details unless clearly stated

SEARCH TOOL USAGE:
1. Use search_linkedin_jobs for all job searches (unified tool)
2. Fill only the parameters the user explicitly provides
3. Set parsing_method to "llm" for best results (AI-powered extraction)
4. Use appropriate num_results based on user request (default 10)
5. Always provide helpful analysis and insights about the search results
6. Suggest relevant keywords and search strategies
7. Be proactive in offering additional search refinements

CRITICAL OUTPUT REQUIREMENTS FOR JOB SEARCH RESULTS:
When you receive job search results, you MUST:
1. **ALWAYS list ALL jobs found in detail** - this is the primary purpose
2. **Display each job with comprehensive information including:**
   - Job title and seniority level
   - Company name and industry information
   - Location and work arrangement (Remote/Hybrid/On-site)
   - Employment type (Full-time, Part-time, Contract, etc.)
   - Salary information if available
   - Key required skills and technologies
   - Experience requirements
   - Education requirements
   - Job description summary
   - Application URL
   - Job posting date
3. **Format jobs in a clear, structured manner** (numbered list or sections)
4. **After listing all jobs, provide summary analysis:**
   - Total number of jobs found
   - Common requirements across positions
   - Salary ranges observed
   - Most frequent technologies/skills
   - Remote work opportunities
   - Suggestions for improving search or next steps

SEARCH TIPS TO SHARE:
- Use specific job titles and skills as keywords
- Include location for better local results
- Try different experience levels if results are limited
- Use company names for targeted searches
- Consider related keywords and synonyms
- Remote work can be specified in work_arrangement parameter
- Date range controls how recent the job postings are

Remember: Users are searching for jobs, so they need to see detailed job listings first and foremost. Analysis and advice come secondary to presenting the actual job opportunities."""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])
    
    # Create agent chain
    agent_chain = RunnablePassthrough.assign(
        agent_scratchpad=lambda x: format_to_openai_functions(x["intermediate_steps"])
    ) | prompt | model | ToolsAgentOutputParser()
    
    # Setup memory
    memory = ConversationBufferMemory(return_messages=True, memory_key="chat_history")
    
    # Create agent executor
    agent_executor = AgentExecutor(
        agent=agent_chain, 
        tools=tools, 
        verbose=True, 
        memory=memory,
        handle_parsing_errors=True
    )
    
    return agent_executor

# Convenience function to get a ready-to-use agent
def get_linkedin_job_agent(model_name: str = "deepseek-r1-distill-llama-70b"):
    """Get a LinkedIn job search agent ready for conversation
    
    Args:
        model_name (str): LLM model name to use for the agent
    """
    return create_linkedin_job_agent(model_name=model_name)