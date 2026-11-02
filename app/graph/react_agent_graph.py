from langgraph.prebuilt import create_react_agent

from app.config import settings
from app.llm import get_llm
from app.tools import get_tools


def build_react_agent_graph():
    llm = get_llm(settings.tools_llm_model)
    tools = get_tools()

    return create_react_agent(
        model=llm,
        tools=tools,
    )