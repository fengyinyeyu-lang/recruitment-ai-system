
import os
path = os.path.join('src', 'llm_service', 'rag_engine.py')
os.makedirs(os.path.dirname(path), exist_ok=True)

# Read the template content from a separate approach
content = []
content.append(chr(34)*3)
content.append('RAG Engine - Bonus Feature 4')
content.append('Uses DashScope Embedding + FAISS vector search for knowledge-enhanced AI chat.')
content.append(chr(34)*3)
content.append('import os, json, logging, numpy as np, pandas as pd')
content.append('logging.basicConfig(level=logging.INFO)')
content.append('PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), chr(46)+chr(46), chr(46)+chr(46)))')
content.append('RAG_DATA_PATH = os.path.join(PROJECT_ROOT, chr(100)+chr(97)+chr(116)+chr(97), chr(114)+chr(97)+chr(103)+chr(95)+chr(107)+chr(110)+chr(111)+chr(119)+chr(108)+chr(101)+chr(100)+chr(103)+chr(101)+chr(46)+chr(106)+chr(115)+chr(111)+chr(110))')

with open(path, chr(119), encoding=chr(117)+chr(116)+chr(102)+chr(45)+chr(56)) as f:
    f.write(chr(10).join(content))
print(chr(79)+chr(75))
