from django.contrib.auth.models import AbstractUser
from django.db import models
from backend.common.models import Countries, Cities, States
from django.conf import settings
from datetime import datetime
from django.db.models import JSONField


class CustomUser(AbstractUser):
    is_faculty = models.BooleanField(default=False, null=True, blank=True)
    is_student = models.BooleanField(default=False, null=True, blank=True)
    phone_no = models.CharField(max_length=20, default="", blank=True)
    verified_code = models.CharField(max_length=30, blank=True, null=True)  # not needed
    is_phone_verified = models.BooleanField(default=False, verbose_name='Phone Verification')
    is_email_verified = models.BooleanField(default=False, verbose_name='Email Verification')
    designation = models.CharField(max_length=225, null=True, blank=True)
    institution_name = models.CharField(max_length=100, default="", blank=True, null=True)
    address = models.CharField(max_length=255, default="", blank=True, null=True)
    profile_image = models.CharField(max_length=225, blank=True, null=True)
    pin_code = models.IntegerField(default=0, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    is_blocked = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    ipAddress = models.GenericIPAddressField(blank=True, null=True)
    user_pk = models.CharField(max_length=255, default="", blank=True, null=True)
    github_url = models.URLField(max_length=225, null=True, blank=True)
    hndb_url = models.URLField(max_length=225, null=True, blank=True)
    linkedin_url = models.URLField(max_length=225, null=True, blank=True)

    # Added from old model
    country = models.ForeignKey(Countries, on_delete=models.CASCADE, related_name='user_country', blank=True,
                                null=True)
    state = models.ForeignKey(States, on_delete=models.CASCADE, related_name='user_state', blank=True, null=True)
    city = models.ForeignKey(Cities, on_delete=models.CASCADE, related_name='user_city', blank=True, null=True)
    latitude = models.CharField(max_length=255, null=True, blank=True)
    longitude = models.CharField(max_length=255, null=True, blank=True)
    company_name = models.CharField(max_length=100, default="", blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    modified_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        db_table = 'auth_user'
        ordering = ['-created_at']

    def get_name(self):
        return self.first_name + ' ' + self.last_name

    def __str__(self):
        return self.username


class StudentProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='student_profile')
    faculty = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='students')
    student_id = models.CharField(max_length=100, blank=True, null=True)
    institution_name = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Student"
        verbose_name_plural = "Students"
        db_table = "student_user"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} under {self.faculty.username}"


class UserSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='user_session')
    lat = models.FloatField(null=True, blank=True)
    long = models.FloatField(null=True, blank=True)
    public_ip = models.GenericIPAddressField(null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    isp_details = models.CharField(max_length=255, null=True, blank=True)
    last_login = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.last_login}"


class DiscussionCategories(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='user_discussion_categories')
    category_name = models.CharField(max_length=255, blank=True, null=True)
    created_date = models.DateTimeField(default=datetime.now, blank=True)
    modified_date = models.DateTimeField(default=datetime.now, blank=True)
    is_blocked = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'discussion_categories'



class DiscussionForum(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_discussion')
    discussion_category = models.ForeignKey(DiscussionCategories, on_delete=models.CASCADE,
                                            related_name='discussion_category_id')
    discussion = models.TextField(blank=True, null=True)
    created_date = models.DateTimeField(default=datetime.now, blank=True)
    modified_date = models.DateTimeField(default=datetime.now, blank=True)
    is_blocked = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    
    @property
    def vote_count(self):
        return self.votes.aggregate(total=models.Sum('value'))['total'] or 0

    class Meta:
        db_table = 'discussion_forum'


class DiscussionReply(models.Model):
    discussion = models.ForeignKey(DiscussionForum, on_delete=models.CASCADE, related_name='replies')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_replies')
    content = models.TextField(default="(no content)")
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='child_replies')
    created_date = models.DateTimeField(default=datetime.now)
    modified_date = models.DateTimeField(default=datetime.now)
    is_blocked = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    
    @property
    def vote_count(self):
        return self.votes.aggregate(total=models.Sum('value'))['total'] or 0

    class Meta:
        db_table = 'discussion_replies'
    
    def get_user(self):
        return self.user

class DiscussionVote(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    discussion = models.ForeignKey(DiscussionForum, on_delete=models.CASCADE, related_name='votes')
    value = models.SmallIntegerField(default=1)  # 1 = upvote, -1 = downvote (optional)

    class Meta:
        unique_together = ('user', 'discussion')
        db_table = 'discussion_votes'


class ReplyVote(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reply = models.ForeignKey(DiscussionReply, on_delete=models.CASCADE, related_name='votes')
    value = models.SmallIntegerField(default=1)

    class Meta:
        unique_together = ('user', 'reply')
        db_table = 'replies_votes'
        

class UsersDomain(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_domain')
    domain_name = models.CharField(max_length=255, blank=True, null=True)
    domain_ip = models.CharField(max_length=255, blank=True, null=True)
    created_date = models.DateTimeField(default=datetime.now, blank=True)
    modified_date = models.DateTimeField(default=datetime.now, blank=True)
    is_public = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'users_domain'


class UsersZone(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='users_zone')
    user_zone_name = models.CharField(max_length=255, blank=True, null=True)
    user_zone_country_name = models.CharField(max_length=255, blank=True, null=True)
    user_zone_state_name = models.CharField(max_length=255, blank=True, null=True)
    user_anchor_ids = JSONField(default=list, blank=True, null=True)
    user_anchor_names = JSONField(default=list, blank=True, null=True)
    user_anchor_latitudes = JSONField(default=list, blank=True, null=True)
    user_anchor_longitudes = JSONField(default=list, blank=True, null=True)
    user_anchor_locations = JSONField(default=list, blank=True, null=True)
    created_date = models.DateTimeField(default=datetime.now, blank=True)
    modified_date = models.DateTimeField(default=datetime.now, blank=True)
    is_blocked = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'user_zone'


class UsersZoneAreaDetails(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='users_zone_area')
    user_zone = models.ForeignKey(UsersZone, on_delete=models.CASCADE, related_name='zone_area_id')
    area_name = models.CharField(max_length=255, blank=True, null=True)
    created_date = models.DateTimeField(default=datetime.now, blank=True)
    modified_date = models.DateTimeField(default=datetime.now, blank=True)
    is_blocked = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'user_zone_area_details'


class UsersHostGroup(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_host_group')
    host_group_name = models.CharField(max_length=255, blank=True, null=True)
    created_date = models.DateTimeField(default=datetime.now, blank=True)
    modified_date = models.DateTimeField(default=datetime.now, blank=True)
    is_blocked = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'users_host_group'


class UsersHostGroupDomain(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='group_domain')
    user_host_group = models.ForeignKey(UsersHostGroup, on_delete=models.CASCADE, related_name='user_host_group_id')
    domain = models.ForeignKey(UsersDomain, on_delete=models.CASCADE, related_name='user_domain_id')
    created_date = models.DateTimeField(default=datetime.now, blank=True)
    modified_date = models.DateTimeField(default=datetime.now, blank=True)
    is_blocked = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'user_host_group_domain'


def user_assignment_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/assignment/<user_id>/<filename>
    return f'assignment/{instance.assigned_by.id}/{filename}'


class Assignment(models.Model):
    STATUS_CHOICES = (
        ('ongoing', 'Ongoing'),
        ('closed', 'Closed'),
    )

    id = models.AutoField(primary_key=True)
    assignment_name = models.CharField(max_length=255)
    uploaded_doc = models.URLField(max_length=1000, null=True, blank=True)
    filename = models.CharField(max_length=255, blank=True, null=True, editable=False)

    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'is_faculty': True, 'is_blocked': False, 'is_deleted': False},
        related_name='teacher_assignments'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ongoing')
    remark = models.TextField(blank=True, null=True)

    created_date = models.DateTimeField(default=datetime.now, blank=True)
    modified_date = models.DateTimeField(default=datetime.now, blank=True)

    class Meta:
        db_table = 'assignment'
        ordering = ['-created_date']

    def save(self, *args, **kwargs):
        if self.uploaded_doc:
            # Remove query parameters from URL
            clean_path = self.uploaded_doc.split('?')[0]
            self.filename = clean_path.split('/')[-1]
        super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.assignment_name} by {self.assigned_by.get_full_name()}"


class LinkedAssignment(models.Model):
    id = models.AutoField(primary_key=True)

    assignment = models.ForeignKey(
        'Assignment',
        on_delete=models.CASCADE,
        related_name='student_assignments'
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assignee_student',
        limit_choices_to={'is_student': True, 'is_blocked': False, 'is_deleted': False}
    )

    remark = models.TextField(blank=True, null=True)
    command = models.CharField(max_length=255, blank=True, null=True)
    zone = models.CharField(max_length=255, blank=True, null=True)
    query_type = models.CharField(max_length=255, blank=True, null=True)
    query_id = models.CharField(max_length=100, blank=True, null=True)
    submitted_at = models.DateTimeField(default=datetime.now)

    class Meta:
        db_table = 'linked_assignment'
        verbose_name = 'Student Assignment'
        verbose_name_plural = 'Student Assignments'
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['assignment']),
            models.Index(fields=['student']),
        ]

    def __str__(self):
        return f"Assignment #{self.assignment.id} - Student #{self.student.id}"
