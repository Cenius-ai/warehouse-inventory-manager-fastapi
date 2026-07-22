import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.status import HTTP_302_FOUND

from config import settings
from database import engine, Base, get_db
from models import User, Product, Category
from seed import seed_data
from templates_loader import get_templates
from routers import auth as auth_router
from routers import categories as categories_router
from routers import products as products_router
from routers import movements as movements_router
from routers import overview as overview_router


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_data()
    yield


app = FastAPI(
    title=settings.APP_TITLE,
    lifespan=lifespan,
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="inventory_session",
    max_age=86400,
    https_only=True,
    same_site="lax",
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth_router.router)
app.include_router(categories_router.router)
app.include_router(products_router.router)
app.include_router(movements_router.router)
app.include_router(overview_router.router)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            products = db.query(Product).order_by(Product.name).all()
            total_products = len(products)
            total_categories = len(set(p.category_id for p in products))
            low_stock = [p for p in products if p.current_stock <= p.reorder_point]
            out_of_stock = [p for p in products if p.current_stock == 0]
            by_category = {}
            for p in products:
                cat_name = p.category.name if p.category else "Uncategorised"
                by_category.setdefault(cat_name, []).append(p)
            return get_templates().TemplateResponse(
                "overview/index.html",
                {
                    "request": request,
                    "user": user,
                    "products": products,
                    "total_products": total_products,
                    "total_categories": total_categories,
                    "low_stock": low_stock,
                    "out_of_stock": out_of_stock,
                    "by_category": by_category,
                },
            )
    # Unauthenticated — serve login page at / with 200
    return get_templates().TemplateResponse("login.html", {"request": request})


@app.get("/health")
async def health():
    return {"status": "ok"}
