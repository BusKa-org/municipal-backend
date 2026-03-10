import atexit
import os
import sys

from apscheduler.triggers.cron import CronTrigger
from flask import Flask
from flask_apscheduler import APScheduler

from app.tasks.agendamento_tasks import job_gerar_viagens_semanais
from app.tasks.notificacao_tasks import verificar_viagens_10min, verificar_viagens_24h


def init_scheduler(app: Flask, scheduler: APScheduler):
    """Inicializa e registra todas as tarefas de background."""

    if "pytest" in sys.modules:
        app.logger.info("Test mode detected: Scheduler isn't needed.")
        return

    if app.debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        return

    scheduler.add_job(
        id="job_24h",
        func=verificar_viagens_24h,
        args=[app],
        trigger="interval",
        minutes=60,
        replace_existing=True,
    )

    scheduler.add_job(
        id="job_10min",
        func=verificar_viagens_10min,
        args=[app],
        trigger="interval",
        minutes=2,
        replace_existing=True,
    )

    scheduler.add_job(
        id="job_viagens_semanais",
        func=job_gerar_viagens_semanais,
        args=[app],
        trigger=CronTrigger(day_of_week="sun", hour=2, minute=0, timezone="America/Sao_Paulo"),
        replace_existing=True,
    )

    scheduler.start()

    atexit.register(lambda: scheduler.shutdown())
