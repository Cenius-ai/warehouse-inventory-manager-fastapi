"""CSRF protection for state-changing requests.

Uses a session-stored token verified against a hidden form field.
SameSite=lax cookies provide a first line of defence; this adds
token-based verification for all POST/PUT/DELETE/PATCH requests.
"""

import secrets

from fastapi import Depends, Form, HTTPException, Request

CSRF_FIELD = "csrf_token"


async def csrf_protect(
    request: Request,
    csrf_token: str = Form(None),
) -> str:
    """Dependency that provides a CSRF token and verifies it on mutation requests.

    On GET/HEAD: ensures a token exists in the session and returns it for
    embedding in forms.

    On POST/PUT/DELETE/PATCH: also verifies the submitted token matches the
    session token, raising 403 on mismatch.
    """
    session_token: str | None = request.session.get(CSRF_FIELD)
    if session_token is None:
        session_token = secrets.token_hex(32)
        request.session[CSRF_FIELD] = session_token

    if request.method in ("POST", "PUT", "DELETE", "PATCH"):
        if not csrf_token or not secrets.compare_digest(session_token, csrf_token):
            raise HTTPException(status_code=403, detail="CSRF token invalid")

    return session_token
