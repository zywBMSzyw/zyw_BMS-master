from django.conf.urls import url

from .views import ProjectListView

urlpatterns = [
    url(r'project/', ProjectListView.as_view(), name='project-list'),
]



