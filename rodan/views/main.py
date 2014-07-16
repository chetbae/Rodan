from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse


@api_view(('GET',))
def api_root(request, format=None):
    return Response({'projects': reverse('project-list', request=request, format=format),
                     'workflows': reverse('workflow-list', request=request, format=format),
                     'workflowjobs': reverse('workflowjob-list', request=request, format=format),
                     'workflowruns': reverse('workflowrun-list', request=request, format=format),
                     'runjobs': reverse('runjob-list', request=request, format=format),
                     'pages': reverse('page-list', request=request, format=format),
                     'jobs': reverse('job-list', request=request, format=format),
                     'results': reverse('result-list', request=request, format=format),
                     'users': reverse('user-list', request=request, format=format),
                     'resultspackages': reverse('resultspackage-list', request=request, format=format),
                     'connections': reverse('connection-list', request=request, format=format),
                     'outputporttypes': reverse('outputporttype-list', request=request, format=format),
                     'outputports': reverse('outputport-list', request=request, format=format),
                     'inputporttypes': reverse('inputporttype-list', request=request, format=format),
                     'inputports': reverse('inputport-list', request=request, format=format),
                     'resources': reverse('resource-list', request=request, format=format),
                     'outputs': reverse('output-list', request=request, format=format),
                     'inputs': reverse('input-list', request=request, format=format)})


@ensure_csrf_cookie
def home(request):
    data = {}
    return render(request, 'base.html', data)
