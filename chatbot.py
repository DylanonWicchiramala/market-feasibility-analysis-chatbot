# %%
import os
import utils

utils.load_env()
os.environ['LANGCHAIN_TRACING_V2'] = "true"

# %%
from langchain_core.messages import HumanMessage

# for llm model
from langchain_openai import ChatOpenAI
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from tools import find_place_from_text, nearby_search
from typing import Dict, List, Tuple
from langchain.agents import (
    AgentExecutor,
)
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain_community.chat_models import ChatOpenAI
from langchain_community.tools.convert_to_openai import format_tool_to_openai_function
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# Bind the tools to the model
tools = [find_place_from_text, nearby_search]  # Include both tools if needed

llm = ChatOpenAI(model="gpt-4o-mini")

llm_with_tools = llm.bind(functions=[format_tool_to_openai_function(t) for t in tools])

def _format_chat_history(chat_history: List[Tuple[str, str]]):
    buffer = []
    for human, ai in chat_history:
        buffer.append(HumanMessage(content=human))
        buffer.append(AIMessage(content=ai))
    return buffer

meta = utils.load_agent_meta()[0]

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", meta['prompt']),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

agent = (
    {
        "input": lambda x: x["input"],
        "chat_history": lambda x: _format_chat_history(x["chat_history"]),
        "agent_scratchpad": lambda x: format_to_openai_function_messages(
            x["intermediate_steps"]
        ),
    }
    | prompt
    | llm_with_tools
    | OpenAIFunctionsAgentOutputParser()
)


class AgentInput(BaseModel):
    input: str
    chat_history: List[Tuple[str, str]] = Field(
        ..., extra={"widget": {"type": "chat", "input": "input", "output": "output"}}
    )


agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True).with_types(
    input_type=AgentInput
)


# %%
def submitUserMessage(user_input: str) -> str:
    responce = agent_executor.invoke({"input": user_input, "chat_history": []})
    return responce["output"]

