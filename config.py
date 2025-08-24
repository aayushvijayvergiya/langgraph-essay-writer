from langchain_openai import ChatOpenAI
from tavily import TavilyClient

from dotenv import load_dotenv

load_dotenv()

model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
tavily = TavilyClient()

