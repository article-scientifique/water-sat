from urllib import request
from django.dispatch import receiver
from background_task.models import Task
from django.contrib import messages

@receiver(task_finished)
def task_finished_handler(sender, **kwargs):
    task_id = kwargs['task_id']
    task = Task.objects.get(id=task_id)
    if task.task_name == 'download_image_and_create_session':
        if task.failed_at:
            # La tâche a échoué
            messages.error(request, 'Le téléchargement des données a échoué.')
        else:
            # La tâche a réussi
            messages.success(request, 'Le téléchargement des données est terminé.')
