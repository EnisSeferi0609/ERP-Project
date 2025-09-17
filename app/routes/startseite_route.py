"""Home page and main dashboard route."""

from fastapi import APIRouter, Request
from app.utils.template_utils import create_templates

router = APIRouter()
templates = create_templates()


@router.get("/")
def startseite(request: Request):
    return templates.TemplateResponse("startseite.html", {
        "request": request
    })
