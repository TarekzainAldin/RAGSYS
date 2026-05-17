import logging
from fastapi import FastAPI
import inngest
import inngest.fast_api
from dotenv import load_dotenv

load_dotenv()

# 1. إنشاء عميل Inngest
inngest_client = inngest.Inngest(
    app_id="rag_app",
    logger=logging.getLogger("uvicorn"),
    is_production=False,
)

# 2. تعريف الدالة (يجب أن يكون هناك دالة بعد الديكوريتور مباشرة)
@inngest_client.create_function(
    fn_id="rag_ingest_pdf",           # ✅ تجنب استخدام النقطتين :
    trigger=inngest.TriggerEvent(event="rag/ingest_pdf"),  # ✅ استخدم trigger وليس event
)
async def ingest_pdf(ctx: inngest.Context) -> dict:   # ✅ هذه هي الدالة المطلوبة
    """معالجة ملف PDF"""
    data = ctx.event.data
    print(f"📄 تم استلام PDF: {data}")
    return {"status": "success", "data": data}

# 3. إنشاء تطبيق FastAPI
app = FastAPI(title="RAG System")

# 4. إضافة المسارات (routes)
@app.get("/")
def home():
    return {"status": "ok", "message": "RAG API is running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

# 5. ربط Inngest مع FastAPI (تصحيح: functions= وليس functions:)
inngest.fast_api.serve(app, inngest_client, functions=[ingest_pdf])