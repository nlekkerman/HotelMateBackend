from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

from entertainment.models import MemoryGameTournament


class Command(BaseCommand):
    help = (
        "Update tournament statuses based on start_date/end_date."
    )

    def handle(self, *args, **options):
        now = timezone.now()

        # Find tournaments that may need status changes
        qs = MemoryGameTournament.objects.all()

        # Local references to status values (shorten long attribute access)
        STATUS_COMPLETED = MemoryGameTournament.TournamentStatus.COMPLETED
        STATUS_ACTIVE = MemoryGameTournament.TournamentStatus.ACTIVE
        STATUS_UPCOMING = MemoryGameTournament.TournamentStatus.UPCOMING

        to_update = []

        for t in qs:
            new_status = None

            # Completed if end_date in the past
            if t.end_date and t.end_date < now:
                if t.status != STATUS_COMPLETED:
                    new_status = STATUS_COMPLETED
            # Active if currently within start and end window
            elif t.start_date and t.start_date <= now <= t.end_date:
                if t.status != STATUS_ACTIVE:
                    new_status = STATUS_ACTIVE
            # Upcoming if start_date in future
            elif t.start_date and t.start_date > now:
                if t.status != STATUS_UPCOMING:
                    new_status = STATUS_UPCOMING

            if new_status:
                t.status = new_status
                to_update.append(t)

        if to_update:
            MemoryGameTournament.objects.bulk_update(
                to_update, ['status', 'updated_at']
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Updated {len(to_update)} tournaments' statuses."
                )
            )
        else:
            self.stdout.write('No tournament status changes needed.')

        # We only update tournament statuses in this command.
        # Ranking/ending logic is left to the admin "end" action.
