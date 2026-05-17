import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import inngest
import inngest.fast_api
from dotenv import load_dotenv
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from pathlib import Path
import hashlib
import uuid

load_dotenv()

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn")

# إنشاء عميل Inngest
inngest_client = inngest.Inngest(
    app_id="rag_app",
    logger=logger,
    is_production=False,
)

# ============================================================
# نماذج البيانات
# ============================================================
class QueryRequest(BaseModel):
    question: str
    top_k: int = 5

class IngestRequest(BaseModel):
    pdf_path: str
    source_id: Optional[str] = None

# ============================================================
# دوال مساعدة بسيطة (بدون مكتبات خارجية معقدة)
# ============================================================

def simple_embed(text: str, size: int = 20) -> List[float]:
    """إنشاء متجه بسيط من النص (يعمل بدون OpenAI)"""
    if not text:
        return [0.0] * size
    
    hash_obj = hashlib.md5(text.encode())
    hex_digest = hash_obj.hexdigest()
    vector = []
    
    for i in range(0, min(40, size * 2), 2):
        try:
            val = int(hex_digest[i:i+2], 16) / 255.0
            vector.append(val)
        except:
            vector.append(0.0)
    
    while len(vector) < size:
        vector.append(0.0)
    
    return vector[:size]

def extract_text_from_pdf(pdf_path: str) -> str:
    """استخراج النص من ملف PDF"""
    try:
        from pypdf import PdfReader
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except ImportError:
        print("⚠️ pypdf غير مثبت، يتم استخدام نص تجريبي")
        return "هذا نص تجريبي من ملف PDF. قم بتثبيت pypdf للحصول على النص الحقيقي."

def chunk_text(text: str, chunk_size: int = 500) -> List[str]:
    """تقطيع النص إلى أجزاء"""
    if not text:
        return []
    
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size):
        chunk = ' '.join(words[i:i+chunk_size])
        chunks.append(chunk)
    
    return chunks

# ============================================================
# تخزين بسيط في الذاكرة (بدلاً من Qdrant)
# ============================================================
pdf_storage = {}

# ============================================================
# دوال Inngest
# ============================================================

@inngest_client.create_function(
    fn_id="rag_ingest_pdf",
    trigger="rag/ingest_pdf",
)
async def rag_ingest_pdf(ctx) -> Dict[str, Any]:
    """استقبال ملف PDF ومعالجته"""
    print("=" * 50)
    print("📄 تم استلام حدث Ingest PDF")
    print("=" * 50)
    
    return {
        "status": "success",
        "message": "تم استلام PDF بنجاح",
    }

@inngest_client.create_function(
    fn_id="rag_query_pdf_ai",
    trigger="rag/query_pdf_ai",
)
async def rag_query_pdf_ai(ctx) -> Dict[str, Any]:
    """الاستعلام عن PDFs"""
    print("=" * 50)
    print("❓ تم استلام حدث استعلام")
    print("=" * 50)
    
    return {
        "answer": "تم استلام سؤالك. جاري المعالجة...",
        "sources": [],
    }

# ============================================================
# تطبيق FastAPI
# ============================================================

app = FastAPI(title="RAG System")

# إضافة CORS للسماح لـ Streamlit بالتواصل
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# نقاط النهاية (Endpoints)
# ============================================================

@app.get("/")
def home() -> Dict[str, Any]:
    return {
        "status": "ok",
        "message": "RAG API is running",
        "endpoints": {
            "health": "/health",
            "query": "/query (POST)",
            "ingest": "/ingest (POST)",
            "process-uploads": "/process-uploads (POST)",
            "uploads": "/uploads (GET)"
        }
    }

@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "healthy"}

@app.post("/ingest")
async def ingest_endpoint(request: IngestRequest) -> Dict[str, Any]:
    """معالجة وتخزين ملف PDF"""
    pdf_path = request.pdf_path
    source_id = request.source_id or Path(pdf_path).name
    
    print("=" * 50)
    print(f"📄 معالجة PDF: {pdf_path}")
    print("=" * 50)
    
    if not Path(pdf_path).exists():
        return {
            "status": "error",
            "message": f"الملف غير موجود: {pdf_path}"
        }
    
    try:
        text = extract_text_from_pdf(pdf_path)
        
        if not text or len(text) < 10:
            return {
                "status": "error",
                "message": "لم يتم استخراج نص من PDF. تأكد من أن الملف يحتوي على نص قابل للقراءة."
            }
        
        chunks = chunk_text(text, chunk_size=500)
        
        if not chunks:
            return {
                "status": "error",
                "message": "لم يتم تقطيع النص إلى أجزاء"
            }
        
        vectors = []
        for chunk in chunks:
            vec = simple_embed(chunk)
            vectors.append(vec)
        
        pdf_storage[source_id] = {
            "chunks": chunks,
            "vectors": vectors,
            "pdf_path": pdf_path,
            "num_chunks": len(chunks)
        }
        
        print(f"✅ تم تخزين {len(chunks)} جزء من {source_id}")
        
        return {
            "status": "success",
            "message": "تمت معالجة PDF وتخزينه بنجاح",
            "source_id": source_id,
            "num_chunks": len(chunks)
        }
        
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

@app.post("/process-uploads")
async def process_all_uploads() -> Dict[str, Any]:
    """معالجة جميع ملفات PDF في مجلد uploads تلقائياً"""
    uploads_dir = Path("uploads")
    results = []
    
    if not uploads_dir.exists():
        return {"status": "error", "message": "مجلد uploads غير موجود"}
    
    for pdf_file in uploads_dir.glob("*.pdf"):
        try:
            text = extract_text_from_pdf(str(pdf_file))
            chunks = chunk_text(text, chunk_size=500)
            vectors = [simple_embed(chunk) for chunk in chunks]
            
            source_id = pdf_file.name
            pdf_storage[source_id] = {
                "chunks": chunks,
                "vectors": vectors,
                "pdf_path": str(pdf_file),
                "num_chunks": len(chunks)
            }
            results.append({"file": source_id, "status": "success", "chunks": len(chunks)})
            print(f"✅ تم معالجة {source_id}")
        except Exception as e:
            results.append({"file": pdf_file.name, "status": "error", "error": str(e)})
    
    return {"status": "done", "results": results}

@app.post("/query")
async def query_endpoint(request: QueryRequest) -> Dict[str, Any]:
    """البحث والإجابة على السؤال"""
    question = request.question
    top_k = request.top_k
    
    print("=" * 50)
    print(f"❓ سؤال: {question}")
    print(f"🔢 عدد النتائج: {top_k}")
    print("=" * 50)
    
    if not pdf_storage:
        return {
            "answer": "⚠️ لا توجد ملفات PDF مخزنة. قم برفع ملف PDF أولاً باستخدام نقطة /ingest أو /process-uploads",
            "sources": [],
            "num_contexts": 0
        }
    
    query_vector = simple_embed(question)
    all_results = []
    
    for source_id, data in pdf_storage.items():
        chunks = data["chunks"]
        vectors = data["vectors"]
        
        for i, vec in enumerate(vectors):
            similarity = sum(a * b for a, b in zip(query_vector, vec))
            all_results.append({
                "similarity": similarity,
                "text": chunks[i],
                "source": source_id,
                "index": i
            })
    
    all_results.sort(key=lambda x: x["similarity"], reverse=True)
    top_results = all_results[:top_k]
    
    if not top_results:
        return {
            "answer": f"❌ لم يتم العثور على إجابة لسؤالك: '{question}'",
            "sources": [],
            "num_contexts": 0
        }
    
    context_parts = []
    sources = set()
    
    for result in top_results:
        if result["similarity"] > 0.1:
            context_parts.append(result["text"])
            sources.add(result["source"])
    
    if not context_parts:
        return {
            "answer": f"❓ لم يتم العثور على معلومات ذات صلة بسؤالك: '{question}'",
            "sources": [],
            "num_contexts": 0
        }
    
    context = "\n\n---\n\n".join(context_parts)
    
    answer = f"""📄 **الإجابة المستخلصة من ملفات PDF:**

{context[:1500]}

---
✨ **ملخص:** تم العثور على {len(top_results)} جزء ذي صلة بسؤالك.
📊 **درجة التشابه الأفضل:** {top_results[0]['similarity']:.3f}
📁 **المصادر:** {', '.join(sources)}"""

    return {
        "answer": answer,
        "sources": list(sources),
        "num_contexts": len(top_results),
        "top_similarity": top_results[0]["similarity"]
    }

@app.get("/uploads")
def list_uploads() -> Dict[str, Any]:
    """عرض قائمة الملفات المخزنة"""
    uploads_dir = Path("uploads")
    files = []
    
    if uploads_dir.exists():
        files = [f.name for f in uploads_dir.iterdir() if f.is_file()]
    
    return {
        "stored_pdfs": list(pdf_storage.keys()),
        "uploaded_files": files,
        "count": len(pdf_storage)
    }

@app.delete("/uploads/{source_id}")
def delete_upload(source_id: str) -> Dict[str, Any]:
    """حذف ملف مخزن"""
    if source_id in pdf_storage:
        del pdf_storage[source_id]
        return {"status": "success", "message": f"تم حذف {source_id}"}
    return {"status": "error", "message": "الملف غير موجود"}

# ============================================================
# ربط Inngest مع FastAPI
# ============================================================
inngest.fast_api.serve(app, inngest_client, [rag_ingest_pdf, rag_query_pdf_ai])

# ============================================================
# تشغيل مباشر
# ============================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)