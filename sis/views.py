from django.shortcuts import render
from .models import Student

# Create your views here.
def student_list_view(request):
    students = Student.objects.all()
    return render(request, 'sis/student_list.html', {'students': students}) # Add 'sis/' here