from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session, joinedload
from starlette.status import HTTP_303_SEE_OTHER

from database import get_db
from models import Product
from dependencies import get_current_user
from templates_loader import get_templates

router = APIRouter(prefix="/overview", tags=["overview"])


def _require_auth(request: Request):
    if "user_id" not in request.session:
        return RedirectResponse(url="/auth/login", status_code=HTTP_303_SEE_OTHER)
    return None


@router.get("/", response_class=HTMLResponse)
async def overview(request: Request, db: Session = Depends(get_db)):
    auth_check = _require_auth(request)
    if auth_check:
        return auth_check
    user = get_current_user(request, db)

    products = (
        db.query(Product)
        .options(joinedload(Product.category))
        .order_by(Product.name)
        .all()
    )

    total_products = len(products)
    total_categories = len(set(p.category_id for p in products))
    low_stock = [p for p in products if p.current_stock <= p.reorder_point]
    out_of_stock = [p for p in products if p.current_stock == 0]

    # Products grouped by category for the overview
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
