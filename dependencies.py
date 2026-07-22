from fastapi import Request, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from starlette.status import HTTP_302_FOUND, HTTP_303_SEE_OTHER

from database import get_db
from models import User


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    user_id = request.session.get("user_id")
    if user_id is None:
        return None
    return db.query(User).filter(User.id == user_id).first()


def require_auth(request: Request):
    if "user_id" not in request.session:
        return RedirectResponse(url="/auth/login", status_code=HTTP_302_FOUND)
    return None
