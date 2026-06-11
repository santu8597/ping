from django.db import models
from django.conf import settings
from datetime import datetime


# Create your models here.
class SubscriptionPackageMaster(models.Model):
    package_name = models.CharField(max_length=50, blank=True, null=True)
    package_description = models.CharField(max_length=255, blank=True, null=True)
    package_points = models.DecimalField(decimal_places=2, max_digits=1000, default=0.00)
    package_amount = models.DecimalField(decimal_places=2, max_digits=1000, default=0.00)
    package_duration = models.IntegerField(default=0)
    created_date = models.DateTimeField(default=datetime.now, blank=True)
    modified_date = models.DateTimeField(default=datetime.now, blank=True)
    is_blocked = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    is_default_plan = models.BooleanField(default=False)
    ipAddress = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        db_table = 'package_master'


class UserSubscription(models.Model):
    status_choices = (
        ('earn', 'earn'),
        ('spend', 'spend')
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             limit_choices_to={'is_blocked': False, 'is_deleted': False},
                             related_name='subscribe_user_id', null=True)
    package = models.ForeignKey(SubscriptionPackageMaster, limit_choices_to={'is_blocked': False, 'is_deleted': False},
                                on_delete=models.CASCADE, related_name='package_id', null=True)
    total_points = models.DecimalField(decimal_places=2, max_digits=1000, default=0.00)
    used_points = models.DecimalField(decimal_places=2, max_digits=1000, default=0.00)
    earn_points = models.DecimalField(decimal_places=2, max_digits=1000, default=0.00)
    remaining_points = models.DecimalField(decimal_places=2, max_digits=1000, default=0.00)
    package_activation_date = models.DateField(null=True, blank=True)
    package_deactivation_date = models.DateField(null=True, blank=True)
    created_date = models.DateTimeField(default=datetime.now, blank=True)
    modified_date = models.DateTimeField(default=datetime.now, blank=True)
    insert_status = models.CharField(max_length=100, choices=status_choices, default='earn')
    command_name = models.CharField(max_length=255, null=True, blank=True)
    run_time = models.CharField(max_length=100, null=True, blank=True)
    is_blocked = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    ipAddress = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        db_table = 'user_subscription'


class SubscriptionPaymentTransaction(models.Model):
    package = models.ForeignKey(SubscriptionPackageMaster, on_delete=models.CASCADE,
                                limit_choices_to={'is_blocked': False, 'is_deleted': False},
                                related_name='subscription_package_master_id', null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             limit_choices_to={'is_blocked': False, 'is_deleted': False},
                             related_name='subscription_payment_user_id', null=True)
    package_amount = models.DecimalField(decimal_places=2, max_digits=10, blank=True, null=True)
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    transaction_status = models.CharField(max_length=50, blank=True, null=True)
    created_date = models.DateTimeField(default=datetime.now, blank=True)
    modified_date = models.DateTimeField(default=datetime.now, blank=True)
    is_blocked = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    ipAddress = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        db_table = 'subscription_payment'
