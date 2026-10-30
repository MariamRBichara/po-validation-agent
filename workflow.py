"""LangGraph workflow with a deterministic-only fallback for local tests."""
from typing import TypedDict
from extraction import extract_document
from validation import validate
from ai import assess
class State(TypedDict,total=False):
    files:list
    guideline:dict
    docs:list
    ai_key:str
    model:str
    llm_findings:dict
    results:list

def extract_node(s):return {'docs':[extract_document(n,b) for n,b in s['files']]}
def enrich_node(s):
    if not s.get('ai_key'):return {'llm_findings':{}}
    return {'llm_findings':assess(s['docs'],s['guideline'],s['ai_key'],s.get('model','gpt-4.1-mini'))}
def validate_node(s):return {'results':validate(s['docs'],s['guideline'],s.get('llm_findings'))}
def run(files,guideline,ai_key='',model='gpt-4.1-mini'):
    from langgraph.graph import StateGraph,START,END
    graph=StateGraph(State)
    for name,func in [('extract',extract_node),('enrich',enrich_node),('validate',validate_node)]:graph.add_node(name,func)
    graph.add_edge(START,'extract');graph.add_edge('extract','enrich');graph.add_edge('enrich','validate');graph.add_edge('validate',END)
    return graph.compile().invoke({'files':files,'guideline':guideline,'ai_key':ai_key,'model':model})
