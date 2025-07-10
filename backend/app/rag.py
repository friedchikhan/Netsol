# import fitz 
# def extract_pdf_text(pdf_path: str) -> str:
#     doc = fitz.open(pdf_path)
#     text = ""
#     for page in doc:
#         text += page.get_text()
#     doc.close()
#     return text

# pdf_text = extract_pdf_text("/Users/faizanalikhan/netsol/NETSOL-2024.pdf")

# from langchain.text_splitter import RecursiveCharacterTextSplitter

# splitter = RecursiveCharacterTextSplitter(
#     chunk_size=1000,
#     chunk_overlap=150
# )

# chunks = splitter.split_text(pdf_text)

# from langchain.embeddings import OpenAIEmbeddings

# embedding_model = OpenAIEmbeddings()
# embeddings = embedding_model.embed_documents(chunks)

# from pymongo import MongoClient
# import numpy as np

# client = MongoClient("mongodb://localhost:27017")
# db = client["netsoltask"]
# collection = db["rag_chunks"]

# # convert list -> string or store as binary if needed
# for chunk, vector in zip(chunks, embeddings):
#     collection.insert_one({
#         "text": chunk,
#         "embedding": vector  # or list(vector)
#     })
    
# from sklearn.metrics.pairwise import cosine_similarity

# def retrieve_top_chunks(query, k=3):
#     query_vector = embedding_model.embed_query(query)
#     docs = list(collection.find({}))

#     scored = []
#     for doc in docs:
#         score = cosine_similarity(
#             [query_vector],
#             [doc["embedding"]]
#         )[0][0]
#         scored.append((score, doc["text"]))

#     scored.sort(reverse=True)
#     return [text for _, text in scored[:k]]

import os
import fitz
from pymongo import MongoClient
from sklearn.metrics.pairwise import cosine_similarity
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate

MONGO_URI    = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
PDF_PATH     = os.getenv("NETSOL_PDF_PATH", "/Users/faizanalikhan/netsol/NETSOL-2024.pdf")
DB_NAME      = "netsoltask"
COLL_NAME    = "rag_chunks"
MODEL_NAME   = "gpt-4.1-nano"

client     = MongoClient(MONGO_URI)
collection = client[DB_NAME][COLL_NAME]

embedder  = OpenAIEmbeddings()
rag_llm    = ChatOpenAI(model_name=MODEL_NAME, temperature=0.0)

def extract_pdf_text(path: str) -> str:
    doc, text = fitz.open(path), ""
    for p in doc: text += p.get_text()
    doc.close()
    return text


def chunk_text(text: str):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    return splitter.split_text(text)

def index_pdf_to_mongodb(path: str = PDF_PATH):
    
    txt    = extract_pdf_text(path)
    chunks = chunk_text(txt)
    vecs   = embedder.embed_documents(chunks)
    for c, v in zip(chunks, vecs):
        collection.insert_one({"text": c, "embedding": v})
    print(f"Indexed {len(chunks)} chunks")

def retrieve_top_chunks(q: str, k: int = 5) -> list[str]:
    q_vec = embedder.embed_query(q)
    docs  = list(collection.find({}, {"text":1, "embedding":1}))
    scored = [
      ( cosine_similarity([q_vec], [d["embedding"]])[0][0], d["text"] )
      for d in docs
    ]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [t for _, t in scored[:k]]

def generate_rag_answer(q: str) -> str:
    ctx = "\n\n---\n\n".join(retrieve_top_chunks(q))
    prompt = PromptTemplate.from_template(
        """Answer using ONLY the context below. If it’s not in the context, say "I don’t know."

Context:
{context}

Question:
{question}

Answer:"""
    )
    full = prompt.format(context=ctx, question=q)
    return rag_llm.predict(full)

def is_netsol_query(q: str) -> bool:
    kws = ["netsol","2024","financial","revenue","profit","loss","income","balance sheet"]
    return any(kw in q.lower() for kw in kws)


print("Total chunks in MongoDB:", collection.count_documents({}))

tops = retrieve_top_chunks("what countries does Netsol operate in", k=5)
for i, chunk in enumerate(tops, 1):
    print(f"#{i}:", chunk[:200].replace("\n"," "), "…")

if __name__ == "__main__" or collection.count_documents({}) == 0:
    print("⚙️  No RAG chunks found – indexing NETSOL-2024.pdf now…")
    index_pdf_to_mongodb()
    print("✅  Finished indexing.")