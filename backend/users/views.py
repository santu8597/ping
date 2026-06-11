from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.urls import reverse
from django.shortcuts import render
from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages
from urllib.parse import urlparse

from config_env import CONFIG
from services.email_service import EmailHelper
from services_aiori_v2 import settings
from .models import CustomUser, StudentProfile, Assignment, LinkedAssignment
# from .serializers import FacultyRegistrationSerializer, StudentCreationSerializer, FacultyLoginSerializer, \
#     JWTTokenRefreshSerializer, StudentListSerializer, FacultyProfileSerializer, StudentProfileSerializer
from .serializers import StudentCreationSerializer, \
    StudentListSerializer, StudentProfileSerializer, AssignmentSerializer, LinkedAssignmentSerializer, \
    EmailVerificationCheckSerializer, UsersSerializer, FacultyWithStudentsSerializer

from rest_framework.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404

from backend.subscription.models import UserSubscription
from backend.subscription.serializers import UserSubscriptionSerializer
from datetime import datetime

from .webservice.signin_signup_view import assign_default_point, recharge_user_points
from ..services_app.common import get_remaining_points_by_user, utilize_points_handler

from django.http import JsonResponse

from ..utils.helpers import handle_uploaded_file, send_otp

import os

from ..utils.minio_handler import upload_file_to_minio, delete_file_from_minio

POINTS_PER_STUDENT = 500


class StudentCreationView(APIView):
    """Student Creation-(Only faculty can create students), On creation student will be assigned 500 points
    and 500 points will be deducted from faculty"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_faculty:
            raise PermissionDenied("Only faculty can create student profiles.")

        user_point = get_remaining_points_by_user(request.user.id)

        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        else:
            token = None

        if user_point < POINTS_PER_STUDENT:
            raise PermissionDenied("You don't have enough points to create a student profile.")

        serializer = StudentCreationSerializer(data=request.data, context={'request': request})
        try:

            if serializer.is_valid():
                # Try saving the student and deducting points in one atomic block
                with transaction.atomic():
                    student_profile, user = serializer.save()
                    # request.user.points -= POINTS_PER_STUDENT
                    utilize_points_handler(anchor_user_id=0,
                                           command_name="student_creation", run_time="",
                                           utilize_point=POINTS_PER_STUDENT, token=token)
                    assign_default_point(student_profile.user_id, "student")
                    request.user.save()
                    # email_helper = EmailHelper(user=student_profile, email_type='student_welcome')
                    # email_status = email_helper.send_email()

                    reset_link = generate_reset_link(user)

                    reset_email_content = {
                        # 'content': student_profile.password,
                        'faculty_name': f'{student_profile.faculty.first_name} {student_profile.faculty.last_name}',
                        'reset_link': reset_link
                    }

                    # Send reset email
                    email_helper = EmailHelper(user=user, email_type='student_welcome',
                                               content=reset_email_content)
                    email_helper.send_email()

                return Response({
                    "message": "Student profile created successfully! An Email Have been sent to the student mail.",
                    "student": {
                        "student_id": student_profile.student_id,
                        "institution_name": student_profile.institution_name,
                        "faculty_name": f"{student_profile.faculty.first_name} {student_profile.faculty.last_name}",
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "username": user.username,
                        "phone_no": user.phone_no
                    }
                }, status=status.HTTP_201_CREATED)

            else:
                print("Serializer erorr.............", serializer.errors)
                error_msg = next(iter(serializer.errors.values()))[0]
                return Response({"message": error_msg}, status=400)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)


class EmailVerificationCheckView(APIView):
    def post(self, request):
        serializer = EmailVerificationCheckSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            try:
                user = CustomUser.objects.get(username=username)
                if user.is_email_verified:
                    return Response({"email_verified": True}, status=status.HTTP_200_OK)
                else:
                    return Response(
                        {"email_verified": False, "detail": "Email is not verified."},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except CustomUser.DoesNotExist:
                return Response(
                    {"email_verified": False, "detail": "User not found."},
                    status=status.HTTP_404_NOT_FOUND
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FacultyStudentListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_faculty:
            raise PermissionDenied("Only faculty can view their students.")

        # Get students created by this faculty
        students = StudentProfile.objects.filter(faculty=request.user)
        serializer = StudentListSerializer(students, many=True)

        return Response({
            "faculty": f"{request.user.first_name} {request.user.last_name}",
            "students": serializer.data
        }, status=status.HTTP_200_OK)


class StudentProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get_student_profile(self, request):
        if request.user.is_student:
            return get_object_or_404(StudentProfile, user=request.user)
        elif request.user.is_faculty:
            email = request.query_params.get('email')
            if not email:
                raise PermissionDenied("Faculty must provide student email to access profile.")
            user = get_object_or_404(CustomUser, email=email, is_student=True)
            return get_object_or_404(StudentProfile, user=user)
        else:
            raise PermissionDenied("Access denied.")

    def get(self, request):
        student_profile = self.get_student_profile(request)
        serializer = StudentProfileSerializer(student_profile)
        return Response(serializer.data)

    def put(self, request):
        student_profile = self.get_student_profile(request)
        serializer = StudentProfileSerializer(student_profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request):
        if not request.user.is_faculty:
            raise PermissionDenied("Only faculty can delete student profiles.")

        email = request.query_params.get('email')
        if not email:
            return Response({"error": "Email parameter is required to delete a student."}, status=400)

        user = get_object_or_404(CustomUser, email=email, is_student=True)
        student_profile = get_object_or_404(StudentProfile, user=user)

        with transaction.atomic():
            student_profile.delete()
            user.delete()

        return Response({"message": "Student and associated user deleted successfully."}, status=204)


class IsFaculty(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_faculty


class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_student


# class AssignmentListCreateView(APIView):
#     permission_classes = [IsAuthenticated, IsFaculty]
#     def get(self, request):
#         try:
#             assignments = Assignment.objects.filter(assigned_by=request.user)
#             serializer = AssignmentSerializer(assignments, many=True)
#             return Response({
#                 "status": 1,
#                 "assignments": serializer.data
#             }, status=status.HTTP_200_OK)
#         except Exception as e:
#             return Response({
#                 "status": 0,
#                 "message": "Error fetching assignments",
#                 "error": str(e)
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
#     def post(self, request):
#         file = request.FILES.get("uploaded_doc")
#         upload_result = None
#
#         if file:
#             upload_result = upload_file_to_minio(
#                 file=file,
#                 user_id=request.user.id,
#                 base_folder=f"assignment/{request.user.id}",
#                 public=False
#             )
#             if not upload_result["success"]:
#                 return Response({
#                     "status": 0,
#                     "message": "File upload failed",
#                     "error": upload_result["error"]
#                 }, status=status.HTTP_400_BAD_REQUEST)
#
#         # Construct a clean payload (only regular data + uploaded_doc as URL)
#         payload = {
#             "assignment_name": request.data.get("assignment_name"),
#             "status": request.data.get("status", "ongoing"),
#             "remark": request.data.get("remark", "")
#         }
#
#         if upload_result:
#             payload["uploaded_doc"] = upload_result["url"]
#             print("ASASSASAS...........................", payload)
#
#         serializer = AssignmentSerializer(data=payload)
#         if serializer.is_valid():
#             serializer.save(assigned_by=request.user)
#             return Response({
#                 "status": 1,
#                 "message": "Assignment created successfully",
#                 "data": serializer.data
#             }, status=status.HTTP_201_CREATED)
#
#         return Response({
#             "status": 0,
#             "message": "Assignment creation failed",
#             "errors": serializer.errors
#         }, status=status.HTTP_400_BAD_REQUEST)
class AssignmentListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsFaculty]

    def get(self, request):
        return handle_assignment_get(request)

    def post(self, request):
        return handle_assignment_post(request)


class AssignmentDetailView(APIView):
    permission_classes = [IsAuthenticated, IsFaculty]

    def get_object(self, id, user):
        return get_object_or_404(Assignment, id=id, assigned_by=user)

    def get(self, request, id):
        assignment = self.get_object(id, request.user)
        serializer = AssignmentSerializer(assignment)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, id):
        assignment = self.get_object(id, request.user)
        serializer = AssignmentSerializer(assignment, data=request.data)
        if serializer.is_valid():
            serializer.save(modified_date=datetime.now())
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, id):
        assignment = self.get_object(id, request.user)
        serializer = AssignmentSerializer(assignment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(modified_date=datetime.now())
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # def delete(self, request, id):
    #     assignment = self.get_object(id, request.user)
    #
    #     # Get the file path before deleting the assignment
    #     file_path = assignment.uploaded_doc.path if assignment.uploaded_doc else None
    #
    #     # Delete the assignment from the database
    #     assignment.delete()
    #
    #     # Delete the file from the file system
    #     if file_path and os.path.isfile(file_path):
    #         os.remove(file_path)
    #
    #     return Response({"status": 1, "message": "Assignment and associated file deleted successfully."},
    #                     status=status.HTTP_200_OK)
    def delete(self, request, id):
        assignment = self.get_object(id, request.user)

        # Extract object key from MinIO URL
        # object_key = assignment.uploaded_doc.split(f'/{CONFIG.AWS_STORAGE_BUCKET_NAME}/')[-1] if assignment.uploaded_doc else None
        object_key = extract_object_key(assignment.uploaded_doc)

        print("Delete object key.................", object_key)
        # Delete file from MinIO first
        if object_key:
            delete_file_from_minio(object_key)

        # Clear the URL before deletion (optional, but keeps record clean if you ever soft-delete)
        assignment.uploaded_doc = None
        assignment.filename = None
        assignment.save()

        # Delete the DB record
        assignment.delete()

        return Response({
            "status": 1,
            "message": "Assignment and associated file deleted successfully."
        }, status=status.HTTP_200_OK)


# ------------------ STUDENT ASSIGNMENT LIST FOR TEACHER ------------------ #

class StudentAssignmentListView(APIView):
    permission_classes = [IsAuthenticated, IsFaculty]

    def get(self, request, student_id):
        student = get_object_or_404(
            CustomUser,
            id=student_id,
            is_student=True,
            is_blocked=False,
            is_deleted=False
        )

        linked_assignments = LinkedAssignment.objects.filter(student=student)

        serializer = LinkedAssignmentSerializer(linked_assignments, many=True)
        return Response({
            "status": 1,
            "student": f"{student.first_name} {student.last_name}",
            "assignments": serializer.data
        }, status=status.HTTP_200_OK)


# ------------------ LINKED ASSIGNMENT (Student) ------------------ #

class LinkedAssignmentListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):
        linked = LinkedAssignment.objects.filter(student=request.user)
        serializer = LinkedAssignmentSerializer(linked, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = LinkedAssignmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(student=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LinkedAssignmentDetailView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def get_object(self, id, user):
        return get_object_or_404(LinkedAssignment, id=id, student=user)

    def get(self, request, id):
        linked = self.get_object(id, request.user)
        serializer = LinkedAssignmentSerializer(linked)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, id):
        linked = self.get_object(id, request.user)
        serializer = LinkedAssignmentSerializer(linked, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        linked = self.get_object(id, request.user)
        linked.delete()
        return Response({"status": 1, "message": "Linked query deleted successfully."},
                        status=status.HTTP_200_OK)


class AssignmentLinkedQueriesView(APIView):
    permission_classes = [IsAuthenticated, IsFaculty]

    def get(self, request, assignment_id):
        assignment = get_object_or_404(
            Assignment,
            id=assignment_id,
            assigned_by=request.user
        )

        linked_queries = LinkedAssignment.objects.filter(assignment=assignment)

        if not linked_queries.exists():
            return Response({
                "status": 0,
                "message": "No linked queries found for this assignment."
            }, status=status.HTTP_200_OK)

        serializer = LinkedAssignmentSerializer(linked_queries, many=True)
        return Response({
            "status": 1,
            "assignment": assignment.assignment_name,
            "linked_queries": serializer.data
        }, status=status.HTTP_200_OK)


class StudentPointUtilizationView(APIView):
    """To view from faculty's window point utilization by student"""
    permission_classes = [IsAuthenticated, IsFaculty]  # You must have this IsFaculty permission

    def get(self, request, student_id):
        # Check if the user is a student
        student = get_object_or_404(
            CustomUser,
            id=student_id,
            is_student=True,
            is_deleted=False,
            is_blocked=False
        )

        rs = UserSubscription.objects.filter(user_id=student.id, is_deleted=False).order_by('-id')[:100]

        response_data = {}

        if rs:
            serializer = UserSubscriptionSerializer(rs, many=True)
            response_data['status'] = 1
            response_data['message'] = f"Points used by student ID {student_id} retrieved."
            response_data['utilization'] = serializer.data
        else:
            response_data['status'] = 0
            response_data['message'] = f"No point utilization found for student ID {student_id}."
            response_data['utilization'] = []

        return JsonResponse(response_data, status=200)


class RechargePointsView(APIView):
    """Recharging points to students by faculty"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_faculty:
            raise PermissionDenied("Only faculty can recharge points to a student.")

        student_user_id = request.data.get('student_user_id')
        points_to_recharge = int(request.data.get('points', 0))

        if not student_user_id or points_to_recharge <= 0:
            return Response({"error": "Invalid student or points."}, status=400)

        faculty_points = get_remaining_points_by_user(request.user.id)
        if faculty_points < points_to_recharge:
            raise PermissionDenied("You don't have enough points to recharge.")

        student_user = get_object_or_404(CustomUser, id=student_user_id, is_student=True)

        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

        with transaction.atomic():
            # Deduct from faculty
            utilize_points_handler(
                anchor_user_id=0,
                command_name="recharge_to_student",
                run_time="",
                utilize_point=points_to_recharge,
                token=token
            )

            # Credit to student
            recharge_user_points(student_user.id, points_to_recharge, "recharged_from_faculty")
        return Response({
            "message": f"{points_to_recharge} points successfully transferred to {student_user.first_name}."
        }, status=200)


class StudentAssignmentsView(APIView):
    """For students to view list of assignments created by their faculty"""
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):
        try:
            # Ensure the logged-in user is a student
            student_profile = StudentProfile.objects.get(user=request.user)

            # Get the faculty assigned to this student
            faculty = student_profile.faculty

            # Fetch assignments created by that faculty
            assignments = Assignment.objects.filter(assigned_by=faculty)

            serializer = AssignmentSerializer(assignments, many=True)
            return Response({"status": 1, "assignments": serializer.data}, status=status.HTTP_200_OK)

        except StudentProfile.DoesNotExist:
            return Response(
                {"status": 0, "message": "Student profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"status": 0, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UploadProfileImageView(APIView):
    """Uploading Profile picture"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        file = request.FILES.get('profile_image')

        if not file:
            return Response({"status": 0, "msg": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            relative_path = handle_uploaded_file(file, user_id=user.id, public=True)
            if not relative_path:
                return Response({"status": 0, "msg": "File upload failed."},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Save path to user model
            user.profile_image = relative_path
            user.save(update_fields=["profile_image"])

            return Response({
                "status": 1,
                "msg": "Profile image uploaded successfully.",
                "image_url": f"{settings.MEDIA_URL}{relative_path}"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": 0,
                "msg": "Something went wrong while uploading.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ForgotPasswordView(APIView):
    permission_classes = []

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required"}, status=400)

        try:
            user = CustomUser.objects.get(email=email, is_active=True)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        # token_generator = PasswordResetTokenGenerator()
        # token = token_generator.make_token(user)
        #
        # # Build reset link (adjust frontend URL accordingly)
        # reset_path = reverse('users:reset-password-form')
        # reset_link = f"{CONFIG.HOST_URL}{reset_path}?uid={user.pk}&token={token}"

        reset_link = generate_reset_link(user)

        # Send reset email
        email_helper = EmailHelper(user=user, email_type='reset', content={'reset_link': reset_link})
        email_helper.send_email()

        return Response({"message": "Password reset email sent."}, status=200)


class ResetPasswordView(View):
    permission_classes = []

    def get(self, request):
        # Render password reset form with uid and token as hidden inputs
        uid = request.GET.get('uid')
        token = request.GET.get('token')

        return render(request, 'services_app/reset_password.html', {
            'uid': uid,
            'token': token
        })

    def post(self, request):
        uid = request.POST.get('uid')
        token = request.POST.get('token')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        if not all([uid, token, password, password_confirm]):
            messages.error(request, "Missing required parameters.")
            return redirect(request.path)

        if password != password_confirm:
            messages.error(request, "Passwords do not match.")
            return redirect(request.path)

        try:
            user = CustomUser.objects.get(pk=uid)
        except CustomUser.DoesNotExist:
            messages.error(request, "Invalid user.")
            return redirect(request.path)

        if user.is_student:
            user.is_email_verified = True
            user.save()

        token_generator = PasswordResetTokenGenerator()
        if not token_generator.check_token(user, token):
            messages.error(request, "Invalid or expired token.")
            return redirect(request.path)

        user.set_password(password)
        user.save()

        messages.success(request, "Password reset successful. Please log in.")
        return redirect('services_app:index')


def generate_reset_link(user: CustomUser):
    token_generator = PasswordResetTokenGenerator()
    token = token_generator.make_token(user)

    # Build reset link (adjust frontend URL accordingly)
    reset_path = reverse('users:reset-password-form')
    reset_link = f"{CONFIG.HOST_URL}{reset_path}?uid={user.pk}&token={token}"

    return reset_link


def get_assignment_data(obj):
    return {
        "id": obj.id,
        "assignment_name": obj.assignment_name,
        "filename": obj.filename,
        "uploaded_doc": obj.uploaded_doc,
        "status": obj.status,
        "remark": obj.remark,
        "assigned_by": obj.assigned_by.id,
        "assigned_by_name": f"{obj.assigned_by.first_name} {obj.assigned_by.last_name}".strip(),
        "created_date": obj.created_date,
        "modified_date": obj.modified_date,
    }


def get_assignment_list_data(queryset):
    return [get_assignment_data(obj) for obj in queryset]


def handle_assignment_get(request):
    try:
        assignments = Assignment.objects.filter(assigned_by=request.user).order_by('-created_date')
        data = get_assignment_list_data(assignments)

        return Response({
            "status": 1,
            "assignments": data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "status": 0,
            "message": "Error fetching assignments",
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def handle_assignment_post(request):
    file = request.FILES.get("uploaded_doc")
    uploaded_url = None

    if file:
        upload_result = upload_file_to_minio(
            file=file,
            user_id=request.user.id,
            base_folder=f"assignment",
            public=True
        )

        if not upload_result["success"]:
            return Response({
                "status": 0,
                "message": "File upload failed",
                "error": upload_result["error"]
            }, status=status.HTTP_400_BAD_REQUEST)

        uploaded_url = upload_result["url"]

    try:
        assignment = Assignment.objects.create(
            assignment_name=request.data.get("assignment_name"),
            remark=request.data.get("remark", ""),
            uploaded_doc=uploaded_url,
            status=request.data.get("status", "ongoing"),
            assigned_by=request.user
        )

        return Response({
            "status": 1,
            "message": "Assignment created successfully",
            "data": get_assignment_data(assignment)
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            "status": 0,
            "message": "Assignment creation failed",
            "error": str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


def extract_object_key(file_url):
    """
    Extract the object key from a full MinIO URL.
    E.g. from: http://minio-url/bucket-name/assignment/123/file.pdf
    Returns: assignment/123/file.pdf
    """
    if not file_url:
        return None

    parsed_url = urlparse(file_url)
    path_parts = parsed_url.path.lstrip('/').split('/', 1)

    if len(path_parts) == 2:
        return path_parts[1]  # everything after the bucket name
    return None


class UserStatsAPIView(APIView):
    def get(self, request):
        try:
            # Query params
            is_faculty = request.GET.get('is_faculty')
            is_student = request.GET.get('is_student')

            all_users = CustomUser.objects.all()  # complete user set
            users = all_users  # filtered set

            if is_faculty is not None:
                users = users.filter(is_faculty=is_faculty.lower() == "true")
            if is_student is not None:
                users = users.filter(is_student=is_student.lower() == "true")

            # Base response
            data = {
                "status": 1,
                "total_users": all_users.count(),
                "total_faculties": all_users.filter(is_faculty=True).count(),
                "total_students": all_users.filter(is_student=True).count(),
            }

            # If user requested faculty details
            if is_faculty and is_faculty.lower() == "true":
                data["faculty_users"] = UsersSerializer(users, many=True).data

            # If user requested student details
            if is_student and is_student.lower() == "true":
                data["student_users"] = UsersSerializer(users, many=True).data

            return Response(data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"status": 0, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class FacultyStudentAPIView(APIView):
    def get(self, request):
        faculty_id = request.GET.get("faculty_id")

        if faculty_id:
            faculties = CustomUser.objects.filter(is_faculty=True, id=faculty_id)
        else:
            faculties = CustomUser.objects.filter(is_faculty=True)
        # Check if faculty exists and has students
        if not faculties.exists():
            return Response({
                "status": 0,
                "message": "No faculty found with given ID" if faculty_id else "No faculties found",
                "data": []
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = FacultyWithStudentsSerializer(faculties, many=True)

        # Check if all faculties have zero students
        has_students = any(len(faculty['students']) > 0 for faculty in serializer.data)

        if not has_students:
            return Response({
                "status": 1,
                "message": "No enrolled students found for this faculty" if faculty_id else "No enrolled students found under any faculty",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        return Response({
            "status": 1,
            "message": "Faculty and student details fetched successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
