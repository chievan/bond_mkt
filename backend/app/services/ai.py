from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from sqlalchemy.orm import Session
from ..models.bond import BondYield, BondSpread
import os

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")

class BondAIService:
    def __init__(self):
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            if not DEEPSEEK_API_KEY:
                raise ValueError("DEEPSEEK_API_KEY is not set in environment.")
            self._llm = ChatOpenAI(
                model="deepseek-chat",
                openai_api_key=DEEPSEEK_API_KEY,
                openai_api_base=DEEPSEEK_BASE_URL
            )
        return self._llm

    async def analyze_market(self, db: Session, user_query: str):
        # Fetch some context from DB
        latest_yields = db.query(BondYield).order_by(BondYield.date.desc()).first()
        latest_spreads = db.query(BondSpread).order_by(BondSpread.date.desc()).first()
        
        context = f"""
        当前市场数据 ({latest_yields.date if latest_yields else '未知'}):
        - 国债收益率: 1Y={latest_yields.y1 if latest_yields else '?'}, 10Y={latest_yields.y10 if latest_yields else '?'}
        - 关键利差: 10Y-2Y={latest_spreads.s10y_2y if latest_spreads else '?'} BP
        """
        
        prompt = ChatPromptTemplate.from_template("""
        你是一位专业的固定收益分析师。基于以下市场数据，回答用户的咨询。
        
        {context}
        
        用户问题: {query}
        
        要求：
        1. 语气专业且客观。
        2. 如果利差出现异常（如倒挂或处于历史极值），请特别指出。
        3. 给出简明扼要的结论。
        """)
        
        chain = prompt | self.llm
        response = await chain.ainvoke({"context": context, "query": user_query})
        
        return response.content

ai_service = BondAIService()
