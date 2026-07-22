from fastapi import APIRouter, Request, Form, Depends, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session, joinedload
from starlette.status import HTTP_303_SEE_OTHER

from database import get_db
from models import Product, Category
from dependencies import get_current_user
from csrf import csrf_protect
from templates_loader import get_templates

router = APIRouter(prefix="/products", tags=["products"])


def _require_auth(request: Request):
    if "user_id" not in request.session:
        return RedirectResponse(url="/auth/login", status_code=HTTP_303_SEE_OTHER)
    return None


@router.get("/", response_class=HTMLResponse)
async def list_products(
    request: Request,
    db: Session = Depends(get_db),
    category: str = Query("", alias="category"),
    search: str = Query("", alias="search"),
):
    auth_check = _require_auth(request)
    if auth_check:
        return auth_check
    user = get_current_user(request, db)

    q = db.query(Product).options(joinedload(Product.category))
    if category:
        q = q.join(Category).filter(Category.name == category)
    if search:
        q = q.filter(
            (Product.name.ilike(f"%{search}%")) | (Product.sku.ilike(f"%{search}%"))
        )

    products = q.order_by(Product.name).all()
    categories = db.query(Category).order_by(Category.name).all()

    return get_templates().TemplateResponse(
        "products/list.html",
        {
            "request": request,
            "user": user,
            "products": products,
            "categories": categories,
            "selected_category": category,
            "search": search,
        },
    )


@router.get("/create", response_class=HTMLResponse)
async def create_form(
    request: Request,
    db: Session = Depends(get_db),
    csrf_token: str = Depends(csrf_protect),
):
    auth_check = _require_auth(request)
    if auth_check:
        return auth_check
    user = get_current_user(request, db)
    categories = db.query(Category).order_by(Category.name).all()
    return get_templates().TemplateResponse(
        "products/create.html",
        {"request": request, "user": user, "categories": categories, "csrf_token": csrf_token},
    )


@router.post("/create")
async def create_product(
    request: Request,
    sku: str = Form(...),
    name: str = Form(...),
    description: str = Form(""),
    category_id: int = Form(...),
    current_stock: int = Form(0),
    reorder_point: int = Form(10),
    unit: str = Form("pcs"),
    db: Session = Depends(get_db),
    csrf_token: str = Depends(csrf_protect),
):
    auth_check = _require_auth(request)
    if auth_check:
        return auth_check
    user = get_current_user(request, db)
    categories = db.query(Category).order_by(Category.name).all()

    errors = []
    if not sku.strip():
        errors.append("SKU is required.")
    if not name.strip():
        errors.append("Name is required.")
    if current_stock < 0:
        errors.append("Current stock cannot be negative.")
    if reorder_point < 0:
        errors.append("Reorder point cannot be negative.")
    if db.query(Product).filter(Product.sku == sku.strip()).first():
        errors.append(f"SKU '{sku.strip()}' already exists.")

    if errors:
        return get_templates().TemplateResponse(
            "products/create.html",
            {
                "request": request,
                "user": user,
                "categories": categories,
                "errors": errors,
                "sku": sku,
                "name": name,
                "description": description,
                "category_id": category_id,
                "current_stock": current_stock,
                "reorder_point": reorder_point,
                "unit": unit,
                "csrf_token": csrf_token,
            },
            status_code=400,
        )

    product = Product(
        sku=sku.strip(),
        name=name.strip(),
        description=description.strip(),
        category_id=category_id,
        current_stock=current_stock,
        reorder_point=reorder_point,
        unit=unit.strip() or "pcs",
    )
    db.add(product)
    db.commit()
    return RedirectResponse(url="/products/", status_code=HTTP_303_SEE_OTHER)


@router.get("/{product_id}", response_class=HTMLResponse)
async def product_detail(
    request: Request,
    product_id: int,
    db: Session = Depends(get_db),
    csrf_token: str = Depends(csrf_protect),
):
    auth_check = _require_auth(request)
    if auth_check:
        return auth_check
    user = get_current_user(request, db)
    product = (
        db.query(Product)
        .options(joinedload(Product.category), joinedload(Product.movements))
        .filter(Product.id == product_id)
        .first()
    )
    if not product:
        return RedirectResponse(url="/products/", status_code=HTTP_303_SEE_OTHER)

    return get_templates().TemplateResponse(
        "products/detail.html",
        {"request": request, "user": user, "product": product, "csrf_token": csrf_token},
    )


@router.get("/{product_id}/edit", response_class=HTMLResponse)
async def edit_form(
    request: Request,
    product_id: int,
    db: Session = Depends(get_db),
    csrf_token: str = Depends(csrf_protect),
):
    auth_check = _require_auth(request)
    if auth_check:
        return auth_check
    user = get_current_user(request, db)
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return RedirectResponse(url="/products/", status_code=HTTP_303_SEE_OTHER)
    categories = db.query(Category).order_by(Category.name).all()
    return get_templates().TemplateResponse(
        "products/edit.html",
        {"request": request, "user": user, "product": product, "categories": categories, "csrf_token": csrf_token},
    )


@router.post("/{product_id}/edit")
async def edit_product(
    request: Request,
    product_id: int,
    sku: str = Form(...),
    name: str = Form(...),
    description: str = Form(""),
    category_id: int = Form(...),
    reorder_point: int = Form(10),
    unit: str = Form("pcs"),
    db: Session = Depends(get_db),
    csrf_token: str = Depends(csrf_protect),
):
    auth_check = _require_auth(request)
    if auth_check:
        return auth_check
    user = get_current_user(request, db)
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return RedirectResponse(url="/products/", status_code=HTTP_303_SEE_OTHER)
    categories = db.query(Category).order_by(Category.name).all()

    errors = []
    if not sku.strip():
        errors.append("SKU is required.")
    if not name.strip():
        errors.append("Name is required.")
    if reorder_point < 0:
        errors.append("Reorder point cannot be negative.")
    dup = db.query(Product).filter(Product.sku == sku.strip(), Product.id != product_id).first()
    if dup:
        errors.append(f"SKU '{sku.strip()}' already exists.")

    if errors:
        return get_templates().TemplateResponse(
            "products/edit.html",
            {
                "request": request,
                "user": user,
                "product": product,
                "categories": categories,
                "errors": errors,
                "csrf_token": csrf_token,
            },
            status_code=400,
        )

    product.sku = sku.strip()
    product.name = name.strip()
    product.description = description.strip()
    product.category_id = category_id
    product.reorder_point = reorder_point
    product.unit = unit.strip() or "pcs"
    db.commit()
    return RedirectResponse(url=f"/products/{product_id}", status_code=HTTP_303_SEE_OTHER)


@router.post("/{product_id}/delete")
async def delete_product(
    request: Request,
    product_id: int,
    db: Session = Depends(get_db),
    csrf_token: str = Depends(csrf_protect),
):
    auth_check = _require_auth(request)
    if auth_check:
        return auth_check
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        db.delete(product)
        db.commit()
    return RedirectResponse(url="/products/", status_code=HTTP_303_SEE_OTHER)
