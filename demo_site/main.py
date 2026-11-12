"""A tiny, fully local notice board used for the offline demo."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .data import (
    EDITIONS,
    NOTICE_BY_SLUG,
    PAGE_SIZE,
    TYPE_LABELS,
    notices_on_page,
    page_count,
    revision_for_notice,
    revision_for_page,
)

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="采购公告示例站", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/")
async def home() -> RedirectResponse:
    return RedirectResponse(url="/notices?page=1", status_code=307)


@app.get("/notices")
async def notice_list(request: Request, page: int = 1, edition: str = "none"):
    if edition not in EDITIONS:
        raise HTTPException(status_code=404, detail="未知的演示版次")
    total_pages = page_count()
    if page < 1 or page > total_pages:
        raise HTTPException(status_code=404, detail="公告列表页不存在")

    notices = notices_on_page(page)
    return templates.TemplateResponse(
        request,
        "list.html",
        {
            "notices": notices,
            "page": page,
            "page_size": PAGE_SIZE,
            "total_pages": total_pages,
            "total_count": sum(1 for _ in NOTICE_BY_SLUG.values()),
            "type_labels": TYPE_LABELS,
            "site_name": os.getenv("DEMO_SITE_NAME", "采购公告示例站"),
            "edition": edition,
            "revision": revision_for_page(edition, page),
        },
    )


@app.get("/notices/detail/{slug}")
async def notice_detail(request: Request, slug: str, edition: str = "none"):
    if edition not in EDITIONS:
        raise HTTPException(status_code=404, detail="未知的演示版次")
    notice = NOTICE_BY_SLUG.get(slug)
    if notice is None:
        return templates.TemplateResponse(
            request,
            "not_found.html",
            {"type_labels": TYPE_LABELS, "revision": None},
            status_code=404,
        )
    return templates.TemplateResponse(
        request,
        "detail.html",
        {
            "notice": notice,
            "type_labels": TYPE_LABELS,
            "edition": edition,
            "revision": revision_for_notice(edition, notice),
        },
    )


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "demo-site"}
