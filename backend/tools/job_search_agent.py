from langchain.tools import tool
from pydantic import BaseModel, Field
from typing import Dict, Optional
import os
from dotenv import load_dotenv

# Import GoogleCSELinkedInSearcher
from backend.tools.google_cse_linkedin_search import GoogleCSELinkedInSearcher

# Define the input schema for LinkedIn job search
class LinkedInJobSearchInput(BaseModel):
    keyword: str = Field(..., description="Search keyword for job title, skills, or company name")
    location: str = Field(default="", description="Work location (city, state, country). Leave empty for all locations")
    job_type: str = Field(default="", description="Job type (full-time, part-time, contract, internship). Leave empty for all types")
    experience_level: str = Field(default="", description="Experience level (entry, mid, senior, lead). Leave empty for all levels")
    num_results: int = Field(default=10, description="Number of job results to return (1-50)")
    parsing_method: str = Field(default="llm", description="Parsing method: 'manual' for regex parsing or 'llm' for AI parsing")

@tool(args_schema=LinkedInJobSearchInput)
def search_linkedin_jobs(
    keyword: str, 
    location: str = "", 
    job_type: str = "",
    experience_level: str = "",
    num_results: int = 10,
    parsing_method: str = "llm"
) -> Dict:
    """Search for jobs on LinkedIn using Google Custom Search Engine. 
    Returns structured job information including title, company, location, salary, requirements, and more."""
    
    # Load environment variables
    load_dotenv()
    
    # Get API credentials from environment
    api_key = os.getenv('GOOGLE_API_KEY')
    search_engine_id = os.getenv('GOOGLE_CSE_ID')
    
    if not api_key or not search_engine_id:
        return {
            "success": False,
            "error": "Missing Google API credentials. Please set GOOGLE_API_KEY and GOOGLE_CSE_ID environment variables.",
            "jobs": []
        }
    
    # Validate num_results
    if num_results < 1 or num_results > 50:
        num_results = 10
    
    # Create searcher instance
    searcher = GoogleCSELinkedInSearcher(api_key, search_engine_id)
    
    # Perform search
    result = searcher.search_linkedin_jobs(
        keyword=keyword,
        location=location,
        job_type=job_type,
        experience_level=experience_level,
        num_results=num_results,
        parsing_method=parsing_method
    )
    
    return result

# Advanced search with filters
class LinkedInAdvancedSearchInput(BaseModel):
    keyword: str = Field(..., description="Main search keyword")
    company: str = Field(default="", description="Specific company name to search within")
    location: str = Field(default="", description="Work location filter")
    job_level: str = Field(default="", description="Job level filter (entry, senior, director, etc.)")
    date_range: str = Field(default="m1", description="Time range: 'm1' (1 month), 'w1' (1 week), 'd1' (1 day)")
    num_results: int = Field(default=10, description="Number of results to return (1-50)")
    parsing_method: str = Field(default="llm", description="Parsing method: 'manual' or 'llm'")

@tool(args_schema=LinkedInAdvancedSearchInput)
def search_linkedin_jobs_advanced(
    keyword: str,
    company: str = "",
    location: str = "",
    job_level: str = "",
    date_range: str = "m1",
    num_results: int = 10,
    parsing_method: str = "llm"
) -> Dict:
    """Advanced LinkedIn job search with company, location, and job level filters.
    Allows searching within specific companies and date ranges."""
    
    # Load environment variables
    load_dotenv()
    
    # Get API credentials from environment
    api_key = os.getenv('GOOGLE_API_KEY')
    search_engine_id = os.getenv('GOOGLE_CSE_ID')
    
    if not api_key or not search_engine_id:
        return {
            "success": False,
            "error": "Missing Google API credentials. Please set GOOGLE_API_KEY and GOOGLE_CSE_ID environment variables.",
            "jobs": []
        }
    
    # Validate inputs
    if num_results < 1 or num_results > 50:
        num_results = 10
        
    if date_range not in ['m1', 'w1', 'd1', 'm2', 'm3', 'm6']:
        date_range = 'm1'
    
    # Create searcher instance
    searcher = GoogleCSELinkedInSearcher(api_key, search_engine_id)
    
    # Perform advanced search
    result = searcher.search_with_filters(
        keyword=keyword,
        company=company,
        location=location,
        job_level=job_level,
        date_range=date_range,
        num_results=num_results,
        parsing_method=parsing_method
    )
    
    return result

# List of available tools
tools = [search_linkedin_jobs, search_linkedin_jobs_advanced]

# Setup conversation model with LinkedIn job search capabilities
def create_linkedin_job_agent():
    """Creates a conversational agent with LinkedIn job search capabilities"""
    
    from langchain_groq import ChatGroq
    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain.tools.render import format_tool_to_openai_function
    from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
    from langchain.schema.runnable import RunnablePassthrough
    from langchain.agents import AgentExecutor
    from langchain.memory import ConversationBufferMemory
    from langchain.agents.format_scratchpad import format_to_openai_functions
    
    # Load environment variables
    load_dotenv()
    
    # Initialize model
    functions = [format_tool_to_openai_function(f) for f in tools]
    model = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.1
    ).bind(functions=functions)
    
    # Create prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful AI assistant specialized in LinkedIn job searching and career guidance.

CAPABILITIES:
- Search LinkedIn jobs by keywords, location, job type, and experience level
- Advanced job search with company filters and date ranges
- Analyze job requirements and match them with candidate profiles
- Provide career advice and job search strategies

INSTRUCTIONS:
1. When users ask about job searches, use the appropriate LinkedIn search tool
2. For basic searches, use search_linkedin_jobs
3. For searches within specific companies or with advanced filters, use search_linkedin_jobs_advanced
4. Always provide helpful analysis and insights about the search results
5. Suggest relevant keywords and search strategies to users
6. Be proactive in offering additional search refinements

SEARCH TIPS TO SHARE:
- Use specific job titles and skills as keywords
- Include location for better local results
- Try different experience levels if results are limited
- Use company names for targeted searches
- Consider related keywords and synonyms

Remember to be helpful, informative, and provide actionable advice for job seekers."""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])
    
    # Create agent chain
    agent_chain = RunnablePassthrough.assign(
        agent_scratchpad=lambda x: format_to_openai_functions(x["intermediate_steps"])
    ) | prompt | model | OpenAIFunctionsAgentOutputParser()
    
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
def get_linkedin_job_agent():
    """Get a LinkedIn job search agent ready for conversation"""
    return create_linkedin_job_agent()

# Example usage function
def example_usage():
    """Example of how to use the LinkedIn job agent"""
    
    # Create agent
    agent = get_linkedin_job_agent()
    
    # Example queries
    example_queries = [
        "Search for Python developer jobs in San Francisco",
        "Find senior software engineer positions at Google",
        "Look for remote data scientist jobs posted in the last week",
        "Search for entry-level marketing jobs in New York"
    ]
    
    print("LinkedIn Job Search Agent Ready!")
    print("Example queries you can try:")
    for i, query in enumerate(example_queries, 1):
        print(f"{i}. {query}")
    
    return agent

if __name__ == "__main__":
    # Demo the agent
    agent = example_usage()
    
    # Interactive demo
    print("\n" + "="*50)
    print("Interactive Demo - Type 'quit' to exit")
    print("="*50)
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("Goodbye!")
            break
        
        try:
            response = agent.invoke({"input": user_input})
            print(f"\nAgent: {response['output']}")
        except Exception as e:
            print(f"Error: {str(e)}")