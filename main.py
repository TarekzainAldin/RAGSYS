import logging
from fastapi import FastAPI
import inngest
import inngest.fast_api
from dotenv import load_dotenv

load_dotenv()

inngest_client = inngest.Inngest(
    app_id="rag_app",
    logger=logging.getLogger("uvicorn"),
)

@inngest_client.create_function(
    fn_id="rag_ingest_pdf",
    trigger=inngest.TriggerEvent(event="rag/ingest_pdf")# type: ignore
)
def ingest_pdf(ctx):
    # استخدم try/except لتجنب أي أخطاء
    try:
        data = ctx.event.data
    except:
        data = {}
    print(f"📄 تم استلام: {data}")
    return {"status": "success"}

app = FastAPI()

@app.get("/")
def home():
    return {"status": "ok"}

@app.get("/about")
def about():
    """معلومات عن التطبيق والمطور"""
    return {
        "app_name": "RAG System",
        "developer": "Tarek Zain Al-Din",
        "version": "1.0.0",
        "description": "نظام لمعالجة واستيعاب ملفات PDF باستخدام RAG"
    }
inngest.fast_api.serve(app, inngest_client, [ingest_pdf])