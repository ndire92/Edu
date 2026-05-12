from django.core.management.base import BaseCommand
from dashboard.kobo_sync import sync_all

class Command(BaseCommand):
    help = "Synchronise toutes les données d'absentéisme depuis KoboToolbox"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('🚀 Début de la synchronisation Kobo...'))
        
        resultats = sync_all()
        
        self.stdout.write("\n--- RAPPORT DE SYNCHRONISATION ---")
        
        for formulaire, stat in resultats.items():
            if "error" in stat:
                self.stdout.write(self.style.ERROR(f"✗ {formulaire}: {stat['error']}"))
            else:
                self.stdout.write(self.style.SUCCESS(
                    f"✓ {formulaire}: Créés={stat['created']}, Modifiés={stat['updated']}, Ignorés={stat['skipped']}, Erreurs={len(stat['errors'])}"
                ))
                
                # ✅ afficher les erreurs POUR CE formulaire
                if stat['errors']:
                    self.stdout.write(self.style.WARNING("  ⚠️ Détails des erreurs :"))
                    for err in stat['errors']:
                        self.stdout.write(self.style.ERROR(f"   - {err}"))
        
        self.stdout.write(self.style.SUCCESS('✅ Synchronisation terminée !'))