from openai import OpenAI
from llama_index.readers.file import PDFReader
from llama_index.core.node_parser import SentenceSplitter
from dotenv import load_dotenv
from pathlib import Path
from typing import List

load_dotenv()

# تهيئة OpenAI
client = OpenAI()
EMBED_MODEL = "text-embedding-3-large"
EMBED_DIM = 3072

# تهيئة أداة التقطيع
splitter = SentenceSplitter(chunk_size=1000, chunk_overlap=200)

def load_and_chunk_pdf(path: str) -> List[str]:
    """
    تحميل ملف PDF وتقطيعه إلى أجزاء نصية
    
    Args:
        path (str): مسار ملف PDF
        
    Returns:
        List[str]: قائمة بالأجزاء النصية
    """
    # تحويل المسار إلى Path object وتحميل PDF
    docs = PDFReader().load_data(file=Path(path))
    
    # استخراج النصوص من الصفحات
    texts = [d.text for d in docs if getattr(d, "text", None)]
    
    # تقطيع كل نص إلى أجزاء
    chunks = []
    for t in texts:
        chunks.extend(splitter.split_text(t))
    
    print(f"✅ تم تحميل {len(docs)} صفحات وتقطيعها إلى {len(chunks)} جزء")
    return chunks

def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    تحويل النصوص إلى متجهات (Embeddings)
    
    Args:
        texts (List[str]): قائمة النصوص المراد تحويلها
        
    Returns:
        List[List[float]]: قائمة المتجهات
    """
    response = client.embeddings.create(
        model=EMBED_MODEL,
        input=texts,
    )
    embeddings = [item.embedding for item in response.data]
    print(f"✅ تم إنشاء {len(embeddings)} متجه (البعد: {len(embeddings[0])})")
    return embeddings

def process_pdf_complete(file_path: str) -> dict:
    """
    معالجة كاملة: تحميل PDF + تقطيع + إنشاء متجهات
    
    Args:
        file_path (str): مسار ملف PDF
        
    Returns:
        dict: نتائج المعالجة
    """
    print(f"📄 بدء معالجة: {file_path}")
    
    # 1. تحميل وتقطيع
    chunks = load_and_chunk_pdf(file_path)
    
    # 2. إنشاء المتجهات
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
        print("⚠️ لم يتم العثور على نصوص في PDF")
        return {"success": False, "error": "لا يوجد نصوص في الملف"}

# اختبار الكود
if __name__ == "__main__":
    # مثال: result = process_pdf_complete("example.pdf")
    print("الكود جاهز للاستخدام!")
    print(f"- نموذج التضمين: {EMBED_MODEL}")
    print(f"- حجم المتجه: {EMBED_DIM}")
    print(f"- حجم التقطيع: 1000 مع تداخل 200")