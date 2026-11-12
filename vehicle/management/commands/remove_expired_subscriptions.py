from django.core.management.base import BaseCommand
from vehicle.utils import remove_expired_pro_subscriptions

class Command(BaseCommand):
    help = "Deactivate expired Pro subscriptions"

    def handle(self, *args, **kwargs):
        remove_expired_pro_subscriptions()
        self.stdout.write("Expired Pro subscriptions have been processed.")
