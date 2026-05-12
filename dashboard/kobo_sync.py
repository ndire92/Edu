import logging
from datetime import datetime
from django.db import transaction

from dashboard.models import (
    Ecole, Eleve, Enseignant,
    AbsenceQuotidienneEleve, AbsenceMensuelleEleve,
    AbsenceQuotidienneEnseignant, AbsenceMensuelleEnseignant
)
from dashboard.kobo_config import FORM_UIDS
from dashboard.kobo_client import fetch_kobo_data

logger = logging.getLogger(__name__)

# ==========================================
# UTILITAIRES
# ==========================================
def get_attachment_url(attachments):
    if attachments and isinstance(attachments, list) and len(attachments) > 0:
        return attachments[0].get("download_url")
    return None


def parse_kobo_month(month_str):
    if not month_str:
        return None
    try:
        return datetime.strptime(month_str, "%Y-%m").date()
    except ValueError:
        try:
            return datetime.strptime(month_str.split("T")[0], "%Y-%m-%d").date()
        except ValueError:
            return None


# ==========================================
# ÉLÈVES
# ==========================================
def sync_eleves():
    stats = {"created": 0, "updated": 0, "skipped": 0, "errors": []}
    records = fetch_kobo_data(FORM_UIDS["eleves_registre"])

    with transaction.atomic():
        for r in records:
            try:
                num_reg = str(r.get("numero_reg", "")).strip()
                if not num_reg:
                    stats["skipped"] += 1
                    continue

                ecole, _ = Ecole.objects.get_or_create(
                    nouveau_code_ecole=r.get("nouveau_code_ecole") or "DEFAULT",
                    defaults={"nom_ecole": r.get("nom_ecole") or "Ecole Inconnue"}
                )

                eleve, created = Eleve.objects.update_or_create(
                    numero_reg=num_reg,
                    defaults={
                        "ecole": ecole,
                        "kobo_id": r.get("_id"),
                        "nom_prenom": r.get("nom_prenom"),
                        "nni": r.get("nni"),
                        "sexe": r.get("sc"),
                        "classe": r.get("cl"),
                        "tel": r.get("tel"),
                        "observations": r.get("observations"),
                        "enseignant": r.get("enseignant"),
                        "signature": get_attachment_url(r.get("_attachments")),
                    }
                )

                stats["created" if created else "updated"] += 1

            except Exception as e:
                stats["errors"].append(f"{r.get('_id')}: {str(e)}")

    return stats

# ==========================================
# ENSEIGNANTS
# ==========================================
def sync_enseignants():
    stats = {"created": 0, "updated": 0, "skipped": 0, "errors": []}
    records = fetch_kobo_data(FORM_UIDS["ens_registre"])

    with transaction.atomic():
        for r in records:
            try:
                num_reg = str(r.get("enseign_numero_reg", "")).strip()
                if not num_reg:
                    stats["skipped"] += 1
                    continue

                ecole, _ = Ecole.objects.get_or_create(
                    nouveau_code_ecole=r.get("nouveau_code_ecole") or "DEFAULT",
                    defaults={"nom_ecole": r.get("nom_ecole") or "Ecole Enseignant"}
                )

                enseignant, created = Enseignant.objects.update_or_create(
                    numero_reg=num_reg,
                    defaults={
                        "ecole": ecole,
                        "kobo_id": r.get("_uuid"),
                        "nom_prenom": r.get("enseign_nom_prenom"),
                        "nni": r.get("enseign_nni"),
                        "mle": r.get("enseign_mle"),
                        "langue_travail": r.get("enseign_langue_travail"),
                        "sexe": r.get("enseign_sexe"),
                        "tel": r.get("enseign_tel"),
                        "observations": r.get("observations"),
                        "directeur_nom": r.get("directeur_nom"),
                        "signature_cachet": get_attachment_url(r.get("_attachments")),
                    }
                )

                stats["created" if created else "updated"] += 1

            except Exception as e:
                stats["errors"].append(f"{r.get('_id')}: {str(e)}")

    return stats
# ==========================================
# ABSENCES ÉLÈVES QUOTIDIENNES
# ==========================================
def sync_abs_eleve_q():
    stats = {"created": 0, "updated": 0, "skipped": 0, "errors": []}
    records = fetch_kobo_data(FORM_UIDS["eleves_abs_q"])

    with transaction.atomic():
        for r in records:
            try:
                kobo_id = str(r.get("_id")).strip()
                if not kobo_id:
                    stats["skipped"] += 1
                    continue

                num_reg = str(r.get("numero_reg", "")).strip()
                if not num_reg:
                    stats["skipped"] += 1
                    continue

                eleve = Eleve.objects.filter(numero_reg=num_reg).first()
                if not eleve:
                    stats["skipped"] += 1
                    continue

                date_str = r.get("date_absence")
                if not date_str:
                    stats["skipped"] += 1
                    continue

                date_obj = datetime.strptime(date_str.split("T")[0], "%Y-%m-%d").date()

                _, created = AbsenceQuotidienneEleve.objects.update_or_create(
                    kobo_id=kobo_id,  # ✅ CORRECTION ICI
                    defaults={
                        "eleve": eleve,
                        "date_absence": date_obj,
                        "total_absences": int(r.get("total_absences") or 0),
                        "periodes": r.get("periodes"),
                        "enseignant": r.get("enseignant"),
                        "signature": get_attachment_url(r.get("_attachments")),
                    }
                )

                stats["created" if created else "updated"] += 1

            except Exception as e:
                stats["errors"].append(f"{r.get('_id')}: {str(e)}")

    return stats
# ==========================================
# ABSENCES ÉLÈVES MENSUELLES
# ==========================================
def sync_abs_eleve_m():
    stats = {"created": 0, "updated": 0, "skipped": 0, "errors": []}
    records = fetch_kobo_data(FORM_UIDS["eleves_abs_m"])

    with transaction.atomic():
        for r in records:
            try:
                num_reg = str(r.get("numero_reg", "")).strip()
                if not num_reg:
                    stats["skipped"] += 1
                    continue

                eleve = Eleve.objects.filter(numero_reg=num_reg).first()
                if not eleve:
                    stats["skipped"] += 1
                    continue

                mois_obj = parse_kobo_month(r.get("mois"))
                if not mois_obj:
                    stats["skipped"] += 1
                    continue

                _, created = AbsenceMensuelleEleve.objects.update_or_create(
                    eleve=eleve,
                    mois=mois_obj,
                    defaults={
                        "kobo_id": r.get("_id"),
                        "total_absences": int(r.get("total_absences") or 0),
                        "observations": r.get("observations"),
                        "enseignant": r.get("enseignant"),
                        "signature": get_attachment_url(r.get("_attachments")),
                    }
                )

                stats["created" if created else "updated"] += 1

            except Exception as e:
                stats["errors"].append(f"{r.get('_id')}: {str(e)}")

    return stats


# ==========================================
# ABSENCES ENSEIGNANTS QUOTIDIENNES
# ==========================================
def sync_abs_ens_q():
    stats = {"created": 0, "updated": 0, "skipped": 0, "errors": []}
    records = fetch_kobo_data(FORM_UIDS["ens_abs_q"])

    with transaction.atomic():
        for r in records:
            try:
                num_reg = str(r.get("enseign_numero_reg", "")).strip()
                if not num_reg:
                    stats["skipped"] += 1
                    continue

                enseignant = Enseignant.objects.filter(numero_reg=num_reg).first()
                if not enseignant:
                    stats["skipped"] += 1
                    continue

                date_str = r.get("date_absence")
                if not date_str:
                    stats["skipped"] += 1
                    continue

                date_obj = datetime.strptime(date_str.split("T")[0], "%Y-%m-%d").date()

                obj, created = AbsenceQuotidienneEnseignant.objects.update_or_create(
                    enseignant=enseignant,
                    date_absence=date_obj,
                    defaults={
                        "kobo_id": r.get("_uuid"),
                        "abs_justifiees": int(r.get("enseign_aj") or 0),
                        "abs_non_justifiees": int(r.get("enseign_total_absences") or 0),
                        "periodes": r.get("periodes"),
                        "directeur_nom": r.get("directeur_nom"),
                        "signature_cachet": get_attachment_url(r.get("_attachments")),
                    }
                )

                stats["created" if created else "updated"] += 1

            except Exception as e:
                stats["errors"].append(f"{r.get('_id')}: {str(e)}")

    return stats

# ==========================================
# ABSENCES ENSEIGNANTS MENSUELLES
# ==========================================
def sync_abs_ens_m():
    stats = {"created": 0, "updated": 0, "skipped": 0, "errors": []}
    records = fetch_kobo_data(FORM_UIDS["ens_abs_m"])

    with transaction.atomic():
        for r in records:
            try:
                mle = str(r.get("enseign_mle", "")).strip()
                if not mle:
                    stats["skipped"] += 1
                    continue

                enseignant = Enseignant.objects.filter(mle=mle).first()
                if not enseignant:
                    stats["skipped"] += 1
                    continue

                mois_obj = parse_kobo_month(r.get("mois"))
                if not mois_obj:
                    stats["skipped"] += 1
                    continue

                obj, created = AbsenceMensuelleEnseignant.objects.update_or_create(
                    enseignant=enseignant,
                    mois=mois_obj,
                    defaults={
                        "kobo_id": r.get("_uuid"),
                        "abs_justifiees": int(r.get("enseign_aj") or 0),
                        "abs_non_justifiees": int(r.get("enseign_total_absences") or 0),
                        "directeur_nom": r.get("directeur_nom"),
                        "signature_cachet": get_attachment_url(r.get("_attachments")),
                    }
                )

                stats["created" if created else "updated"] += 1

            except Exception as e:
                stats["errors"].append(f"{r.get('_id')}: {str(e)}")

    return stats

# ==========================================
# SYNC GLOBAL
# ==========================================
def sync_all():
    logger.info("Début sync global")

    tasks = {
        "eleves_registre": sync_eleves,
        "eleves_abs_q": sync_abs_eleve_q,
        "eleves_abs_m": sync_abs_eleve_m,
        "ens_registre": sync_enseignants,
        "ens_abs_q": sync_abs_ens_q,
        "ens_abs_m": sync_abs_ens_m,
    }

    results = {}

    for key, func in tasks.items():
        try:
            results[key] = func()
        except Exception as e:
            results[key] = {"error": str(e)}
            logger.error(f"Erreur {key}: {str(e)}")

    logger.info("Fin sync global")
    return results