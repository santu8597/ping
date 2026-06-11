import requests
import logging
import time

from django.db import transaction

from backend.anchor.models import UserAnchor, AnchorIpDetails, CommendExecutionHistory, Measurement
from config_env import CONFIG
from services_aiori_v2 import settings

logger = logging.getLogger(__name__)

IPINFO_URL = "https://ipinfo.io/{ip}/json"
IPINFO_TIMEOUT = 3


# --------------------------------------------------
# IPINFO FETCH
# --------------------------------------------------

def sync_anchor_ip():
    print("Starting Anchor sync...")

    token = CONFIG.IPINFO_TOKEN_NEW

    if not token:
        print("IPINFO_TOKEN_NEW missing in settings")
        return

    created = 0
    updated = 0
    skipped = 0
    failed = 0

    # -----------------------------
    # Active Anchors Query
    # -----------------------------

    qs = (
        UserAnchor.objects
        .select_related("anchor", "user")
        .filter(
            is_deleted=False,
            is_blocked=False,
            status="active",
            anchor__is_online=True,
        )

    )

    total = qs.count()

    print(f"Found {total} active anchors")

    # -----------------------------
    # IPInfo Cache (in-memory)
    # -----------------------------

    ip_cache = {}

    with transaction.atomic():

        for idx, ua in enumerate(qs, start=1):

            try:

                print(f"[{idx}/{total}] Processing UA {ua.id}")

                anchor = ua.anchor
                ip = anchor.public_ip

                # -------------------------
                # Validation
                # -------------------------

                if not anchor:
                    skipped += 1
                    logger.warning("UA %s has no anchor", ua.id)
                    continue

                if not ip:
                    skipped += 1
                    logger.warning("UA %s missing IP", ua.id)
                    continue

                if not anchor.id:
                    skipped += 1
                    logger.warning("Anchor %s missing anchor_id", anchor.id)
                    continue

                try:
                    anchor_id = int(anchor.id)
                except Exception:
                    skipped += 1
                    logger.warning(
                        "Invalid anchor_id %s",
                        anchor.id
                    )
                    continue

                # -------------------------
                # IPINFO LOOKUP (Cached)
                # -------------------------

                if ip in ip_cache:

                    ipinfo = ip_cache[ip]

                else:

                    ipinfo = fetch_ipinfo(ip, token)

                    ip_cache[ip] = ipinfo

                    # Rate protection
                    time.sleep(0.2)

                asn = ipinfo.get("asn", "NA").get("asn", "NA")
                isp = ipinfo.get("asn", "NA").get("name", "NA")
                country = ipinfo.get("country", "")
                region = ipinfo.get("region", "")

                isp_location = f"{region}, {country}".strip()

                # -------------------------
                # Status
                # -------------------------

                status = "online" if anchor.is_online else "offline"

                # -------------------------
                # UPSERT
                # -------------------------

                obj, is_created = AnchorIpDetails.objects.update_or_create(

                    anchor_id=anchor_id,

                    defaults={

                        "anchor_name": anchor.anchor_name or "",

                        "user_anchor_id": ua.id,

                        "ip_address": ip,

                        "anchor_location": ua.location or "",

                        "asn": asn,

                        "isp": isp,

                        "isp_location": isp_location,

                        "status": status,
                    }
                )

                if is_created:
                    created += 1
                else:
                    updated += 1

                logger.info(
                    "Synced anchor=%s ip=%s",
                    anchor_id,
                    ip
                )

            except Exception as e:

                failed += 1

                logger.exception(
                    "Failed UA %s: %s",
                    ua.id,
                    e
                )

    # -----------------------------
    # SUMMARY
    # -----------------------------

    print("\n Sync Completed")
    print(f"Created : {created}")
    print(f"Updated : {updated}")
    print(f"Skipped : {skipped}")
    print(f"Failed  : {failed}")
    print(f"Total   : {total}")


# --------------------------------------------------
# IPINFO FETCH (SAFE)
# --------------------------------------------------

def fetch_ipinfo(ip, token):
    try:

        url = IPINFO_URL.format(ip=ip)

        resp = requests.get(
            url,
            params={"token": token},
            timeout=IPINFO_TIMEOUT,
        )

        if resp.status_code != 200:
            logger.warning(
                "IPINFO failed %s → %s",
                ip,
                resp.status_code
            )
            return {}

        return resp.json()

    except Exception as e:

        logger.warning(
            "IPINFO error %s → %s",
            ip,
            e
        )

        return {}
def sync_pending_measurements():

    print("====== MEASUREMENT SYNC START ======")

    pending_qs = Measurement.objects.filter(
        status="pending",
        command_id__isnull=False
    )

    pending_count = pending_qs.count()

    print("[INFO] Pending records:", pending_count)

    if pending_count == 0:
        print("[INFO] No pending measurements. Exiting.")
        print("====== MEASUREMENT SYNC END ======")
        return

    for measurement in pending_qs:

        try:

            print("[PROCESS] Measurement ID: ", measurement.id)

            command_id = measurement.command_id

            # ----------------------------------
            # Find Command History
            # ----------------------------------

            history = CommendExecutionHistory.objects.filter(
                id=command_id
            ).first()

            if not history:
                print("[SKIP] No history for", command_id)
                continue


            query_id = str(history.commend_query_id)

            if not query_id:
                print("[SKIP] Missing query_id")
                continue

            # ----------------------------------
            # Query Influx
            # ----------------------------------

            influx_url = (
                f"{settings.INFLUXDB_HOST}/query"
                f"?pretty=true"
                f"&db={settings.INFLUXDB_DATABASE}"
                f"&q=SELECT * FROM ping WHERE id='{query_id}'"
            )

            resp = requests.get(influx_url, timeout=20)

            if resp.status_code != 200:
                print("[WAIT] Influx not ready")
                continue


            data = resp.json()

            records = []

            # ----------------------------------
            # Parse Result
            # ----------------------------------

            for result in data.get("results", []):

                for series in result.get("series", []):

                    columns = series.get("columns", [])

                    for row in series.get("values", []):

                        record = dict(zip(columns, row))

                        records.append(record)

            if not records:
                print("[WAIT] No data yet")
                continue

            # ----------------------------------
            # Take First Record (Aggregated)
            # ----------------------------------

            rec = records[0]

            rtt_min = rec.get("rtt_min")
            rtt_avg = rec.get("rtt_avg")
            rtt_max = rec.get("rtt_max")

            if rtt_min is None or rtt_avg is None or rtt_max is None:
                print("[WAIT] RTT not ready")
                continue

            # ----------------------------------
            # Update Measurement
            # ----------------------------------

            measurement.min_latency = float(rtt_min)
            measurement.avg_latency = float(rtt_avg)
            measurement.max_latency = float(rtt_max)

            measurement.status = "success"
            measurement.error_message = None

            measurement.save(update_fields=[
                "min_latency",
                "avg_latency",
                "max_latency",
                "status",
                "error_message"
            ])

            print("[UPDATED] Measurement ID: ", measurement.id)

        except Exception as e:

            print("[ERROR]", measurement.id, str(e))

            measurement.error_message = str(e)

            measurement.save(update_fields=["error_message"])

            continue

    print("====== MEASUREMENT SYNC END ======")

