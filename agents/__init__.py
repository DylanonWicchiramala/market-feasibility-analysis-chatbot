from deprecated import deprecated
from langchain_openai import ChatOpenAI
from tools import (
    get_geometric_data,
    restaurant_sale_projection,
    duckduckgo_search,
    find_place_from_text,
    all_tools,
)
from langchain_core.messages import (
    AIMessage, 
    BaseMessage,
    ToolMessage,
    SystemMessage
)
from langchain_core.tools.structured import StructuredTool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

import operator
from typing import Annotated, Sequence, TypedDict, List
from agents.prompt import *
import functools

llm = ChatOpenAI(
    model="gpt-4o-mini-2024-07-18", 
    temperature=0, 
    top_p=0, 
    )


## Define state ------------------------------------------------------------------------
# This defines the object that is passed between each node
# in the graph. We will create different nodes for each agent and tool
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    chat_history: List[BaseMessage]
    data_context: list[str] = []
    sender: str
    
    
def __bind(llm, tools:list, agent_prompt:str):
    """ create llm with SYSTEM_PROMPT and agent prompt, bind tools, return LLM agent with tools and prompts.
    """
    ## create agents with prompt and tools.
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                SYSTEM_PROMPT,
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    prompt = prompt.partial(system_message=agent_prompt)
    prompt = prompt.partial(agent_names=agent_names)
    
    # return llm without tools
    if tools:
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        #llm_with_tools = llm.bind(functions=[format_tool_to_openai_function(t) for t in tools])
        llm = llm.bind_tools(tools)
    else:
        prompt = prompt.partial(tool_names="<no available tools for you>")
    
    agent = prompt | llm
    return agent


## create agent node
@deprecated("old node build function, use other node build functions.")
def agent_node_build(state:AgentState, name:str, tools:StructuredTool, agent_prompt:str, llm:ChatOpenAI):
    """ bulid agent and agnet node to use in langgraph.
        use functools.partial to pass the argument `name`, `tools`, `llm`.
    """
    agent = __bind(llm, tools, agent_prompt=agent_prompt)
    
    result = agent.invoke(state)
    # We convert the agent output into a format that is suitable to append to the global state
    if isinstance(result, ToolMessage):
        pass
    else:
        chat_history = state.get('chat_history')
        result = AIMessage(**result.dict(exclude={"type", "name"}), name=name)
    return {
        "messages": [result],
        "chat_history" : chat_history,
        # Since we have a strict workflow, we can
        # track the sender so we know who to pass to next.
        "sender": name,
    }
    
    
def analyst_node_build(state:AgentState, name:str, tools:StructuredTool, agent_prompt:str, llm:ChatOpenAI):
    """ bulid agent and agnet node to use in langgraph.
        use functools.partial to pass the argument `name`, `tools`, `llm`.
    """
    agent = __bind(llm, tools, agent_prompt=agent_prompt)
    
    result = agent.invoke(state)
    # We convert the agent output into a format that is suitable to append to the global state
    if isinstance(result, ToolMessage):
        pass
    else:
        chat_history = state.get('chat_history')
        result = AIMessage(**result.dict(exclude={"type", "name"}), name=name)
    return {
        "messages": [result],
        "chat_history" : chat_history,
        # Since we have a strict workflow, we can
        # track the sender so we know who to pass to next.
        "sender": name,
    }
        
    
def data_collector_node_build(state:AgentState, name:str, tools:StructuredTool, agent_prompt:str, llm:ChatOpenAI):
    """ bulid agent and agnet node to use in langgraph.
        use functools.partial to pass the argument `name`, `tools`, `llm`.
    """
    agent = __bind(llm, tools, agent_prompt=agent_prompt)
    
    result = agent.invoke(state)

    chat_history = state.get('chat_history')
    result = AIMessage(**result.dict(exclude={"type", "name"}), name=name)
    
    data_context = state.get("data_context", "")
    return {
        "messages": [result],
        "chat_history" : chat_history,
        "data_context": data_context+"\n"+result.content,
        # Since we have a strict workflow, we can
        # track the sender so we know who to pass to next.
        "sender": name,
    }
        

def data_analyst_node_build(state:AgentState, name:str, tools:StructuredTool, agent_prompt:str, llm:ChatOpenAI):
    """ bulid agent and agnet node to use in langgraph.
        use functools.partial to pass the argument `name`, `tools`, `llm`.
    """
    agent = __bind(llm, tools, agent_prompt=agent_prompt)
    
    result = agent.invoke(state)

    chat_history = state.get('chat_history')
    result = AIMessage(**result.dict(exclude={"type", "name"}), name=name)
    return {
        "messages": [result],
        "chat_history" : chat_history,
        "data_context": state.get("data_context","n/a"),
        # Since we have a strict workflow, we can
        # track the sender so we know who to pass to next.
        "sender": name,
    }
        
    
def reporter_node_build(state:AgentState, name:str, tools:StructuredTool, agent_prompt:str, llm:ChatOpenAI):
    """ bulid agent and agnet node to use in langgraph.
        use functools.partial to pass the argument `name`, `tools`, `llm`.
    """
    data_context = state.get("data_context","n/a")
    agent_prompt = agent_prompt + "\ndata_context: \n" + data_context
    
    agent = __bind(llm, tools, agent_prompt=agent_prompt)
    
    result = agent.invoke(state)
    # We convert the agent output into a format that is suitable to append to the global state
    if isinstance(result, ToolMessage):
        assert True
        assert False
    else:
        chat_history = state.get('chat_history')
        result = AIMessage(**result.dict(exclude={"type", "name"}), name=name)
    return {
        "messages": [result],
        "chat_history" : chat_history,
        "data_context": [],
        # Since we have a strict workflow, we can
        # track the sender so we know who to pass to next.
        "sender": name,
    }


agent_names = ['analyst', 'data_collector', 'data_analyst', 'reporter']


analyst_node = functools.partial(
    analyst_node_build, 
    name='analyst',
    tools=[],
    agent_prompt=ANALYST_PROMPT,
    llm=llm
    )

data_collector_node = functools.partial(
    data_collector_node_build, 
    name='data_collector',
    tools=[restaurant_sale_projection, get_geometric_data, find_place_from_text, duckduckgo_search],
    agent_prompt=DATA_COLLECTOR_PROMPT,
    llm=llm
    )

data_analyst_node = functools.partial(
    data_analyst_node_build, 
    name='data_analyst',
    tools=[],
    agent_prompt=DATA_ANALYST_PROMPT,
    llm=llm
    )

reporter_node = functools.partial(
    reporter_node_build, 
    name='reporter',
    tools=[],
    agent_prompt=REPORTER_PROMPT,
    llm=llm
    )