from .financial_analysis import FinancialAnalysisService
from .general_knowledge import GeneralKnowledgeServices
from .investment_advice import InvestmentAdviceService
from ..entities.user_intent import UserIntent
from .route_query import RouteQueryService

class FinancialAssistant:
    def __init__(self, client, fmp_api_key: str, fh_api_key: str):
        self.client = client
        self.fmp_api_key = fmp_api_key
        self.fh_api_key = fh_api_key

    def run(self, query: str) -> dict:
        """
        Routes the query, calls the appropriate handler, and returns the result as a dictionary.
        """
        route_query_service = RouteQueryService(self.client)
        intent_classification = route_query_service.route_query(query)
        intent = intent_classification.intent
        
        if intent == UserIntent.TICKER_ANALYSIS:
            financial_analysis_service = FinancialAnalysisService(
                self.client, 
                self.fmp_api_key, 
                self.fh_api_key
            )
            analysis = financial_analysis_service.create_financial_analysis(query)
            if analysis:
                return {
                    "type": "ticker_analysis",
                    "data": analysis.dict()
                }
            return {"type": "error", "data": {"message": "Could not generate financial analysis."}}
                
        elif intent == UserIntent.GENERAL_KNOWLEDGE:
            general_knowledge_service = GeneralKnowledgeServices(self.client)
            response = general_knowledge_service.handle_general_question(query)
            if response:
                return {
                    "type": "general_knowledge",
                    "data": response.dict()
                }
            return {"type": "error", "data": {"message": "Could not generate general knowledge response."}}
        
        elif intent == UserIntent.INVESTMENT_ADVICE:
            investment_advice_service = InvestmentAdviceService(self.client)
            advice = investment_advice_service.provide_investment_advice(query)
            if advice:
                return {"type": "investment_advice", "data": advice.dict()}
            return {"type": "error", "data": {"message": "Could not generate investment advice."}}
        
        return {"type": "error", "data": {"message": "Could not determine user intent."}}

