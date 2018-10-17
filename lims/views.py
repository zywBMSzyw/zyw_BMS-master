from django.shortcuts import render
from django.views.generic.list import ListView
from pm.models import Project
import operator
from functools import partial, reduce, update_wrapper
from django.db.models import Q

class ProjectListView(ListView):
    model = Project
    def get_context_data(self, **kwargs):
        context = super(ProjectListView,self).get_context_data(**kwargs)
        context["opts"] = Project._meta
        context['has_permission'] = True
        context['has_filters'] = True
        context['site_url'] = '/'
        query =  self.request.GET.get('q')
        if query:
            query = query.strip()
            context['queryq'] = query
        return context

    def get_queryset(self):
        result = super(ProjectListView, self).get_queryset()
        print(self.request)
        query = self.request.GET.get('q')
        if query:
            query = query.strip()
            #模糊检索合同号，和检索项目id
            result = Project.objects.filter(reduce(operator.or_, [Q(contract__contract_number__icontains=query),Q(id__icontains=query)]))
            return result
        querystatus = self.request.GET.get('status')
        if querystatus:
            querystatus = querystatus.strip()
            #模糊检索合同号，和检索项目id
            result = Project.objects.filter(status=querystatus)
            return result
        return result

