from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from starlette.status import HTTP_303_SEE_OTHER

from database import get_db
from models import Category
from dependencies import get_current_user
from csrf import csrf_protect
from templates_loader import get_templates

router = APIRouter(prefix="/categories", tags=["categories"])


def _require_auth(request: Request):
    if "user_id" not in request.session:
        return RedirectResponse(url="/auth/login", status_code=HTTP_303_SEE_OTHER)
    return None


@router.get("/", response_class=HTMLResponse)
async def list_categories(
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
        "categories/list.html",
        {"request": request, "user": user, "categories": categories, "csrf_token": csrf_token},
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
    return get_templates().TemplateResponse(
        "categories/create.html",
        {"request": request, "user": user, "csrf_token": csrf_token},
    )


@router.post("/create")
async def create_category(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
    csrf_token: str = Depends(csrf_protect),
):
    auth_check = _require_auth(request)
    if auth_check:
        return auth_check
    user = get_current_user(request, db)

    error = None
    if not name.strip():
        error = "Name is required."
    elif db.query(Category).filter(Category.name == name.strip()).first():
        error = f"Category '{name.strip()}' already exists."

    if error:
        return get_templates().TemplateResponse(
            "categories/create.html",
            {
                "request": request,
                "user": user,
                "error": error,
                "name": name,
                "description": description,
                "csrf_token": csrf_token,
            },
            status_code=400,
        )

    cat = Category(name=name.strip(), description=description.strip())
    db.add(cat)
    db.commit()
    return RedirectResponse(url="/categories/", status_code=HTTP_303_SEE_OTHER)


@router.get("/{category_id}/edit", response_class=HTMLResponse)
async def edit_form(
    request: Request,
    category_id: int,
    db: Session = Depends(get_db),
    csrf_token: str = Depends(csrf_protect),
):
    auth_check = _require_auth(request)
    if auth_check:
        return auth_check
    user = get_current_user(request, db)
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        return RedirectResponse(url="/categories/", status_code=HTTP_303_SEE_OTHER)
    return get_templates().TemplateResponse(
        "categories/edit.html",
        {"request": request, "user": user, "category": category, "csrf_token": csrf_token},
    )


@router.post("/{category_id}/edit")
async def edit_category(
    request: Request,
    category_id: int,
    name: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
    csrf_token: str = Depends(csrf_protect),
):
    auth_check = _require_auth(request)
    if auth_check:
        return auth_check
    user = get_current_user(request, db)
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        return RedirectResponse(url="/categories/", status_code=HTTP_303_SEE_OTHER)

    error = None
    if not name.strip():
        error = "Name is required."
    else:
        dup = db.query(Category).filter(Category.name == name.strip(), Category.id != category_id).first()
        if dup:
            error = f"Category '{name.strip()}' already exists."

    if error:
        return get_templates().TemplateResponse(
            "categories/edit.html",
            {"request": request, "user": user, "category": category, "error": error, "csrf_token": csrf_token},
            status_code=400,
        )

    category.name = name.strip()
    category.description = description.strip()
    db.commit()
    return RedirectResponse(url="/categories/", status_code=HTTP_303_SEE_OTHER)


@router.post("/{category_id}/delete")
async def delete_category(
    request: Request,
    category_id: int,
    db: Session = Depends(get_db),
    csrf_token: str = Depends(csrf_protect),
):
    auth_check = _require_auth(request)
    if auth_check:
        return auth_check
    category = db.query(Category).filter(Category.id == category_id).first()
    if category:
        # Only allow delete if no products reference it
        if len(category.products) > 0:
            return RedirectResponse(
                url="/categories/?error=Cannot+delete+category+with+products",
                status_code=HTTP_303_SEE_OTHER,
            )
        db.delete(category)
        db.commit()
    return RedirectResponse(url="/categories/", status_code=HTTP_303_SEE_OTHER)
