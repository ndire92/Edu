import logging
import requests
from .kobo_config import BASE_URL, HEADERS

logger = logging.getLogger(__name__)

class KoboSyncError(Exception):
    pass


def fetch_kobo_data(uid):
    """
    Récupère toutes les données Kobo avec pagination + sécurité
    """
    url = f"{BASE_URL}{uid}/data/"
    results = []

    with requests.Session() as session:
        while url:
            try:
                response = session.get(url, headers=HEADERS, timeout=30)
                response.raise_for_status()

                data = response.json()

                results.extend(data.get("results", []))
                url = data.get("next")

            except requests.exceptions.Timeout:
                logger.error(f"Timeout Kobo: {url}")
                raise KoboSyncError("Timeout Kobo")

            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error Kobo: {e}")
                raise KoboSyncError(f"HTTP error: {e}")

            except requests.exceptions.RequestException as e:
                logger.error(f"Network error Kobo: {e}")
                raise KoboSyncError("Network error Kobo")

    logger.info(f"Kobo sync OK: {len(results)} records ({uid})")
    return results