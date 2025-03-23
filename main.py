import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import create_engine, Column, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
from uuid import uuid4

from video_parser import get_transcript
from gpt_service import generate_blog

load_dotenv()

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"))
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# OAuth config (без server_metadata_url)
oauth = OAuth()
oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    access_token_url='https://oauth2.googleapis.com/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    api_base_url='https://www.googleapis.com/oauth2/v2/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
    client_kwargs={"scope": "email profile"}  # ✅ Без "openid"
)


# SQLite
Base = declarative_base()
engine = create_engine("sqlite:///generations.db")
SessionLocal = sessionmaker(bind=engine)

class Generation(Base):
    __tablename__ = "generations"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    email = Column(String)
    url = Column(String)
    result = Column(Text)

Base.metadata.create_all(bind=engine)

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    user = request.session.get("user")
    pdf_link = None
    md_link = None
    return templates.TemplateResponse("index.html", {"request": request, "user": user, "pdf_link": pdf_link, "md_link": md_link})

@app.get("/login")
async def login(request: Request):
    redirect_uri = "http://localhost:8000/auth"
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth")
async def auth(request: Request):
    token = await oauth.google.authorize_access_token(request)
    resp = await oauth.google.get('userinfo', token=token)
    user = resp.json()
    request.session["user"] = user
    return RedirectResponse(url="/")

@app.get("/logout")
def logout(request: Request):
    request.session.pop("user", None)
    return RedirectResponse("/")

@app.post("/generate", response_class=HTMLResponse)
async def generate(request: Request, url: str = Form(...), style: str = Form(...), language: str = Form(...), export_pdf: str = Form(None), export_md: str = Form(None)):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login")

    transcript = get_transcript(url)
    blog_post = transcript if style == "transcript" else generate_blog(transcript, style)

    db = SessionLocal()
    gen = Generation(email=user["email"], url=url, result=blog_post)
    db.add(gen)
    db.commit()
    db.close()

    
    if export_pdf:
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", size=12)
        for line in blog_post.split("\n"):
            pdf.multi_cell(0, 10, line)
        pdf_output = "result.pdf"
        pdf.output(pdf_output)

    if export_md:
        md_output = "result.md"
        with open(md_output, "w", encoding="utf-8") as f:
            f.write(blog_post)

    
    pdf_link = "/result.pdf" if export_pdf else None
    md_link = "/result.md" if export_md else None

    return templates.TemplateResponse("result.html", {
        "request": request,
        "result": blog_post,
        "transcript": transcript,
        "user": user, "pdf_link": pdf_link, "md_link": md_link
    })

@app.get("/history.txt", response_class=PlainTextResponse)
def history(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login")
    db = SessionLocal()
    results = db.query(Generation).filter(Generation.email == user["email"]).all()
    db.close()
    return "\n---\n".join([f"{g.url}\n{g.result}" for g in results]) or "История пуста."