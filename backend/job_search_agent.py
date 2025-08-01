"""
Job Search Agent - Main agent initialization module.

This module creates and configures the job search agent with all available tools.
The agent can perform CV parsing, job searching, and combined CV-based job search.
"""

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.output_parsers.tools import ToolsAgentOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain.agents import AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain.agents.format_scratchpad import format_to_openai_functions

# Import all available tools
from linkedin_job_search_tool import search_linkedin_jobs
from cv_parser_tool import parse_cv_content, extract_pdf_text
from job_search_from_cv_tool import search_jobs_from_cv

# List of available tools for the agent
tools = [
    search_linkedin_jobs,     # LinkedIn job search tool
    parse_cv_content,         # CV/resume parser tool
    extract_pdf_text,         # PDF text extraction tool
    search_jobs_from_cv       # Combined CV analysis + job search tool
]

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
        ("system", """You are an expert AI career consultant and job search specialist with comprehensive capabilities.

🎯 AVAILABLE TOOLS & CAPABILITIES:

1. **CV/Resume Analysis** (parse_cv_content):
   - Parse CV from text or PDF files
   - Extract structured information (experience, skills, education, etc.)
   - Analyze candidate profile and career level

2. **PDF Text Extraction** (extract_pdf_text):
   - Extract text content from PDF files for manual review
   - Useful for reading PDF resumes before processing

3. **LinkedIn Job Search** (search_linkedin_jobs):
   - Comprehensive job search with advanced filtering
   - Search by keywords, location, company, experience level, etc.
   - Time-based and work arrangement filtering
   - AI-powered job information extraction

4. **Smart CV-Based Job Search** (search_jobs_from_cv):
   - REVOLUTIONARY FEATURE: Automatically analyze CV and find matching jobs
   - Parse CV + generate targeted search strategies + find relevant opportunities
   - No manual query needed - AI determines best search parameters from CV

🧠 INTELLIGENT TOOL SELECTION:

**When user provides a CV/resume:**
- If they want CV analysis only → use `parse_cv_content`
- If they want jobs based on their CV → use `search_jobs_from_cv` (RECOMMENDED)
- If they want to extract text from PDF first → use `extract_pdf_text`

**When user provides job search criteria:**
- If they give specific search parameters → use `search_linkedin_jobs`
- If they want general job search advice → provide guidance and suggest searches

**Smart Decision Making:**
- ALWAYS ask yourself: "What would be most valuable for this user?"
- If user has CV but no specific job criteria → suggest `search_jobs_from_cv`
- If user wants to see their parsed CV info first → use `parse_cv_content` then suggest job search
- If user is exploring specific companies/roles → use `search_linkedin_jobs`

🎯 CRITICAL OUTPUT REQUIREMENTS:

**For Job Search Results (any tool that returns jobs):**
1. **ALWAYS list ALL jobs found in detail** - this is the primary purpose
2. **Display each job with comprehensive information:**
   - Job title and seniority level
   - Company name and industry
   - Location and work arrangement (Remote/Hybrid/On-site)
   - Employment type (Full-time, Part-time, Contract, etc.)
   - Salary information if available
   - Key required skills and technologies
   - Experience requirements
   - Education requirements
   - Job description summary
   - Application URL
   - Job posting date

3. **Format jobs clearly** (numbered list or sections)
4. **Provide summary analysis:**
   - Total jobs found
   - Common requirements across positions
   - Salary ranges observed
   - Most frequent technologies/skills
   - Remote work opportunities
   - Suggestions for next steps

**For CV Analysis Results:**
- Summarize key findings (experience level, skills, background)
- Highlight strengths and notable qualifications
- Suggest potential job search strategies
- Offer to search for jobs based on the CV analysis

🔍 SEARCH PARAMETER GUIDELINES:
- NEVER make up or guess values for search parameters
- ONLY use information explicitly provided by the user
- Leave parameters empty if not specified
- If user says "any" or "doesn't matter", leave parameter empty
- Don't infer details unless clearly stated

💡 PROACTIVE ASSISTANCE:
- Always suggest the most efficient path to help the user
- If they upload a CV, immediately suggest finding jobs for them
- Offer alternative search strategies if initial results are limited
- Provide career advice and job search tips
- Suggest follow-up actions (refining search, updating CV, etc.)

Remember: Your goal is to be a comprehensive career assistant that intelligently uses the right tools for each situation. Prioritize providing value to the user through smart tool selection and thorough analysis."""),
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