from openai import OpenAI
from llama_index.readers.file import PDFReader
from llama_index.core.node_parser import SentenceSplitter
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

client = OpenAI()
EMBED_MODEL = "text-embedding-3-large"
EMBED_DIM = 3072

splitter = SentenceSplitter(chunk_size=1000, chunk_overlap=200)

def load_and_chunk_pdf(path: str):
    """تحميل ملف PDF وتقطيعه إلى أجزاء"""
    # تحويل المسار إلى Path object
    file_path = Path(path)
    
    # التحقق من وجود الملف
    if not file_path.exists():
        raise FileNotFoundError(f"الملف غير موجود: {path}")
    
    # تحميل PDF
    docs = PDFReader().load_data(file=file_path)
    
    # استخراج النصوص
    texts = [d.text for d in docs if getattr(d, "text", None)]
    
    # تقطيع النصوص
    chunks = []
    for t in texts:
        chunks.extend(splitter.split_text(t))
    
    print(f"✅ تم تحميل {len(docs)} صفحة وتقطيعها إلى {len(chunks)} جزء")
    return chunks

def embed_texts(texts: list[str]) -> list[list[float]]:
    """تحويل النصوص إلى متجهات (embeddings)"""
    response = client.embeddings.create(
        model=EMBED_MODEL,
        input=texts,
    )
    embeddings = [item.embedding for item in response.data]
    print(f"✅ تم إنشاء {len(embeddings)} متجه")
    return embeddings

# دالة إضافية لمعالجة PDF كاملة
def process_pdf(file_path: str):
    """معالجة كاملة: تحميل PDF + تقطيع + إنشاء متجهات"""
    print(f"📄 بدء معالجة: {file_path}")
    
    # 1. تحميل وتقطيع PDF
    chunks = load_and_chunk_pdf(file_path)
    
    # 2. إنشاء متجهات للنصوص
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
        return None

# اختبار الكود
if __name__ == "__main__":
    # مثال للاختبار
    result = process_pdf("example.pdf")
    if result:
        print(f"\n📊 النتائج:")
        print(f"  - عدد الأجزاء: {result['num_chunks']}")
        print(f"  - حجم المتجه: {result['embedding_dim']}")