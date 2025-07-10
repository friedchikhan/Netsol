# from dotenv import load_dotenv
# load_dotenv()

# from langchain.chat_models import ChatOpenAI
# from langchain.memory import ConversationBufferMemory
# from langchain.prompts import PromptTemplate
# from langchain_community.agent_toolkits.load_tools import load_tools
# from langchain.agents import initialize_agent, AgentType

# from .televy_tool import search_tool
# from .rag import is_netsol_query, generate_rag_answer

# llm = ChatOpenAI(model_name="gpt-4.1-nano", temperature=0.6)

# tools = [search_tool]
# tool_desc = "\n".join(f"> {t.name}: {t.description}" for t in tools)

# prompt = PromptTemplate(
#     input_variables=["input"],
#     template=f"""
# You are a helpful assistant with access to Tavily search:

# {tool_desc}

# When asked non-Netsol questions, use Tavily.

# Use exactly:
#   Action: <tool name>
#   Action Input: <what you send it>
# Then wait for the Observation, then say:
#   Final Answer: <your answer>

# User: {{input}}
# Assistant:"""
# )

# memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# agent = initialize_agent(
#     tools=tools,
#     llm=llm,
#     agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
#     verbose=True,
#     handle_parsing_errors=True,
#     memory=memory,
#     agent_kwargs={"prompt": prompt},
# )

# def run_agent(query: str) -> str:
#     if is_netsol_query(query):
#         return generate_rag_answer(query)
#     return agent.run(query)


#correct non thread code
# import uuid
# from langgraph.graph import StateGraph, START, END, MessagesState
# from langchain_core.messages import HumanMessage, AIMessage
# from langchain_community.chat_models import ChatOpenAI
# from langgraph.checkpoint.memory import MemorySaver
# from .rag import generate_rag_answer, is_netsol_query
# from .televy_tool import search_tool

# graph = StateGraph(MessagesState)

# llm = ChatOpenAI(model_name="gpt-4.1-nano", temperature=0.7)

# tool_desc = (
#     f"> tavily-search: {search_tool.description}\n"
#     f"> rag: use your RAG backend for Netsol-specific queries"
# )

# def plan_node(state: MessagesState) -> dict[str, list]:
#     user_input = state["messages"][-1].content
#     prompt = f"""
# You have TWO backends:
# {tool_desc}

# If the user’s question is about Netsol (financials, PDF content, 2024 report, etc.), use RAG.
# Otherwise for any factual or real-time question, use Tavily search.

# OUTPUT EXACTLY (no extra text!):
# Action: <rag OR tavily-search>
# Action Input: <what you send it>

# User asked: {user_input}
# Assistant (plan):"""
#     plan = llm.invoke([HumanMessage(content=prompt)]).content
#     return {"messages": state["messages"] + [AIMessage(content=plan)]}

# def tool_node(state: MessagesState) -> dict[str, list]:
#     plan = state["messages"][-1].content
#     lines = plan.splitlines()
#     action_line = next((l for l in lines if l.startswith("Action:")), "")
#     input_line  = next((l for l in lines if l.startswith("Action Input:")), "")
#     tool_name  = action_line.replace("Action:", "").strip()
#     tool_input = input_line.replace("Action Input:", "").strip()

#     if tool_name == "rag":
#         result = generate_rag_answer(tool_input)
#     else:
#         resp = search_tool.func(tool_input)
#         print("🔍 Raw Tavily response:", resp)
#         results  = resp.get("results", []) if isinstance(resp, dict) else []
#         def get_score(result):
#             return result.get("score", 0)

#         snippets = sorted(results, key=get_score, reverse=True)[:3]
#         if snippets:
#             summary = snippets[0].get("content") or snippets[0].get("title")
#         else:
#             summary = resp.get("answer", "No result found.")
#         result = summary

#     obs_msg = AIMessage(content=f"Observation: {result}")
#     return {"messages": state["messages"] + [obs_msg]}

# def finish_node(state: MessagesState) -> dict[str, list]:
#     response = llm.invoke(state["messages"])
#     return {"messages": state["messages"] + [response]}

# graph.add_node("plan",   plan_node)
# graph.add_node("tool",   tool_node)
# graph.add_node("finish", finish_node)

# graph.add_edge(START,    "plan")
# graph.add_edge("plan",   "tool")
# graph.add_edge("tool",   "finish")
# graph.add_edge("finish", END)

# memory       = MemorySaver()
# compiled_app = graph.compile(checkpointer=memory)
# THREAD_ID    = str(uuid.uuid4())

# def run_agent(query: str) -> str:
#     initial = {"messages": [HumanMessage(content=query)]}
#     config  = {"configurable": {"thread_id": THREAD_ID}}
#     final   = compiled_app.invoke(initial, config)
#     return final["messages"][-1].content


#thread code

# import uuid
# from langgraph.graph import StateGraph, START, END, MessagesState
# from langchain_core.messages import HumanMessage, AIMessage
# from langchain_community.chat_models import ChatOpenAI
# from langgraph.checkpoint.memory import MemorySaver

# from .rag import generate_rag_answer, is_netsol_query
# from .televy_tool import search_tool

# graph = StateGraph(MessagesState)

# llm = ChatOpenAI(model_name="gpt-4.1-nano", temperature=0.7)

# tool_desc = (
#     f"> tavily-search: {search_tool.description}\n"
#     f"> rag: use your RAG backend for Netsol-specific queries"
# )

# def plan_node(state: MessagesState) -> dict[str, list]:
#     user_input = state["messages"][-1].content
#     prompt = f"""
# You have TWO backends:
# {tool_desc}

# If the user’s question is about Netsol (financials, PDF content, 2024 report, etc.), use RAG.
# Otherwise for any factual or real-time question, use Tavily search.

# OUTPUT EXACTLY (no extra text!):
# Action: <rag OR tavily-search>
# Action Input: <what you send it>

# User asked: {user_input}
# Assistant (plan):"""
#     plan = llm.invoke([HumanMessage(content=prompt)]).content
#     return {"messages": state["messages"] + [AIMessage(content=plan)]}

# def tool_node(state: MessagesState) -> dict[str, list]:
#     plan    = state["messages"][-1].content
#     lines   = plan.splitlines()
#     action  = next((l for l in lines if l.startswith("Action:")), "")
#     inp     = next((l for l in lines if l.startswith("Action Input:")), "")
#     tool_nm = action.replace("Action:", "").strip()
#     tool_q  = inp.replace("Action Input:", "").strip()

#     if tool_nm == "rag":
#         result = generate_rag_answer(tool_q)
#     else:
#         resp    = search_tool.func(tool_q)
#         print("🔍 Raw Tavily response:", resp)
#         results = resp.get("results", []) if isinstance(resp, dict) else []
#         # pick top‐scoring snippet
#         def get_score(r): return r.get("score", 0)
#         top3    = sorted(results, key=get_score, reverse=True)[:3]
#         if top3:
#             summary = top3[0].get("content") or top3[0].get("title")
#         else:
#             summary = resp.get("answer", "No result found.")
#         result = summary

#     obs = AIMessage(content=f"Observation: {result}")
#     return {"messages": state["messages"] + [obs]}

# def finish_node(state: MessagesState) -> dict[str, list]:
#     response = llm.invoke(state["messages"])
#     return {"messages": state["messages"] + [response]}

# graph.add_node("plan",   plan_node)
# graph.add_node("tool",   tool_node)
# graph.add_node("finish", finish_node)

# graph.add_edge(START,  "plan")
# graph.add_edge("plan",  "tool")
# graph.add_edge("tool",  "finish")
# graph.add_edge("finish", END)

# memory       = MemorySaver()
# compiled_app = graph.compile(checkpointer=memory)

# def run_agent(query: str, thread_id: str) -> str:
#     """
#     Now requires the per-session thread_id from main.py
#     """
#     initial = {"messages": [HumanMessage(content=query)]}
#     config  = {"configurable": {"thread_id": thread_id}}
#     final   = compiled_app.invoke(initial, config)
#     return final["messages"][-1].content

# agent.py
import uuid
from langgraph.graph import StateGraph, START, END, MessagesState
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.chat_models import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver

from .rag import generate_rag_answer, is_netsol_query
from .televy_tool import search_tool

# ─── build your graph as before ────────────────────────────────────────────────
graph = StateGraph(MessagesState)
llm       = ChatOpenAI(model_name="gpt-4.1-nano", temperature=0.7)
tool_desc = f"> tavily-search: {search_tool.description}\n> rag: use your RAG backend"

def plan_node(state: MessagesState):
    user_in = state["messages"][-1].content
    prompt  = f"""
You have TWO backends:
{tool_desc}

If it's a Netsol question, use RAG.
Otherwise, use Tavily search.

OUTPUT EXACTLY:
Action: <rag OR tavily-search>
Action Input: <what you send>

User asked: {user_in}
Assistant (plan):"""
    plan = llm.invoke([HumanMessage(content=prompt)]).content
    return {"messages": state["messages"] + [AIMessage(content=plan)]}

def tool_node(state: MessagesState):
    plan = state["messages"][-1].content.splitlines()
    act  = next(l for l in plan if l.startswith("Action:")).split(":",1)[1].strip()
    inp  = next(l for l in plan if l.startswith("Action Input:")).split(":",1)[1].strip()
    if act=="rag":
        res = generate_rag_answer(inp)
    else:
        resp = search_tool.func(inp)
        snippets = sorted(resp.get("results",[]),
                          key=lambda r: r.get("score",0),
                          reverse=True)[:3]
        res = snippets[0].get("content") or snippets[0].get("title") if snippets else resp.get("answer","")
    return {"messages": state["messages"] + [AIMessage(content=f"Observation: {res}")]}

def finish_node(state: MessagesState):
    reply = llm.invoke(state["messages"])
    return {"messages": state["messages"] + [reply]}

# assemble graph
graph.add_node("plan", plan_node)
graph.add_node("tool", tool_node)
graph.add_node("finish", finish_node)
graph.add_edge(START, "plan")
graph.add_edge("plan", "tool")
graph.add_edge("tool", "finish")
graph.add_edge("finish", END)

memory       = MemorySaver()
compiled_app = graph.compile(checkpointer=memory)

def run_agent(query: str, thread_id: str) -> str:
    init   = {"messages":[HumanMessage(content=query)]}
    cfg    = {"configurable":{"thread_id":thread_id}}
    final  = compiled_app.invoke(init, cfg)
    return final["messages"][-1].content

def run_agent_stream(query: str, thread_id: str):
    # 1) Inline plan+tool to build context
    state = {"messages":[HumanMessage(content=query)]}
    state = {"messages": plan_node(state)["messages"]}
    state = {"messages": tool_node(state)["messages"]}
    history = state["messages"]

    # 2) Spawn a streaming LLM for the final response
    streamer = ChatOpenAI(
        model_name="gpt-4.1-nano",
        temperature=0.7,
        streaming=True
    )
    for chunk in streamer.stream(history):
        # chunk is an AIMessage; yield its piece of text
        yield chunk.content  