from llama_index.readers.file import PDFReader
from llama_index.core.node_parser import SentenceSplitter
from pathlib import Path
from typing import List
import hashlib

def load_and_chunk_pdf(path: str) -> List[str]:
    """تحميل ملف PDF وتقطيعه إلى أجزاء نصية"""
    docs = PDFReader().load_data(file=Path(path))
    texts = [d.text for d in docs if getattr(d, "text", None)]
    
    splitter = SentenceSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = []
    for t in texts:
        chunks.extend(splitter.split_text(t))
    
    print(f"✅ تم تحميل {len(docs)} صفحات وتقطيعها إلى {len(chunks)} جزء")
    return chunks

def embed_texts(texts: List[str]) -> List[List[float]]:
    """تحويل النصوص إلى متجهات (Embeddings تجريبية محلية)"""
    embeddings = []
    for text in texts:
        hash_obj = hashlib.md5(text.encode())
        hex_digest = hash_obj.hexdigest()
        vector = [float(int(hex_digest[i:i+2], 16)) / 255.0 for i in range(0, 40, 2)]
        embeddings.append(vector)
    
    print(f"✅ تم إنشاء {len(embeddings)} متجه تجريبي")
    return embeddings

def process_pdf_complete(file_path: str) -> dict:
    """معالجة كاملة: تحميل PDF + تقطيع + إنشاء متجهات"""
    print(f"📄 بدء معالجة: {file_path}")
    
    chunks = load_and_chunk_pdf(file_path)
    
    if chunks:
        embeddings = embed_texts(chunks)
        return {
            "success": True,
            "num_chunks": len(chunks),
            "chunks": chunks,
            "embeddings": embeddings,
            "embedding_dim": len(embeddings[0])
        }
    else:
        return {"success": False, "error": "لا يوجد نصوص في الملف"}
    
    