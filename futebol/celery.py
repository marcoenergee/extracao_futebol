import os
from celery import Celery
from celery.schedules import crontab


# Configura a variável DJANGO_SETTINGS_MODULE
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "futebol.settings")

app = Celery("futebol")

# Carrega as configurações do Django no Celery
app.config_from_object("django.conf:settings", namespace="CELERY")

# Descobre automaticamente tasks nos apps instalados
app.autodiscover_tasks()



# Configurações Celery Beat (opcional, se usado)
app.conf.beat_schedule = {
    'scrape_campeonato_every_20_minutes': {
        'task': 'jogos.tasks.scrape_campeonato',  # Caminho completo para a task
        'schedule': crontab(minute='*/20'),  # A cada 10 minutos
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
