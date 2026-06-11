from backend.anchor.models import CommendExecutionHistory
from django.db import transaction
from django.utils import timezone


def update_measurement_public(user_ids, start_date, end_date=None, is_public=True):
    """
    Core function to update is_public=True for given users and date range.
    """

    print(f"[INFO] Running update_is_public...")
    print(f"[INFO] Users: {user_ids}")
    print(f"[INFO] Start Date: {start_date}")
    print(f"[INFO] End Date: {end_date if end_date else 'NOW'}")
    print(f"[INFO] Is_public: {is_public}")

    qs = CommendExecutionHistory.objects.filter(
        user_id__in=user_ids,
        created_date__gte=start_date,
        is_deleted=False,
        is_blocked=False
    )

    if end_date:
        qs = qs.filter(created_date__lte=end_date)

    total = qs.count()

    if total == 0:
        print("[INFO] No records found to update")
        return 0

    print(f"[INFO] Total records to update: {total}")

    with transaction.atomic():
        updated = qs.update(
            is_public=is_public,
            modified_date=timezone.now()
        )

    print(f"[SUCCESS] Updated {updated} records successfully")

    return updated
