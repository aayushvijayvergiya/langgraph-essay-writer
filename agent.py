from typing import TypedDict, Annotated, List

from langgraph.graph import END
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic.v1 import BaseModel

import prompts
from config import model, tavily
from prompts import PLAN_PROMPT


class AgentState(TypedDict):
    task: str
    plan: str
    draft: str
    critique: str
    content: str
    revision_number: int
    max_revisions: int

class Queries(BaseModel):
    queries: List[str]


def plan_node(state: AgentState):
    messages = [
        SystemMessage(content=PLAN_PROMPT),
        HumanMessage(content=state["task"])
    ]
    response = model.invoke(messages)

    return {"plan": response.content}


def research_plan_node(state: AgentState):
    queries = model.with_structured_output(Queries).invoke([
        SystemMessage(content=prompts.RESEARCH_PLAN_PROMPT),
        HumanMessage(content=state["task"])
    ])

    content = state["content"] or []
    for query in queries.queries:
        response = tavily.search(query=query, max_results=2)

        for r in response:
            if isinstance(r, dict) and "content" in r:
                content.append(r["content"])
            elif isinstance(r, str):
                content.append(r)
            else:
                content.append(str(r))

    return {"content": content}


def generation_node(state: AgentState):
    content = "\n\n".join(state["content"] or [])
    messages = [
        SystemMessage(content=prompts.WRITER_PROMPT.format(content=content)),
        HumanMessage(content=f"{state['task']}\n\nHere is my plan:\n\n{state['plan']}")
    ]
    response = model.invoke(messages)

    return {
        "draft": response.content,
        "revision_number": state.get("revision_number", 1) + 1
    }


def reflection_node(state: AgentState):
    messages = [
        SystemMessage(content=prompts.REFLECTION_PROMPT),
        HumanMessage(content=f"Here is my draft:\n\n{state['draft']}\n\n"
                             f"Here is my plan:\n\n{state['plan']}\n\n"
                             f"Here is my task:\n\n{state['task']}")
    ]
    response = model.invoke(messages)

    return {"critique": response.content}


def research_critique_node(state: AgentState):
    queries = model.with_structured_output(Queries).invoke([
        SystemMessage(content=prompts.RESEARCH_CRITIQUE_PROMPT),
        HumanMessage(content=f"Here is my critique:\n\n{state['critique']}\n\n"
                             f"Here is my draft:\n\n{state['draft']}\n\n"
                             f"Here is my plan:\n\n{state['plan']}\n\n"
                             f"Here is my task:\n\n{state['task']}")
    ])

    content = state["content"] or []
    for query in queries.queries:
        response = tavily.search(query=query, max_results=2)

        for r in response:
            if isinstance(r, dict) and "content" in r:
                content.append(r["content"])
            elif isinstance(r, str):
                content.append(r)
            else:
                content.append(str(r))

    return {"content": content}

def should_continue(state: AgentState):
    if state["revision_number"] > state["max_revisions"]:
        return END
    return "reflect"
