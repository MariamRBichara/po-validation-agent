"""Deterministic LangGraph workflow (no OpenAI calls or API keys)."""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from extraction import extract_document
from validation import validate

class State(TypedDict, total=False):
    files: list
    guideline: dict
    docs: list
    results: list

def extract_node(state: State):
    return {'docs': [extract_document(name, content) for name, content in state['files']]}

def validate_node(state: State):
    return {'results': validate(state['docs'], state['guideline'])}

def run(files, guideline):
    graph = StateGraph(State)
    graph.add_node('extract', extract_node)
    graph.add_node('validate', validate_node)
    graph.add_edge(START, 'extract')
    graph.add_edge('extract', 'validate')
    graph.add_edge('validate', END)
    return graph.compile().invoke({'files': files, 'guideline': guideline})
