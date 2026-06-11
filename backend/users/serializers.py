from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from backend.users.models import CustomUser, StudentProfile, DiscussionForum,DiscussionReply,ReplyVote, DiscussionCategories, UsersDomain, \
    UsersHostGroupDomain, UsersZone, UsersZoneAreaDetails, UsersHostGroup, Assignment, LinkedAssignment
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError
# Serializer for Token Refresh (Optional)
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
User = get_user_model()


class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_active',
            'last_login',
            'is_blocked',
            'created_date',
            'modified_date',
            'is_email_verified',
            'is_faculty',
            'is_student',
            'designation',
            'phone_no',
            'institution_name'

        ]


class SignupSerializer(serializers.ModelSerializer):
    # username = serializers.CharField(required=True, allow_blank=False, max_length=200)
    password = serializers.CharField(required=True, allow_blank=False, max_length=200)
    phone_no = serializers.CharField(required=False, allow_blank=False, max_length=20)
    email = serializers.CharField(required=True, allow_blank=False, max_length=200)
    first_name = serializers.CharField(required=True, allow_blank=False, max_length=200)
    last_name = serializers.CharField(required=True, allow_blank=False, max_length=200)
    designation = serializers.CharField(required=True, allow_blank=False, max_length=200)
    is_faculty = serializers.BooleanField(required=False)
    company_name = serializers.CharField(required=False, allow_blank=True, max_length=100)
    institution_name = serializers.CharField(required=False, allow_blank=True, max_length=100)
    address = serializers.CharField(required=False, allow_blank=True, max_length=100)
    pin_code = serializers.IntegerField(required=False, allow_null=True)
    country = serializers.CharField(required=False, allow_blank=True, max_length=100)
    city = serializers.CharField(required=False, allow_blank=True, max_length=100)
    state = serializers.CharField(required=False, allow_blank=True, max_length=100)
    is_phone_verified = serializers.CharField(required=False, allow_blank=True, max_length=100)
    is_email_verified = serializers.CharField(required=True, allow_blank=True, max_length=100)

    class Meta:
        model = get_user_model()
        fields = ['email', 'phone_no', 'password', 'first_name', 'last_name', 'designation', 'is_faculty',
                  'company_name', 'institution_name', 'country', 'city', 'state', 'address', 'pin_code',
                  'is_phone_verified', 'is_email_verified']


class ProfileViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = "__all__"


class LoginSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=False, allow_blank=True, write_only=True)
    email = serializers.EmailField(required=True, write_only=True, label="Email Address")
    token = serializers.CharField(allow_blank=True, read_only=True)
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

    class Meta(object):
        many = True
        model = CustomUser
        fields = ['id', 'email', 'username', 'password', 'token', 'first_name', 'last_name', 'email', 'is_superuser',
                  'is_active', 'is_staff', 'last_login']

class EmailVerificationCheckSerializer(serializers.Serializer):
    username = serializers.CharField()

class DiscussionCategoryViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscussionCategories
        fields = "__all__"


class DiscussionForumViewSerializer(serializers.ModelSerializer):
    user_details = serializers.SerializerMethodField()

    class Meta:
        model = DiscussionForum
        fields = "__all__"

    def get_user_details(self, DiscussionForum):
        rs = CustomUser.objects.filter(id=DiscussionForum.user_id).first()
        user_data = [{'user_name': rs.first_name + ' ' + rs.last_name, 'email': rs.email}]
        return user_data


class DomainViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsersDomain
        fields = "__all__"


class UsersZoneViewSerializer(serializers.ModelSerializer):
    # area_details = serializers.SerializerMethodField()
    class Meta:
        model = UsersZone
        fields = [
            'id',
            'user_zone_name',
            'user_zone_country_name',
            'user_zone_state_name',
            'created_date',
            'user',
            'user_anchor_latitudes',
            'user_anchor_longitudes',
            'user_anchor_locations',
            'user_anchor_ids',
            'user_anchor_names'
        ]


class UserReportProfileViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'date_joined', 'phone_no', 'designation',
                  'company_name', 'address', 'pin_code', 'is_faculty', 'is_student', 'institution_name']


class UserReportDomainDetSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsersDomain
        fields = ['id', 'domain_name', 'domain_ip', 'created_date', 'modified_date', 'is_public', 'is_blocked']


class UserHostGroupDomainViewSerializer(serializers.ModelSerializer):
    domain = DomainViewSerializer()

    class Meta:
        model = UsersHostGroupDomain
        fields = "__all__"


class UserHostGroupViewSerializer(serializers.ModelSerializer):
    domain_details = serializers.SerializerMethodField()

    class Meta:
        model = UsersHostGroup
        fields = ['id', 'host_group_name', 'created_date', 'user', 'domain_details']

    def get_domain_details(self, UsersHostGroup):
        return []


class AreaDetailsViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsersZoneAreaDetails
        fields = ['id', 'area_name', 'created_date']




# Serializer for Student Creation
class StudentCreationSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    student_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    institution_name = serializers.CharField(required=False)
    phone_no = serializers.CharField()

    class Meta:
        model = CustomUser  # This should be the CustomUser model, not StudentProfile.
        fields = ['first_name', 'last_name', 'email', 'password', 'student_id', 'institution_name', 'phone_no']

    def validate(self, data):
        # Validate that student_id (which is used as the username) is unique
        if CustomUser.objects.filter(phone_no=data['phone_no']).exists():
            raise serializers.ValidationError("This phone no is already in use.")

        # Validate that the email is unique
        if CustomUser.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("This email is already registered.")

        return data

    def create(self, validated_data):
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context is required.")

        with transaction.atomic():
            # Create the user (CustomUser) for the student
            user = CustomUser.objects.create_user(
                username=validated_data['email'],
                email=validated_data['email'],
                first_name=validated_data['first_name'],
                last_name=validated_data['last_name'],
                password=validated_data['password'],
                phone_no=validated_data['phone_no'],
                is_student=True,  # Set is_student to True
                designation='student',
                created_date=timezone.now(),
                modified_date=timezone.now(),
            )

            # Create the student profile and link it to the user
            student_profile = StudentProfile.objects.create(
                user=user,
                faculty=request.user,  # Authenticated faculty
                student_id=validated_data['student_id'],
                institution_name=validated_data.get('institution_name', '')
            )

        return student_profile, user




class StudentListSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email')
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    phone_no = serializers.CharField(source='user.phone_no')

    class Meta:
        model = StudentProfile
        fields = ['user_id', 'student_id', 'institution_name', 'email', 'first_name', 'last_name', 'created_at',
                  'phone_no']


class StudentProfileSerializer(serializers.ModelSerializer):
    email = serializers.ReadOnlyField(source='user.email')
    first_name = serializers.ReadOnlyField(source='user.first_name')
    last_name = serializers.ReadOnlyField(source='user.last_name')
    user_id = serializers.ReadOnlyField(source='user.id')

    class Meta:
        model = StudentProfile
        fields = ['student_id', 'institution_name', 'user_id', 'email', 'first_name', 'last_name']


class AssignmentSerializer(serializers.ModelSerializer):
    assigned_by_name = serializers.SerializerMethodField()
    uploaded_doc = serializers.URLField(required=False, allow_null=True)

    class Meta:
        model = Assignment
        fields = '__all__'
        read_only_fields = ['assigned_by', 'filename', 'created_date', 'modified_date']

    def get_assigned_by_name(self, obj):
        user = obj.assigned_by  # This is a User instance
        return f"{user.first_name} {user.last_name}".strip()


class LinkedAssignmentSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    designation = serializers.SerializerMethodField()
    student_id = serializers.SerializerMethodField()
    assignment_name = serializers.SerializerMethodField()

    class Meta:
        model = LinkedAssignment

        fields = [
            'id',
            'remark',
            'command',
            'query_id',
            'zone',
            'query_type',
            'submitted_at',
            'assignment',
            'assignment_name',
            'student',
            'student_name',
            'designation',
            'student_id',
        ]
        read_only_fields = ['student']

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"

    def get_designation(self, obj):
        return f"{obj.student.designation}"

    def get_student_id(self, obj):
        try:
            return obj.student.student_profile.student_id
        except StudentProfile.DoesNotExist:
            return None

    def get_assignment_name(self, obj):
        return obj.assignment.assignment_name if obj.assignment else None



class DiscussionReplySerializer(serializers.ModelSerializer):
    child_replies = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    vote_count = serializers.SerializerMethodField()
    user_has_voted = serializers.SerializerMethodField()

    class Meta:
        model = DiscussionReply
        fields = ['id', 'user', 'content', 'created_date', 'child_replies', 'vote_count', 'user_has_voted']

    def get_user(self, obj):
        return obj.user.get_full_name() or obj.user.username or obj.user.email

    def get_vote_count(self, obj):
        return ReplyVote.objects.filter(reply=obj).count()

    def get_user_has_voted(self, obj):
        request = self.context.get('request')
        user = request.user if request else None
        if user and user.is_authenticated:
            return ReplyVote.objects.filter(user=user, reply=obj).exists()
        return False

    def get_child_replies(self, obj):
        child_qs = obj.child_replies.filter(is_deleted=False, is_blocked=False).order_by('created_date')
        # pass context to include request in nested serializers
        return DiscussionReplySerializer(child_qs, many=True, context=self.context).data


class FacultyWithStudentsSerializer(serializers.ModelSerializer):
    total_students = serializers.SerializerMethodField()
    students = StudentListSerializer(many=True, read_only=True)  # uses related_name='students'

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'total_students', 'students']

    def get_total_students(self, obj):
        return obj.students.count()

