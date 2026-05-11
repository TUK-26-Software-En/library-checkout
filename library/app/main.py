from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from app.database import engine, Base
import app.models  # noqa: F401 — register all ORM models before create_all
from app.routers import book_router, member_router, loan_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="도서 대출 관리 시스템")

app.include_router(book_router)
app.include_router(member_router)
app.include_router(loan_router)


@app.get("/")
def root():
    return RedirectResponse("/books/")
