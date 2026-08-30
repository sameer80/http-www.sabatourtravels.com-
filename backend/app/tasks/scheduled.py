import asyncio

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import Website
from app.services.crawl_service import refresh_opportunities, run_website_crawl
from app.tasks.celery_app import celery_app


def _run(coro):
    return asyncio.run(coro)


@celery_app.task(name="app.tasks.scheduled.refresh_all_crawls")
def refresh_all_crawls():
  async def _inner():
      async with AsyncSessionLocal() as db:
          websites = (await db.execute(select(Website))).scalars().all()
          for website in websites:
              await run_website_crawl(db, website.id)
  return _run(_inner())


@celery_app.task(name="app.tasks.scheduled.refresh_all_opportunities")
def refresh_all_opportunities():
  async def _inner():
      async with AsyncSessionLocal() as db:
          websites = (await db.execute(select(Website))).scalars().all()
          for website in websites:
              await refresh_opportunities(db, website.id)
  return _run(_inner())
