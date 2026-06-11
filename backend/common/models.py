from django.db import models
from datetime import datetime
from django.db.models import JSONField
from django.conf import settings


# Create your models here.

class Countries(models.Model):
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   limit_choices_to={'is_deleted': False, 'is_blocked': False},
                                   on_delete=models.CASCADE, related_name='country_created_by', null=True)
    country_name = models.CharField(max_length=255, null=False)
    country_code = models.CharField(max_length=5)
    country_coordinates = JSONField(default=dict)
    country_iso_code = models.CharField(max_length=10)
    created_date = models.DateTimeField(default=datetime.now, blank=True)
    modified_date = models.DateTimeField(default=datetime.now, blank=True)
    is_deleted = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    ip_address = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'countries'


class States(models.Model):
    country = models.ForeignKey(Countries, on_delete=models.CASCADE,
                                limit_choices_to={'is_deleted': False, 'is_blocked': False},
                                related_name='state_country_id', null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   limit_choices_to={'is_deleted': False, 'is_blocked': False},
                                   related_name='state_created_by', null=True)
    state_code = models.CharField(max_length=32, blank=True, null=True)
    state_name = models.CharField(max_length=255)
    state_coordinates = JSONField(default=dict)
    created_at = models.DateTimeField(default=datetime.now, blank=True)
    updated_at = models.DateTimeField(default=datetime.now, blank=True)
    is_deleted = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    ip_address = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'states'


class Cities(models.Model):
    country = models.ForeignKey(Countries, limit_choices_to={'is_deleted': False, 'is_blocked': False},
                                on_delete=models.CASCADE, related_name='city_country_id', null=True)
    state = models.ForeignKey(States, limit_choices_to={'is_deleted': False, 'is_blocked': False},
                              on_delete=models.CASCADE, related_name='city_state_id', null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   limit_choices_to={'is_deleted': False, 'is_blocked': False},
                                   on_delete=models.CASCADE, related_name='citylocation_created_by', null=True)
    city_name = models.CharField(max_length=255)
    state_code = models.CharField(max_length=32, blank=True, null=True)
    city_coordinates = JSONField(default=dict)
    created_at = models.DateTimeField(default=datetime.now, blank=True)
    updated_at = models.DateTimeField(default=datetime.now, blank=True)
    is_deleted = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    ip_address = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'cities'

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()


class UserGroupMasters(models.Model):
    enum_choices = (
        (0, 'Inactive'),
        (1, 'Active')
    )
    group_name = models.CharField(max_length=255)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=datetime.now, blank=True)
    updated_at = models.DateTimeField(default=datetime.now, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, limit_choices_to={'status': 1, 'isDeleted': False},
                                   on_delete=models.CASCADE, related_name='group_created_by', null=True)
    status = models.IntegerField(default=1, choices=enum_choices)
    ip_address = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'user_group_masters'


class UserGroup(models.Model):
    enum_choices = (
        (0, 'Inactive'),
        (1, 'Active')
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, limit_choices_to={'status': 1, 'isDeleted': False},
                             on_delete=models.CASCADE, related_name='group_user_id', null=True)
    group = models.ForeignKey(UserGroupMasters, limit_choices_to={'status': 1, 'isDeleted': False},
                              on_delete=models.CASCADE, related_name='group_id', null=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=datetime.now, blank=True)
    updated_at = models.DateTimeField(default=datetime.now, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, limit_choices_to={'status': 1, 'isDeleted': False},
                                   on_delete=models.CASCADE, related_name='user_group_created_by', null=True)
    status = models.IntegerField(default=1, choices=enum_choices)
    ip_address = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'user_group'


class MenuMasters(models.Model):
    curd = (
        ('no', 'No'),
        ('yes', 'Yes'),
    )
    enum_choices = (
        ('inactive', 'Inactive'),
        ('active', 'Active')
    )
    menu_type_choice = (
        ('admin', 'admin'),
        ('frontend', 'frontend')
    )
    menu_name = models.CharField(max_length=250)
    alt_name = models.CharField(max_length=255, blank=True, null=True)
    menu_link = models.CharField(max_length=250, blank=True, null=True)
    menu_type = models.CharField(max_length=20, choices=menu_type_choice, default='frontend')
    module = models.CharField(max_length=100, blank=True, null=True)
    parent_id = models.IntegerField(default=0)
    list_orders = models.IntegerField(blank=True, null=True)
    all_action = models.CharField(max_length=20, choices=curd, default='no')
    add_action = models.CharField(max_length=20, choices=curd, default='no')
    edit_action = models.CharField(max_length=20, choices=curd, default='no')
    delete_action = models.CharField(max_length=20, choices=curd, default='no')
    view_action = models.CharField(max_length=20, choices=curd, default='no')
    block_action = models.CharField(max_length=20, choices=curd, default='no')
    import_action = models.CharField(max_length=20, choices=curd, default='no')
    export_action = models.CharField(max_length=20, choices=curd, default='no')
    icon_class = models.CharField(max_length=255, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, limit_choices_to={'status': 1, 'isDeleted': False},
                                   on_delete=models.CASCADE, related_name='menu_created_user_id', null=True)
    created_at = models.DateTimeField(default=datetime.now, blank=True)
    updated_at = models.DateTimeField(default=datetime.now, blank=True)
    status = models.CharField(max_length=50, default='active', choices=enum_choices)

    class Meta:
        db_table = 'menu_masters'

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()


class RoleMenuPermission(models.Model):
    enum_choices = (
        (0, 'No'),
        (1, 'Yes')
    )
    menu = models.ForeignKey(MenuMasters, limit_choices_to={'status': 1, 'isDeleted': False}, on_delete=models.CASCADE,
                             related_name='role_menu_name', null=True)
    group = models.ForeignKey(UserGroupMasters, limit_choices_to={'status': 1, 'is_deleted': False},
                              on_delete=models.CASCADE, related_name='user_group', null=True)
    add = models.IntegerField(default=0, choices=enum_choices)
    edit = models.IntegerField(default=0, choices=enum_choices)
    delete = models.IntegerField(default=0, choices=enum_choices)
    view = models.IntegerField(default=0, choices=enum_choices)
    block = models.IntegerField(default=0, choices=enum_choices)
    import_field = models.IntegerField(default=0, choices=enum_choices)
    export = models.IntegerField(default=0, choices=enum_choices)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=datetime.now, blank=True)
    updated_at = models.DateTimeField(default=datetime.now, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, limit_choices_to={'status': 1, 'isDeleted': False},
                                   on_delete=models.CASCADE, related_name='role_permission_created_by', null=True)
    status = models.IntegerField(default=1, choices=enum_choices)
    ip_address = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'role_menu_permission'


class Templates(models.Model):
    enum_choices = (
        (0, 'No'),
        (1, 'Yes')
    )
    heading = models.CharField(max_length=255, blank=True, null=True)
    layout_name = models.CharField(max_length=255, blank=True, null=True)
    layout_html = models.TextField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=datetime.now, blank=True)
    updated_at = models.DateTimeField(default=datetime.now, blank=True)
    status = models.IntegerField(default=1, choices=enum_choices)

    class Meta:
        db_table = 'templates'


class ResearchPageLayouts(models.Model):
    enum_choices = (
        (0, 'No'),
        (1, 'Yes')
    )

    template_choices = (
        ('info', 'info'),
        ('graph', 'graph'),
        ('map', 'map'),
        ('datatable', 'datatable')
    )
    layout_parent = models.IntegerField(default=0)
    layout_type = models.IntegerField(default=0)
    template_type = models.CharField(max_length=255, default='info', choices=template_choices)
    heading = models.CharField(max_length=255, blank=True, null=True)
    layout_name = models.CharField(max_length=255, blank=True, null=True)
    layout_function = models.CharField(max_length=255, blank=True, null=True)
    layout_ajax_url = models.CharField(max_length=255, blank=True, null=True)
    layout_coll_no = models.CharField(max_length=255, blank=True, null=True)
    layout_position = models.IntegerField(default=0)
    layout_id = models.CharField(max_length=255, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=datetime.now, blank=True)
    updated_at = models.DateTimeField(default=datetime.now, blank=True)
    template = models.ForeignKey(Templates, limit_choices_to={'is_deleted': False, 'is_blocked': False},
                                 on_delete=models.CASCADE, related_name='template_id', null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, limit_choices_to={'status': 1, 'isDeleted': False},
                                   on_delete=models.CASCADE, related_name='layout_created_by', null=True)
    status = models.IntegerField(default=1, choices=enum_choices)

    class Meta:
        db_table = 'research_page_layouts'


class DefaultSiteSetup(models.Model):
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   limit_choices_to={'is_deleted': False, 'is_blocked': False},
                                   on_delete=models.CASCADE, related_name='settings_created_by', null=True)
    anchor_execution_limit = models.CharField(max_length=255, blank=True, null=True)
    commend_execution_ttl = models.CharField(max_length=255, blank=True, null=True)
    rd3mn_server_url = models.CharField(max_length=255, blank=True, null=True)
    rd3mn_api_key = models.CharField(max_length=255, blank=True, null=True)
    rd3mn_api_key_value = models.CharField(max_length=255, blank=True, null=True)
    rd3mn_db_url = models.CharField(max_length=255, blank=True, null=True)
    rd3mn_data_storage_db = models.CharField(max_length=255, blank=True, null=True)
    created_date = models.DateTimeField(default=datetime.now, blank=True)
    modified_date = models.DateTimeField(default=datetime.now, blank=True)
    is_blocked = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'default_site_setup'

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()


class blogs(models.Model):
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   limit_choices_to={'is_deleted': False, 'is_blocked': False},
                                   on_delete=models.CASCADE, related_name='blog_created_by', null=True)
    blog_title = models.CharField(max_length=255, blank=True, null=True)
    smoll_content = models.CharField(max_length=255, blank=True, null=True)
    content = models.TextField()
    created_at = models.DateTimeField(default=datetime.now, blank=True)
    updated_at = models.DateTimeField(default=datetime.now, blank=True)
    is_deleted = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)

    class Meta:
        db_table = 'blogs'


class blogComment(models.Model):
    blog = models.ForeignKey(blogs, limit_choices_to={'is_deleted': False, 'is_blocked': False},
                             on_delete=models.CASCADE, related_name='comment_blog_id', null=True)
    comment = models.TextField()
    # body = tinymce_models.HTMLField()
    created_at = models.DateTimeField(default=datetime.now, blank=True)
    updated_at = models.DateTimeField(default=datetime.now, blank=True)
    is_deleted = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)

    class Meta:
        db_table = 'blog_comment'



class ClusterLocationNode(models.Model):
    STATUS_CHOICES = [("ACTIVE", "Active"), ("INACTIVE", "Inactive"), ]
    name = models.CharField(max_length=255, db_index=True)
    cluster_ip = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    location = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    status = models.CharField(max_length=8,choices=STATUS_CHOICES, default="INACTIVE")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = "cluster_location_nodes"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.status})"


