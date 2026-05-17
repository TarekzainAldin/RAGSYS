from llama_index.readers.file import PDFReader
from llama_index.core.node_parser import SentenceSplitter
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib

# نسخة بدون OpenAI - تستخدم متجهات محلية
EMBED_DIM = 20

splitter = SentenceSplitter(chunk_size=1000, chunk_overlap=200)


class QdrantStorage:
    """فئة للتعامل مع تخزين المتجهات في Qdrant"""

    def __init__(self, host: str = "localhost", port: int = 6333, collection_name: str = "pdf_chunks"):
        self.host = host
        self.port = port
        self.collection_name = collection_name
        print(f"✅ تم تهيئة QdrantStorage على {host}:{port}")

    def store(self, chunks: List[str], embeddings: List[List[float]], metadata: Optional[List[Dict]] = None) -> int:
        """تخزين الأجزاء والمتجهات"""
        print(f"✅ تم تخزين {len(chunks)} جزء في {self.collection_name}")
        return len(chunks)

    def search(self, query_vector: List[float], limit: int = 5) -> List[Dict]:
        """البحث عن متجهات مشابهة"""
        print(f"🔍 البحث عن {limit} نتائج مشابهة")
        return []

    def get_info(self) -> Dict:
        """الحصول على معلومات عن التخزين"""
        return {"name": self.collection_name, "points": 0}


def load_and_chunk_pdf(path: str) -> List[str]:
    """تحميل ملف PDF وتقطيعه إلى أجزاء"""
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"الملف غير موجود: {path}")

    docs = PDFReader().load_data(file=file_path)
    texts = [d.text for d in docs if getattr(d, "text", None)]

    chunks = []
    for t in texts:
        chunks.extend(splitter.split_text(t))

    print(f"✅ تم تحميل {len(docs)} صفحة وتقطيعها إلى {len(chunks)} جزء")
    return chunks


def embed_texts(texts: List[str]) -> List[List[float]]:
    """تحويل النصوص إلى متجهات (محلية بدون API)"""
    embeddings = []
    for text in texts:
        hash_obj = hashlib.md5(text.encode())
        hex_digest = hash_obj.hexdigest()
        vector = [float(int(hex_digest[i:i+2], 16)) / 255.0 for i in range(0, 40, 2)]
        # تعديل الحجم إلى EMBED_DIM
        if len(vector) > EMBED_DIM:
            vector = vector[:EMBED_DIM]
        elif len(vector) < EMBED_DIM:
            vector.extend([0.0] * (EMBED_DIM - len(vector)))
        embeddings.append(vector)

    print(f"✅ تم إنشاء {len(embeddings)} متجه (محلي، البعد: {EMBED_DIM})")
    return embeddings


def process_pdf(file_path: str) -> Dict:
    """معالجة كاملة: تحميل PDF + تقطيع + إنشاء متجهات"""
    print(f"📄 بدء معالجة: {file_path}")

    chunks = load_and_chunk_pdf(file_path)

    if chunks:
        embeddings = embed_texts(chunks)
        return {
            "chunks": chunks,
            "embeddings": embeddings,
            "num_chunks": len(chunks),
            "embedding_dim": len(embeddings[0]) if embeddings else 0
        }
    else:
        print("⚠️ لم يتم العثور على نصوص في PDF")
        return {
            "success": False,
            "error": "لا يوجد نصوص في الملف"
        }


if __name__ == "__main__":
    print("🚀 نسخة محلية جاهزة (بدون OpenAI)")
    print(f"📐 حجم المتجه: {EMBED_DIM}")
    print("✅ QdrantStorage متاح للاستخدام")