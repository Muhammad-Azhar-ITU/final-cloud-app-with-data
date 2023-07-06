from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.views.generic import View

app_name = 'onlinecourse'
urlpatterns = [
    path('', views.CourseListView.as_view(), name='index'),
    path('registration/', views.registration_request, name='registration'),
    path('login/', views.login_request, name='login'),
    path('logout/', views.logout_request, name='logout'),
    path('<int:pk>/', views.CourseDetailView.as_view(), name='course_details'),
    path('<int:course_id>/enroll/', views.enroll, name='enroll'),
    path('course/<int:course_id>/submission/<int:submission_id>/result/', views.show_exam_result, name='show_exam_result'),
    path('<int:course_id>/submit_exam/', views.ExamSubmissionView.as_view(), name='submit_exam'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
