from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import LutaRegistrada

@receiver(post_save, sender=LutaRegistrada)
def enviar_para_ml(sender, instance, created, **kwargs):
    if created:  # só quando a luta é criada
        try:
            instance.enviar_para_ml_db()
        except Exception as e:
            print("ERRO ao enviar para ML:", e)
