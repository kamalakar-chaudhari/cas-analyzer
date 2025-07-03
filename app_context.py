from agents import pf_analyzer
from agents.cas_parser import CASParserAgent
from services.openai_service import OpenAIService


llm_service = OpenAIService()
cas_parser_agent = CASParserAgent(llm_service=llm_service)
pf_analyzer_agent = pf_analyzer.PFAnalyzerAgent(llm_service=llm_service)
