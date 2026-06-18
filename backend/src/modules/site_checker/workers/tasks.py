import asyncio
import time
import httpx
from taskiq_aio_pika import AioPikaBroker  
from taskiq.scheduler.scheduler import TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource
from ..dependencies import get_site_service
from ..service import SiteService
from ..repositories import SiteCheckerRepository
from src.core.database import AsyncSessionLocal
from src.core.config import settings
from loguru import logger

FAKE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

broker = AioPikaBroker(settings.RABBITMQ_URL)

scheduler = TaskiqScheduler(
    broker=broker,
    sources=[LabelScheduleSource(broker)]
)

class PingWorkerService:
    async def ping_single_site(self, client: httpx.AsyncClient, checker_id: str, url: str) -> None:
        start_time = time.time()
        status_code = 0
        try:
            response = await client.head(url, follow_redirects=True)
            status_code = response.status_code

            if status_code == 405:
                response = await client.get(url, follow_redirects=True)
                status_code = response.status_code
                
        except (httpx.RequestError, httpx.TimeoutException) as exc:
            status_code = 0
            logger.warning(
                "Ping failed for {url}. Error: {error_type}", 
                url=url, 
                error_type=exc.__class__.__name__
            )
            
        end_time = time.time()
        response_time_ms = int((end_time - start_time) * 1000)
        
        async with AsyncSessionLocal() as session:
            try:
                site_service = SiteService(session)
                
                await site_service.log(
                    checker_id=checker_id,
                    status_code=status_code,
                    response_time_ms=response_time_ms
                )

                logger.debug(
                    "Ping processed: {url} -> Status: {status} ({time}ms)", 
                    url=url, 
                    status=status_code, 
                    time=response_time_ms
                )
            except Exception:
                logger.exception("Failed to save ping log to DB for {url}", url=url)


@broker.task(schedule=[{"interval": 300}])
async def run_monitoring_job_task() -> None:
    logger.info("RabbitMQ Worker (Taskiq): Starting a batch of checks and cleaning old logs...")
    
    try:
        async with AsyncSessionLocal() as session:
            await get_site_service(session).delete_old_logs()
            site_checker_repo = SiteCheckerRepository(session)
            checkers = await site_checker_repo.get_all()
    except Exception:
        logger.exception("Taskiq Worker failed during pre-check DB operations (cleaning logs/fetching checkers)")
        return
        
    if not checkers:
        logger.info("RabbitMQ Worker (Taskiq): No sites to check.")
        return
        
    worker = PingWorkerService()
    
    logger.info("RabbitMQ Worker (Taskiq): Processing {count} checkers in parallel...", count=len(checkers))
    
    async with httpx.AsyncClient(headers=FAKE_HEADERS, timeout=10.0) as client:
        tasks = [
            worker.ping_single_site(client, str(checker.id), checker.site_url)
            for checker in checkers
        ]
        await asyncio.gather(*tasks)
            
    logger.info("RabbitMQ Worker (Taskiq): All parallel checks finished successfully.")
