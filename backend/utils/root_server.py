import json
import requests
from datetime import date
from time import sleep
from backend.utils.helpers import set_cache, get_cache, delete_cache
from config_env import CONFIG

ROOT_CACHE_ALIAS = "root_server_cache"
ROOT_CACHE_KEY = "root:cache"
ROOT_FILES = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M"]


def fetch_roots(roots):
    data = {}
    failed_roots = []
    for f in roots:
        url = f"{CONFIG.ROOT_VIZ_URL}/root/{f}/json/"
        print("Fetching:", url)

        try:
            res = requests.get(url, timeout=20)
            json_data = res.json()
            asn = json_data.get("ASN")

            if asn is None or not isinstance(asn, int):
                failed_roots.append(f)
            else:
                data[f] = json_data

        except Exception:
            failed_roots.append(f)

        sleep(0.1)

    return data, failed_roots


def load_root_data():
    today = str(date.today())
    # print(delete_cache(ROOT_CACHE_ALIAS, ROOT_CACHE_KEY))
    raw = get_cache(ROOT_CACHE_ALIAS, ROOT_CACHE_KEY)
    cache = json.loads(raw) if raw else None

    # CASE 1: Valid cache exists for today
    if cache and cache.get("date") == today:
        print("DEBUG: Cache found")

        cached_data = cache.get("data", {})
        failed_roots = cache.get("failed_roots", [])

        # If some roots failed earlier → retry only those
        if failed_roots:
            print("DEBUG: Retrying failed roots:", failed_roots)

            new_data, new_failed = fetch_roots(failed_roots)

            cached_data.update(new_data)

            payload = {
                "date": today,
                "data": cached_data,
                "failed_roots": new_failed
            }

            set_cache(
                ROOT_CACHE_ALIAS,
                ROOT_CACHE_KEY,
                json.dumps(payload),
                timeout=86400
            )

            failed_roots = new_failed

        return {
            "source": "Cached + Partial Refresh" if failed_roots else "Cached (Complete)",
            "date": today,
            "data": cached_data,
            "failed_roots": failed_roots
        }

    # CASE 2: No cache or old cache → fetch all
    print("DEBUG: No valid cache, fetching all roots")

    data, failed_roots = fetch_roots(ROOT_FILES)

    payload = {
        "date": today,
        "data": data,
        "failed_roots": failed_roots
    }

    set_cache(
        ROOT_CACHE_ALIAS,
        ROOT_CACHE_KEY,
        json.dumps(payload),
        timeout=86400
    )

    return {
        "source": "API (Fresh)",
        "date": today,
        "data": data,
        "failed_roots": failed_roots
    }
