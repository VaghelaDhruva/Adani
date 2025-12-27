from celery import Celery
from typing import Dict, Any

from app.core.config import get_settings

settings = get_settings()

# Initialize Celery app
celery_app = Celery(
    "clinker_opt",
    broker=settings.BROKER_URL,
    backend=settings.RESULT_BACKEND,
    include=["app.services.job_queue"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task(bind=True)
def run_optimization_task(self, scenario_name: str, scenario_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Async Celery task to run a single optimization scenario.
    Updates task state and returns result.
    """
    from app.services.scenarios.scenario_runner import run_single_scenario

    self.update_state(state="PROGRESS", meta={"status": "starting"})
    result = run_single_scenario(scenario_data)
    self.update_state(state="SUCCESS", meta=result)
    return result
