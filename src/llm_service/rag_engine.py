"""
RAG Engine - Bonus Feature 4
DashScope Embedding + FAISS vector search for knowledge-enhanced AI chat.
"""
import os
import json
import logging
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAG_DATA_PATH = os.path.join(PROJECT_ROOT, "data", "rag_knowledge.json")
EMBEDDING_CACHE_PATH = os.path.join(PROJECT_ROOT, "data", "rag_embeddings.npy")

def build_knowledge_base(csv_path=None):
    """Build RAG knowledge base from job statistics."""
    if csv_path is None:
        csv_path = os.path.join(PROJECT_ROOT, "data", "processed", "cleaned_jobs.csv")
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    knowledge = []
    NL = chr(10)

    # 1. Overall
    knowledge.append({"title": "Overall Overview", "content": f"Database has {len(df)} jobs, {df[chr(99)+chr(105)+chr(116)+chr(121)].nunique()} cities, {df[chr(99)+chr(111)+chr(109)+chr(112)+chr(97)+chr(110)+chr(121)+chr(70)+chr(117)+chr(108)+chr(108)+chr(78)+chr(97)+chr(109)+chr(101)].nunique()} companies, {df[chr(107)+chr(101)+chr(121)+chr(119)+chr(111)+chr(114)+chr(100)].nunique()} categories. Avg salary {df[chr(115)+chr(97)+chr(108)+chr(97)+chr(114)+chr(121)+chr(95)+chr(97)+chr(118)+chr(103)].mean():.1f}K, median {df[chr(115)+chr(97)+chr(108)+chr(97)+chr(114)+chr(121)+chr(95)+chr(97)+chr(118)+chr(103)].median():.1f}K."})
