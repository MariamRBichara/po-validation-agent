"""In-memory ingestion. The uploaded evidence is never persisted by the app."""
import io
import re
from pathlib import Path
import fitz
from docx import Document

EXTS = {'.pdf','.docx','.txt','.csv','.xlsx','.png','.jpg','.jpeg'}

def extract_document(filename: str, content: bytes) -> dict:
    ext = Path(filename).suffix.lower()
    if ext not in EXTS:
        raise ValueError(f"Unsupported type {ext}. Accepted: {', '.join(sorted(EXTS))}")
    pages = []
    if ext == '.pdf':
        with fitz.open(stream=content, filetype='pdf') as d:
            for i,p in enumerate(d):
                pages.append({'page':i+1,'text':p.get_text(sort=True),'image': p.get_pixmap(matrix=fitz.Matrix(1.5,1.5)).tobytes('png') if len(p.get_text().strip())<100 else None})
    elif ext == '.docx':
        d=Document(io.BytesIO(content))
        lines=[p.text for p in d.paragraphs if p.text.strip()]
        for t in d.tables:
            for row in t.rows:
                lines.append(' | '.join(cell.text.replace('\n',' ') for cell in row.cells))
        pages=[{'page':1,'text':'\n'.join(lines),'image':None}]
    elif ext == '.xlsx':
        from openpyxl import load_workbook
        w=load_workbook(io.BytesIO(content),read_only=True,data_only=True)
        for sheet in w:
            rows=[]
            for row in sheet.iter_rows(max_row=2000,max_col=50,values_only=True):
                if any(x is not None for x in row): rows.append(' | '.join('' if x is None else str(x) for x in row))
            pages.append({'page':sheet.title,'text':'\n'.join(rows),'image':None})
        w.close()
    elif ext in ('.png','.jpg','.jpeg'):
        pages=[{'page':1,'text':'','image':content}]
    else:
        pages=[{'page':1,'text':content.decode('utf-8-sig',errors='replace'),'image':None}]
    text='\n'.join(f"[Page {p['page']}]\n{p['text']}" for p in pages)
    return {'name':filename,'pages':pages,'text':text,'kind':classify(text,filename)}

def classify(text,filename=''):
    t=(text+' '+filename).lower()
    if ('requisitioning bu' in t or 'requisition amount' in t): return 'requisition'
    if ('purchase order number' in t or ('purchase order' in t and 'bill to' in t)): return 'purchase_order'
    if ('quote number' in t or 'quotation' in t or 'proposal is valid until' in t): return 'quotation'
    if 'gold order' in t and ('one-off charge' in t or 'order status' in t): return 'gold_order'
    if 'pr approval guideline' in t or ('pre-requisite' in t and 'fpc' in t): return 'guideline'
    return 'supporting_document'

def identify_refs(text):
    return {'po':list(dict.fromkeys(re.findall(r'\b\d{7}/[A-Z]{3}\b',text,re.I))),
            'quote':list(dict.fromkeys(re.findall(r'\bQ-\d{4,6}-\d\b',text,re.I))),
            'gold':list(dict.fromkeys(re.findall(r'\b10-\s*\d{6,8}\b',text,re.I))),
            'requisition':list(dict.fromkeys(re.sub(r'\s+','',''.join(x.split())) for x in re.findall(r'\b872[-\s]*\d{10}\b',text,re.I)))}
