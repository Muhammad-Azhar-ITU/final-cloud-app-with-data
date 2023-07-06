from django.shortcuts import render
from django.http import HttpResponseRedirect
# <HINT> Import any new Models here
from .models import Course, Enrollment
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.contrib.auth import login, logout, authenticate
import logging
from django.views import View
# Get an instance of a logger
logger = logging.getLogger(__name__)
# Create your views here.


def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'onlinecourse/user_registration_bootstrap.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("onlinecourse:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'onlinecourse/user_registration_bootstrap.html', context)


def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('onlinecourse:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'onlinecourse/user_login_bootstrap.html', context)
    else:
        return render(request, 'onlinecourse/user_login_bootstrap.html', context)


def logout_request(request):
    logout(request)
    return redirect('onlinecourse:index')


def check_if_enrolled(user, course):
    is_enrolled = False
    if user.id is not None:
        # Check if user enrolled
        num_results = Enrollment.objects.filter(user=user, course=course).count()
        if num_results > 0:
            is_enrolled = True
    return is_enrolled


# CourseListView
class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list_bootstrap.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        user = self.request.user
        courses = Course.objects.order_by('-total_enrollment')[:10]
        for course in courses:
            if user.is_authenticated:
                course.is_enrolled = check_if_enrolled(user, course)
        return courses


class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_detail_bootstrap.html'


def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user

    is_enrolled = check_if_enrolled(user, course)
    if not is_enrolled and user.is_authenticated:
        # Create an enrollment
        Enrollment.objects.create(user=user, course=course, mode='honor')
        course.total_enrollment += 1
        course.save()

    return HttpResponseRedirect(reverse(viewname='onlinecourse:course_details', args=(course.id,)))

class ExamSubmissionView(View):
    def post(self, request, course_id):
        # Process the form submission and save the selected choices
        # Retrieve the selected choice IDs from the submitted form data
        selected_choice_ids = request.POST.getlist('choices')

        # Get the course and enrollment
        course = Course.objects.get(id=course_id)
        enrollment = Enrollment.objects.get(user=request.user, course=course)

        # Clear the previous choices for this enrollment
        enrollment.submission.choices.clear()

        # Save the selected choices for this enrollment
        for choice_id in selected_choice_ids:
            choice = Choice.objects.get(id=choice_id)
            enrollment.submission.choices.add(choice)

        # Redirect to the exam result page or another appropriate page
        return redirect('onlinecourse:exam_result', course_id=course_id)

def submit_exam(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user

    is_enrolled = check_if_enrolled(user, course)
    if not is_enrolled and user.is_authenticated:
        # Create an enrollment
        Enrollment.objects.create(user=user, course=course, mode='honor')
        course.total_enrollment += 1
        course.save()

    return HttpResponseRedirect(reverse(viewname='onlinecourse:course_details', args=(course.id,)))


def submit(request, course_id):
    # Get the current user and the course object
    user = request.user
    course = Course.objects.get(id=course_id)

    # Get the associated enrollment object
    enrollment = Enrollment.objects.get(user=user, course=course)

    # Create a new submission object referring to the enrollment
    submission = Submission.objects.create(enrollment=enrollment)

    # Collect the selected choices from the HTTP request object
    selected_choice_ids = request.POST.getlist('choices')

    # Add each selected choice object to the submission object
    for choice_id in selected_choice_ids:
        choice = Choice.objects.get(id=choice_id)
        submission.choices.add(choice)

    # Redirect to the exam result page with the submission id
    return redirect('onlinecourse:show_exam_result', course_id=course_id, submission_id=submission.id)

def show_exam_result(request, course_id, submission_id):
    # Get the course object and submission object
    course = Course.objects.get(id=course_id)
    submission = Submission.objects.get(id=submission_id)

    # Get the selected choice ids from the submission record
    selected_choice_ids = submission.choices.values_list('id', flat=True)

    # For each selected choice, check if it is a correct answer or not
    # Calculate the total score by adding up the grades for all questions in the course

    # Add the course, selected_choice_ids, and grade to the context for rendering the HTML page
    context = {
        'course': course,
        'selected_choice_ids': selected_choice_ids,
        'grade': submission.get_grade(),
    }
    return render(request, 'onlinecourse/exam_result.html', context)

# Helper method to extract selected choices from the request object
def extract_answers(request):
    submitted_answers = []
    for key in request.POST:
        if key.startswith('choice'):
            value = request.POST[key]
            choice_id = int(value)
            submitted_answers.append(choice_id)
    return submitted_answers

def course_detail(request, course_id):
    # Retrieve the course object
    course = get_object_or_404(Course, id=course_id)

    # Retrieve the exam questions related to the course
    exam_questions = Question.objects.filter(course=course)

    context = {
        'course': course,
        'exam_questions': exam_questions,  # Add this line to include exam_questions in the context
    }

    return render(request, 'onlinecourse/course_detail_bootstrap.html', context)


