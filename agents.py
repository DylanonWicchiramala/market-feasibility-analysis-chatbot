import operator
from typing import Annotated, Sequence, TypedDict, List
from langchain_core.messages import (
    AIMessage, 
    HumanMessage,
    BaseMessage,
)
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from prompt import system_prompt

## Create agents ------------------------------------------------------------------------
def create_agent(llm, tools, system_message: str):
    # memory = ConversationBufferMemory(memory_key='chat_history', return_messages=False)
    """Create an agent."""
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                system_prompt,
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    prompt = prompt.partial(system_message=system_message)
    prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
    #llm_with_tools = llm.bind(functions=[format_tool_to_openai_function(t) for t in tools])
    llm_with_tools = llm.bind_tools(tools)
    agent = prompt | llm_with_tools
    return agent


## Define state ------------------------------------------------------------------------
# This defines the object that is passed between each node
# in the graph. We will create different nodes for each agent and tool
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    chat_history: List[BaseMessage]
    sender: str