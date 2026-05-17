import streamlit as st
import requests
from pathlib import Path
import time
from dotenv import load_dotenv
import json

load_dotenv()

st.set_page_config(page_title="RAG Ingest PDF", page_icon="📄", layout="centered")

# عنوان الخدمات
INNGEST_URL = "http://localhost:8288/api/events"
FASTAPI_URL = "http://localhost:8000"

# تخزين الإجابات في session state
if 'answers' not in st.session_state:
    st.session_state.answers = []
if 'last_question' not in st.session_state:
    st.session_state.last_question = ""

def save_uploaded_pdf(file) -> Path:
    """حفظ ملف PDF مرفوع"""
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    file_path = uploads_dir / file.name
    file_path.write_bytes(file.getbuffer())
    return file_path

def send_rag_ingest_event(pdf_path: Path) -> tuple[bool, str]:
    """إرسال حدث ingest إلى Inngest"""
    try:
        response = requests.post(
            INNGEST_URL,
            json={
                "name": "rag/ingest_pdf",
                "data": {
                    "pdf_path": str(pdf_path.resolve()),
                    "source_id": pdf_path.name,
                }
            },
            timeout=10
        )
        if response.status_code in [200, 201, 202]:
            return True, "تم الإرسال بنجاح"
        else:
            return False, f"خطأ {response.status_code}"
    except Exception as e:
        return False, str(e)

def send_rag_query_event(question: str, top_k: int) -> tuple[bool, str, dict]:
    """إرسال حدث استعلام إلى Inngest وجلب الإجابة"""
    try:
        # محاولة الحصول على إجابة مباشرة من FastAPI أولاً
        response = requests.post(
            f"{FASTAPI_URL}/query",
            json={"question": question, "top_k": top_k},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return True, "تم الحصول على الإجابة", data
        else:
            # إذا فشل، أرسل إلى Inngest
            response = requests.post(
                INNGEST_URL,
                json={
                    "name": "rag/query_pdf_ai",
                    "data": {
                        "question": question,
                        "top_k": top_k,
                    }
                },
                timeout=10
            )
            if response.status_code in [200, 201, 202]:
                return True, "تم إرسال السؤال (المعالجة في الخلفية)", {"answer": "جاري المعالجة...", "sources": []}
            else:
                return False, f"خطأ {response.status_code}", {}
                
    except Exception as e:
        return False, str(e), {}

def get_direct_answer(question: str, top_k: int = 5) -> dict:
    """الحصول على إجابة مباشرة من FastAPI"""
    try:
        response = requests.post(
            f"{FASTAPI_URL}/query",
            json={"question": question, "top_k": top_k},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"answer": "لم يتم الحصول على إجابة", "sources": []}
    except:
        return {"answer": "لا يمكن الاتصال بالخادم", "sources": []}

# ============ واجهة المستخدم ============

st.title("📄 Upload a PDF to Ingest")

uploaded = st.file_uploader("Choose a PDF", type=["pdf"], accept_multiple_files=False)

if uploaded is not None:
    with st.spinner("Uploading and triggering ingestion..."):
        path = save_uploaded_pdf(uploaded)
        success, message = send_rag_ingest_event(path)
        time.sleep(0.3)
    
    if success:
        st.success(f"✅ Triggered ingestion for: {path.name}")
    else:
        st.error(f"❌ {message}")
    
    st.caption("You can upload another PDF if you like.")

st.divider()

st.title("💬 Ask a question about your PDFs")

# نموذج السؤال
with st.form("rag_query_form"):
    question = st.text_input("Your question", key="question_input")
    top_k = st.number_input("How many chunks to retrieve", min_value=1, max_value=20, value=5, step=1)
    submitted = st.form_submit_button("Ask", type="primary")

    if submitted and question.strip():
        st.session_state.last_question = question
        
        with st.spinner("🔍 جاري البحث عن إجابة..."):
            # الحصول على الإجابة مباشرة
            answer_data = get_direct_answer(question.strip(), int(top_k))
            
            # حفظ في session state
            st.session_state.answers.insert(0, {
                "question": question,
                "answer": answer_data.get("answer", "لا توجد إجابة"),
                "sources": answer_data.get("sources", []),
                "num_contexts": answer_data.get("num_contexts", top_k),
                "timestamp": time.strftime("%H:%M:%S")
            })

# ============ عرض الإجابات ============

if st.session_state.answers:
    st.divider()
    st.subheader("📝 الإجابات")
    
    for i, ans in enumerate(st.session_state.answers):
        with st.container():
            st.markdown(f"### ❓ {ans['question']}")
            st.markdown(f"**📌 الإجابة:**")
            st.markdown(f"> {ans['answer']}")
            
            if ans.get('sources'):
                st.markdown(f"**📚 المصادر:**")
                for src in ans['sources']:
                    st.markdown(f"- {src}")
            
            if ans.get('num_contexts'):
                st.caption(f"📊 عدد الأجزاء المسترجعة: {ans['num_contexts']}")
            
            st.caption(f"🕐 {ans['timestamp']}")
            st.divider()

# ============ حالة الخدمات ============
with st.expander("ℹ️ System Status"):
    try:
        r = requests.get(f"{FASTAPI_URL}/health", timeout=2)
        if r.status_code == 200:
            st.success("✅ FastAPI: يعمل على المنفذ 8000")
        else:
            st.error("❌ FastAPI: لا يعمل")
    except:
        st.error("❌ FastAPI: لا يعمل")
    
    try:
        r = requests.get("http://localhost:8288/health", timeout=2)
        if r.status_code == 200:
            st.success("✅ Inngest: يعمل على المنفذ 8288")
        else:
            st.error("❌ Inngest: لا يعمل")
    except:
        st.error("❌ Inngest: لا يعمل")
    
    st.info(f"📁 مسار التحميل: {Path('uploads').absolute()}")