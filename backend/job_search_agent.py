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
from config import get_current_model

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
def create_linkedin_job_agent():
    """Creates a conversational agent with LinkedIn job search capabilities
    """

    # Load environment variables
    load_dotenv()
    
    # Initialize model - get current model dynamically
    current_model = get_current_model()
    print(f"Creating agent with model: {current_model}")  # Debug log
    model = ChatGroq(
        model=current_model,
        temperature=0
    ).bind_tools(tools=tools)
    
    # Create prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a friendly and knowledgeable AI career consultant. You can have natural conversations about careers, job searching, and professional development, while also helping with specific tasks using your tools when needed.

🤖 **YOUR PERSONALITY:**
- Be conversational and approachable - respond naturally to greetings, questions, and casual conversation
- Provide helpful career advice and insights even without using tools
- Only use tools when the user has a specific request that requires them
- If someone just says "hi" or asks a general question, respond normally without invoking tools

🛠️ **AVAILABLE TOOLS** (use only when specifically needed):

1. **parse_cv_content** - Analyze CV/resume content and extract structured information
2. **extract_pdf_text** - Extract text from PDF files for review  
3. **search_linkedin_jobs** - Search for jobs with specific criteria (keywords, location, company, etc.)
4. **search_jobs_from_cv** - Automatically find jobs that match a provided CV/resume

🎯 **WHEN TO USE TOOLS:**
- **CV Analysis**: User wants their CV/resume parsed or analyzed → use `parse_cv_content`
- **Job Search**: User provides specific search criteria → use `search_linkedin_jobs`  
- **Smart Job Matching**: User provides CV and wants job recommendations → use `search_jobs_from_cv`
- **PDF Processing**: User needs text extracted from PDF → use `extract_pdf_text`

🎯 **WHEN NOT TO USE TOOLS:**
- General career questions or advice
- Greetings and casual conversation
- Questions about job search strategies  
- Resume writing tips
- Industry insights
- Salary negotiation advice

💬 **OUTPUT GUIDELINES:**
- For casual conversation: Respond naturally and helpfully
- For tool results: Present information clearly and comprehensively
- Always be helpful and suggest next steps when appropriate
- Keep the conversation flowing - ask follow-up questions when relevant

Remember: You're a helpful career assistant who can both chat naturally AND perform specific tasks. Use tools only when the user's request specifically requires them."""),
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