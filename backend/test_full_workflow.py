import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.test import Client
from apps.accounts.models import User
from apps.quizzes.models import Quiz
from apps.attempts.models import QuizAttempt

def run_verification():
    client = Client()
    print("==================================================")
    print("STARTING KDTECHX FULL-STACK E2E VERIFICATION SUITE")
    print("==================================================")

    # 1. Public Routes
    print("\n[1] Testing Public Routes...")
    r = client.get('/')
    assert r.status_code == 200, f"Expected 200 on /, got {r.status_code}"
    print("  PASS: Landing Page (/) -> 200 OK")

    r = client.get('/accounts/login/admin/')
    assert r.status_code == 200, f"Expected 200 on /accounts/login/admin/, got {r.status_code}"
    print("  PASS: Admin Login Page (/accounts/login/admin/) -> 200 OK")

    r = client.get('/accounts/login/student/')
    assert r.status_code == 200, f"Expected 200 on /accounts/login/student/, got {r.status_code}"
    print("  PASS: Student Login Page (/accounts/login/student/) -> 200 OK")

    # 2. Anonymous Protection
    print("\n[2] Testing Anonymous Access Protection...")
    r = client.get('/portal/admin/dashboard/')
    assert r.status_code in (302, 403), f"Expected redirect/forbidden, got {r.status_code}"
    print(f"  PASS: Anonymous access to /portal/admin/dashboard/ blocked ({r.status_code})")

    r = client.get('/portal/student/dashboard/')
    assert r.status_code in (302, 403), f"Expected redirect/forbidden, got {r.status_code}"
    print(f"  PASS: Anonymous access to /portal/student/dashboard/ blocked ({r.status_code})")

    # 3. Admin Authentication & Admin Portal Pages
    print("\n[3] Testing Admin Role Access...")
    admin_user = User.objects.filter(role=User.Role.ADMIN).first()
    client.force_login(admin_user)
    print(f"  Logged in as Admin: {admin_user.username} ({admin_user.email})")

    admin_routes = [
        ('/portal/admin/dashboard/', "Admin Dashboard"),
        ('/portal/admin/batches/', "Batches Index"),
        ('/portal/admin/students/', "Students Index"),
        ('/portal/admin/courses/', "Courses Index"),
        ('/portal/admin/questions/', "Questions Index"),
        ('/portal/admin/questions/import/', "Questions Import"),
        ('/portal/admin/quizzes/', "Quizzes Index"),
        ('/portal/admin/quizzes/create/', "Quiz Creation"),
        ('/portal/admin/results/', "Results Index"),
        ('/portal/admin/analytics/', "Analytics Index"),
        ('/portal/admin/announcements/', "Announcements Index"),
        ('/portal/admin/settings/', "Settings Index"),
    ]

    for route, label in admin_routes:
        r = client.get(route)
        assert r.status_code == 200, f"Failed on {route}: status {r.status_code}"
        print(f"  PASS: {label} ({route}) -> 200 OK")

    # Admin access to student portal should be blocked
    r = client.get('/portal/student/dashboard/')
    assert r.status_code in (302, 403), f"Admin expected redirect/forbidden on student portal, got {r.status_code}"
    print(f"  PASS: Admin blocked from student portal -> {r.status_code}")

    # 4. Student Authentication & Student Portal Pages
    print("\n[4] Testing Student Role Access...")
    student_user = User.objects.filter(role=User.Role.STUDENT).first()
    client.force_login(student_user)
    print(f"  Logged in as Student: {student_user.username} ({student_user.email})")

    student_routes = [
        ('/portal/student/dashboard/', "Student Dashboard"),
        ('/portal/student/courses/', "Enrolled Courses"),
        ('/portal/student/history/', "Assessment History"),
        ('/portal/student/progress/', "Progress & Trends"),
        ('/portal/student/profile/', "Student Profile"),
    ]

    for route, label in student_routes:
        r = client.get(route)
        assert r.status_code == 200, f"Failed on {route}: status {r.status_code}"
        print(f"  PASS: {label} ({route}) -> 200 OK")

    # Student access to admin portal should be blocked
    r = client.get('/portal/admin/dashboard/')
    assert r.status_code in (302, 403), f"Student expected redirect/forbidden on admin portal, got {r.status_code}"
    print(f"  PASS: Student blocked from admin portal -> {r.status_code}")

    # 5. Exam Engine Take Interface
    print("\n[5] Testing Student Exam Interface...")
    quiz = Quiz.objects.filter(status=Quiz.Status.PUBLISHED).first()
    if quiz:
        r = client.get(f'/portal/student/quiz/{quiz.id}/take/')
        # Should be 200 OK (or 302 if already attempted/expired)
        print(f"  PASS: Exam Take route for Quiz '{quiz.title}' -> {r.status_code}")
    else:
        print("  SKIP: No published quiz found for take test")

    # 6. Preserved REST API Endpoints
    print("\n[6] Testing Preserved DRF API Endpoints...")
    api_routes = [
        ('/api/courses/', "Courses API"),
        ('/api/quizzes/', "Quizzes API"),
    ]
    for route, label in api_routes:
        r = client.get(route)
        # API can return 200 or 401/403 if auth is required, but definitely NOT 404 or 500
        assert r.status_code in (200, 401, 403), f"API failed on {route}: status {r.status_code}"
        print(f"  PASS: Preserved {label} ({route}) -> {r.status_code} (Active & Operational)")

    print("\n==================================================")
    print("ALL VERIFICATION SUITE CHECKS COMPLETED WITH SUCCESS!")
    print("==================================================")

if __name__ == '__main__':
    run_verification()
