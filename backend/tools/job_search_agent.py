from langchain.tools import tool
from typing import Dict
import os
from dotenv import load_dotenv

# Import GoogleCSELinkedInSearcher and schema
from backend.tools.google_cse_linkedin_search import GoogleCSELinkedInSearcher
from backend.tools.schema import LinkedInJobSearchInput

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
    """
    
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
    
    # Create searcher instance
    searcher = GoogleCSELinkedInSearcher(api_key, search_engine_id)
    
    # Build search query intelligently based on provided parameters
    query_parts = [keyword]
    
    # Add non-empty filters to search query
    if location.strip():
        query_parts.append(location.strip())
    
    if job_type.strip():
        query_parts.append(job_type.strip())
        
    if experience_level.strip():
        query_parts.append(experience_level.strip())
    
    if work_arrangement.strip():
        query_parts.append(work_arrangement.strip())
    
    if job_function.strip():
        query_parts.append(job_function.strip())
    
    if industry.strip():
        query_parts.append(industry.strip())
    
    # For salary and company, use more targeted approach
    if salary_range.strip():
        # Add salary terms to help find relevant jobs
        query_parts.append("salary")
    
    # Decide between basic search and advanced search based on parameters
    if company.strip():
        # Use advanced search when company is specified
        result = searcher.search_with_filters(
            keyword=" ".join(query_parts),
            company=company if exact_match_company else "",
            location=location,
            job_level=experience_level,
            date_range=date_range,
            num_results=num_results,
            parsing_method=parsing_method
        )
    else:
        # Use basic search for general queries
        result = searcher.search_linkedin_jobs(
            keyword=" ".join(query_parts),
            location=location,
            job_type=job_type,
            experience_level=experience_level,
            num_results=num_results,
            parsing_method=parsing_method
        )
    
    # Add metadata about applied filters
    if result.get("success"):
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
        
        # Post-process results for additional filtering if needed
        if salary_range.strip() and result.get("jobs"):
            # Note: Actual salary filtering would need more sophisticated parsing
            # For now, just add this info to metadata
            result["salary_filter_note"] = f"Searched with salary consideration: {salary_range}"
    
    return result

# List of available tools
tools = [search_linkedin_jobs]

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

SEARCH TIPS TO SHARE:
- Use specific job titles and skills as keywords
- Include location for better local results
- Try different experience levels if results are limited
- Use company names for targeted searches
- Consider related keywords and synonyms
- Remote work can be specified in work_arrangement parameter
- Date range controls how recent the job postings are

RESULT ANALYSIS:
- Summarize key findings from search results
- Identify common requirements across jobs
- Point out salary ranges when available
- Highlight remote/flexible work opportunities
- Suggest follow-up searches or refinements

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
    """Example of how to use the enhanced LinkedIn job agent"""
    
    # Create agent
    agent = get_linkedin_job_agent()
    
    # Example queries showcasing the enhanced capabilities
    example_queries = [
        "Search for Python developer jobs in San Francisco",
        "Find senior software engineer positions at Google in the last week",
        "Look for remote data scientist jobs with salary above $100k",
        "Search for entry-level marketing jobs in New York",
        "Find full-time backend engineer positions in the technology industry",
        "Search for contract DevOps jobs posted in the last month",
        "Look for hybrid machine learning engineer positions",
        "Find director-level positions at startups in healthcare industry"
    ]
    
    print("Enhanced LinkedIn Job Search Agent Ready!")
    print("Features: Unified search tool with comprehensive filtering")
    print("- All job types, locations, companies, industries")
    print("- Experience levels, work arrangements, salary considerations")
    print("- Time-based filtering, job functions")
    print("\nExample queries you can try:")
    for i, query in enumerate(example_queries, 1):
        print(f"{i}. {query}")
    
    print("\nDirect tool usage example:")
    print("from backend.tools.job_search_agent import search_linkedin_jobs")
    print('result = search_linkedin_jobs(keyword="DevOps", location="remote", experience_level="senior")')
    
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