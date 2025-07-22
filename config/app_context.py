from agents.cas_etl_workflow import CasETLWorkflow
from agents.pf_analyzer_agent import PFAnalyzerAgent
from services.openai_service import OpenAIService

llm = OpenAIService()
cas_etl_workflow = CasETLWorkflow()
pf_analyzer_agent = PFAnalyzerAgent()
