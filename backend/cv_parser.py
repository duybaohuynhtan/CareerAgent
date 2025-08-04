from PyPDF2 import PdfReader
from dotenv import load_dotenv
from schema import ResumeSchema
from config import MODEL_NAME

def read_pdf(path):
    reader = PdfReader(path)
    text = []
    for page in reader.pages:
        text.append(page.extract_text())
    return "\n".join(text)

class CVParser:
    """
    CV/Resume parser using LLM for structured data extraction
    """
    def __init__(self):
        self.model_name = MODEL_NAME
        try:
            load_dotenv()
            from langchain_groq import ChatGroq
            from langchain_core.utils.function_calling import convert_to_openai_function
            from langchain.prompts import ChatPromptTemplate
            from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
            
            self.llm_model = ChatGroq(
                model=self.model_name,
                temperature=0,
            )
            self._setup_resume_extraction_chain()
            self.llm_available = True
        except Exception as e:
            print(f"Warning: LLM setup failed for CV parser: {e}")
            self.llm_available = False
    
    def _setup_resume_extraction_chain(self):
        """Setup LLM extraction chain for resume parsing"""
        try:
            from langchain_core.utils.function_calling import convert_to_openai_function
            from langchain.prompts import ChatPromptTemplate
            from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
            
            extraction_functions = [convert_to_openai_function(ResumeSchema)]
            extraction_model = self.llm_model.bind(
                functions=extraction_functions, 
                function_call={"name": "ResumeSchema"}
            )
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert resume/CV parser that extracts structured information from resumes. 

CRITICAL INSTRUCTIONS:
1. Extract ONLY information explicitly present in the resume text
2. DO NOT guess, infer, or make up any information
3. For ANY missing information, you MUST use the string "None" (never null, never empty string)
4. Be thorough and comprehensive in extracting all available details
5. Parse work experience chronologically with all details
6. Extract all skills mentioned, categorizing them appropriately
7. Identify education details including dates, degrees, institutions
8. Parse contact information carefully from headers/footers
9. Extract projects, certifications, awards, and other achievements
10. Determine experience level and skills proficiency from context
11. Parse salary expectations if mentioned
12. Identify preferred work arrangements (Remote/Hybrid/On-site)

PARSING GUIDELINES:
- For experiences: extract job titles, companies, dates, responsibilities, achievements
- For skills: categorize as technical vs soft skills, note proficiency if mentioned
- For education: get degree type, major, institution, graduation dates, GPA if present
- For projects: extract names, descriptions, technologies used, your role
- For certifications: get certification names, issuing bodies, dates, credential IDs
- For contact info: extract all contact methods, social profiles, portfolios

Remember: Use "None" string for any field where information is not explicitly available."""),
                ("human", "Resume/CV Content:\n{resume_text}")
            ])
            
            self.extraction_chain = prompt | extraction_model | JsonOutputFunctionsParser()
        except Exception as e:
            print(f"Error setting up resume extraction chain: {e}")
            self.llm_available = False
    
    def parse_resume_from_text(self, resume_text: str) -> dict:
        """
        Parse resume from text content using LLM
        
        Args:
            resume_text (str): The full text content of the resume
            
        Returns:
            dict: Parsed resume data according to ResumeSchema
        """
        if not self.llm_available:
            return {
                "success": False,
                "error": "LLM not available for resume parsing",
                "data": None
            }
        
        try:
            # Extract resume information using LLM
            resume_data = self.extraction_chain.invoke({
                "resume_text": resume_text
            })
            
            return {
                "success": True,
                "data": resume_data,
                "parsing_method": "llm",
                "source": "text_input"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error parsing resume: {str(e)}",
                "data": None
            }
    
    def parse_resume_from_pdf(self, pdf_path: str) -> dict:
        """
        Parse resume from PDF file
        
        Args:
            pdf_path (str): Path to the PDF file
            
        Returns:
            dict: Parsed resume data according to ResumeSchema
        """
        try:
            # Extract text from PDF
            resume_text = read_pdf(pdf_path)
            
            if not resume_text or resume_text.strip() == "":
                return {
                    "success": False,
                    "error": "Could not extract text from PDF or PDF is empty",
                    "data": None
                }
            
            # Parse the extracted text
            result = self.parse_resume_from_text(resume_text)
            result["source"] = "pdf_file"
            result["file_path"] = pdf_path
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error processing PDF: {str(e)}",
                "data": None
            }