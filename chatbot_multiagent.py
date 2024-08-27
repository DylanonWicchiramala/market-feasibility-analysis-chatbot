# %%
import os
import utils

utils.load_env()
os.environ['LANGCHAIN_TRACING_V2'] = "false"

# %%
from langchain.globals import set_debug, set_verbose

set_verbose(True)
set_debug(False)

# %%
# def store_memory(result, user_id):
#      history.update_one({"user_id":user_id}, {"$push":{
#           "chat_history" : {"$each":[
#                          (result["messages"][0].content),
#                          (result["messages"][-1].content)
#                             ]}}})

# def QA(question, user_id):
#      query = history.find_one({"user_id": user_id})
#      if query is None:
#           query = {
#                "user_id": user_id,
#                "chat_history": [],
#           }
#           history.insert_one(query)
     
#      chat_history = []
#      for i, msg in enumerate(query["chat_history"]):
#           chat_history.append(
#                AIMessage(msg) if i % 2 == 1 else HumanMessage(msg)
#           )

#      result = graph.invoke({
#           "messages": [
#                HumanMessage(
#                     content=question
#                )
#           ],
#           "chat_history":chat_history,
          
#      },)
#      store_memory(result, user_id)
#      return result

# %%
from langchain import LLMChain
from langchain_core.messages import HumanMessage
import operator
import functools

# for llm model
from langchain_openai import ChatOpenAI
# from langchain_community.chat_models import ChatOpenAI
from tools import (
    find_place_from_text, 
    nearby_search, 
    nearby_dense_community, 
    google_search, 
    population_doc_retriever,
    duckduckgo_search
)
from typing import Annotated, Sequence, TypedDict, List
from langchain_core.messages import (
    AIMessage, 
    HumanMessage,
    BaseMessage,
    ToolMessage
)
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langgraph.graph import END, StateGraph, START



## tools and LLM
# Bind the tools to the model
tools = [population_doc_retriever, find_place_from_text, nearby_search, nearby_dense_community, duckduckgo_search]  # Include both tools if needed
# tools = [google_search]

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)


## Create agents
def create_agent(llm, tools, system_message: str):
    # memory = ConversationBufferMemory(memory_key='chat_history', return_messages=False)
    """Create an agent."""
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful AI assistant, collaborating with other assistants."
                " Use the provided tools to progress towards answering the question."
                " If you are unable to fully answer, that's OK, another assistant with different tools "
                " will help where you left off. Execute what you can to make progress."
                " If you or any of the other assistants have the final answer or deliverable,"
                " "
                " You have access to the following tools: {tool_names}.\n{system_message}",
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    prompt = prompt.partial(system_message=system_message)
    prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
    #llm_with_tools = llm.bind(functions=[format_tool_to_openai_function(t) for t in tools])
    llm_with_tools = llm.bind_tools(tools)
    # agent = LLMChain(
    #     prompt=prompt,
    #     llm=llm_with_tools,
    #     # memory=memory
    # )
    # return agent
    return prompt | llm.bind_tools(tools)
    #agent = prompt | llm_with_tools
    #return agent


## Define state
# This defines the object that is passed between each node
# in the graph. We will create different nodes for each agent and tool
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    chat_history: List[BaseMessage]
    sender: str


# Helper function to create a node for a given agent
def agent_node(state, agent, name):
    result = agent.invoke(state)
    # We convert the agent output into a format that is suitable to append to the global state
    if isinstance(result, ToolMessage):
        pass
    else:
        result = AIMessage(**result.dict(exclude={"type", "name"}), name=name)
        # result = AIMessage(**result.dict(), name=name)
    return {
        "messages": [result],
        # Since we have a strict workflow, we can
        # track the sender so we know who to pass to next.
        "sender": name,
    }


## Define Agents Node
# Research agent and node
from prompt import agent_meta
agent_name = [meta['name'] for meta in agent_meta]

agents={}
agent_nodes={}

for meta in agent_meta:
    name = meta['name']
    prompt = meta['prompt']
    
    agents[name] = create_agent(
            llm,
            tools,
            system_message=prompt,
        )
    
    agent_nodes[name] = functools.partial(agent_node, agent=agents[name], name=name)


## Define Tool Node
from langgraph.prebuilt import ToolNode
from typing import Literal

tool_node = ToolNode(tools)

def router(state) -> Literal["call_tool", "__end__", "continue"]:
    # This is the router
    messages = state["messages"]
    last_message = messages[-1]
    if "continue" in last_message.content:
        return "continue"
    if last_message.tool_calls:
        # The previous agent is invoking a tool
        return "call_tool"
    if "%SIjfE923hf" in last_message.content:
        # Any agent decided the work is done
        return "__end__"
    else:
        return "continue"



## Workflow Graph
workflow = StateGraph(AgentState)

# add agent nodes
for name, node in agent_nodes.items():
    workflow.add_node(name, node)
    
workflow.add_node("call_tool", tool_node)


workflow.add_conditional_edges(
    "analyst",
    router,
    {"continue": "data_collector", "call_tool": "call_tool", "__end__": END}
)

workflow.add_conditional_edges(
    "data_collector",
    router,
    {"call_tool": "call_tool", "continue": "reporter", "__end__": END}
)

workflow.add_conditional_edges(
    "reporter",
    router,
    {"continue": "data_collector", "call_tool": "call_tool", "__end__": END}
)

workflow.add_conditional_edges(
    "call_tool",
    # Each agent node updates the 'sender' field
    # the tool calling node does not, meaning
    # this edge will route back to the original agent
    # who invoked the tool
    lambda x: x["sender"],
    {name:name for name in agent_name},
)
workflow.add_edge(START, "analyst")
graph = workflow.compile()

# %%
# from IPython.display import Image, display

# try:
#     display(Image(graph.get_graph(xray=True).draw_mermaid_png()))
# except Exception:
#     # This requires some extra dependencies and is optional
#     pass

# %%
# question = "วิเคราะห์คู่แข่งของร้านเบเกอรี่ใกล้ตลาดจตุจักร"

# graph = workflow.compile()

# events = graph.stream(
#     {
#         "messages": [
#             HumanMessage(
#                 question
#             )
#         ],
#         "chat_history": [    
#         ]
#     },
#     # Maximum number of steps to take in the graph
#     {"recursion_limit": 50},
#     debug=True
# )
# for s in events:
#     # print(s)
#     a = list(s.items())[0]
#     a[1]['messages'][0].pretty_print()

# %%
chat_history=[]
def submitUserMessage(user_input: str) -> str:
    graph = workflow.compile()

    events = graph.stream(
        {
            "messages": [
                HumanMessage(
                    user_input
                )
            ],
            "chat_history": [    
            ]
        },
        # Maximum number of steps to take in the graph
        {"recursion_limit": 20},
    )
    
    events = [e for e in events]
    
    response = list(events[-1].values())[0]["messages"][0]
    response = response.content
    response = response.replace("%SIjfE923hf", "")
    
    chat_history.append(HumanMessage(user_input))
    chat_history.append(AIMessage(response))
    
    return response


question = "hello my frend"
submitUserMessage(question)


