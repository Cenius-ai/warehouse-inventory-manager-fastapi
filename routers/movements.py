from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session, joinedload
from starlette.status import HTTP_303_SEE_OTHER

from database import get_db
from models import Product, StockMovement, MovementType
from dependencies import get_current_user
from csrf import csrf_protect
from templates_loader import get_templates

router = APIRouter(prefix="/movements", tags=["movements"])


def _require_auth(request: Request):
    if "user_id" not in request.session:
        return RedirectResponse(url="/auth/login", status_code=HTTP_303_SEE_OTHER)
    return None


@router.get("/", response_class=HTMLResponse)
async def list_movements(request: Request, db: Session = Depends(get_db)):
    auth_check = _require_auth(request)
    if auth_check:
        return auth_check
    user = get_current_user(request, db)
    movements = (
        db.query(StockMovement)
        .options(joinedload(StockMovement.product))
        .order_by(StockMovement.created_at.desc())
        .limit(100)
        .all()
    )
    return get_templates().TemplateResponse(
        "movements/list.html",
        {"request": request, "user": user, "movements": movements},
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
    products = db.query(Product).order_by(Product.name).all()
    return get_templates().TemplateResponse(
        "movements/create.html",
        {
            "request": request,
            "user": user,
            "products": products,
            "types": [t.value for t in MovementType],
            "csrf_token": csrf_token,
        },
    )


@router.post("/create")
async def create_movement(
    request: Request,
    product_id: int = Form(...),
    type: str = Form(...),
    quantity: int = Form(...),
    note: str = Form(""),
    db: Session = Depends(get_db),
    csrf_token: str = Depends(csrf_protect),
):
    auth_check = _require_auth(request)
    if auth_check:
        return auth_check
    user = get_current_user(request, db)
    products = db.query(Product).order_by(Product.name).all()

    product = db.query(Product).filter(Product.id == product_id).first()

    errors = []
    if not product:
        errors.append("Product not found.")
    if quantity <= 0:
        errors.append("Quantity must be a positive integer.")
    if type not in [t.value for t in MovementType]:
        errors.append("Invalid movement type.")

    # Server-side non-negative stock enforcement for OUT and ADJUST types
    if type == MovementType.OUT.value and product:
        if quantity > product.current_stock:
            errors.append(
                f"Insufficient stock: only {product.current_stock} {product.unit} available "
                f"for {product.name}."
            )

    if errors:
        return get_templates().TemplateResponse(
            "movements/create.html",
            {
                "request": request,
                "user": user,
                "products": products,
                "types": [t.value for t in MovementType],
                "errors": errors,
                "product_id": product_id,
                "type": type,
                "quantity": quantity,
                "note": note,
                "csrf_token": csrf_token,
            },
            status_code=400,
        )

    # Create movement and update stock atomically
    movement = StockMovement(
        product_id=product_id,
        type=MovementType(type),
        quantity=quantity,
        note=note.strip(),
    )
    db.add(movement)

    if type == MovementType.IN.value:
        product.current_stock += quantity
    elif type == MovementType.OUT.value:
        product.current_stock -= quantity
    elif type == MovementType.ADJUST.value:
        # ADJUST sets to exact quantity
        product.current_stock = quantity

    db.commit()
    return RedirectResponse(url="/movements/", status_code=HTTP_303_SEE_OTHER)
