from dotenv import load_dotenv
load_dotenv()  

import os
from tavily import TavilyClient
from langchain.tools import Tool

tv = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

search_tool = Tool(
    name="tavily-search",
    func=lambda query: tv.search(query),
    description="Useful for real-time internet searches via Tavily"
)