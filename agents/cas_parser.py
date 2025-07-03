from lib.pdf_utils import parse_pdf

GET_PORTFOLIO_PROMPT = """
    You are a raw pdf text parser for mutual funds consolidated account statement.

    Your task is to create the below two tables:
    - transactions: extract the transactions for each fund.
    - portfolio: also for each fund, opening and closing unit balances, nav as on the cas date, total cost value and market value, absolute gain or loss, percentage gain or loss


    Guidelines:
    - Do not assume values if not explicitly stated.
"""


class CASParserAgent:
    def __init__(self, llm_service):
        self.llm_service = llm_service

    async def get_portfolio_from_pdf(self, file, password):
        pdf_stream = await file.read()
        pdf_contents = parse_pdf(pdf_stream, password)
        messages = [
            {"role": "system", "content": GET_PORTFOLIO_PROMPT},
            {"role": "user", "content": pdf_contents},
        ]
        reply = self.llm_service.ask(messages)
        return reply.choices[0].message.content
