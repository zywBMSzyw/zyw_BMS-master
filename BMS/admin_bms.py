# -*- coding: UTF-8 -*-
from django.contrib.admin import AdminSite
from django.contrib.auth.admin import User, UserAdmin, Group, GroupAdmin
from django.views.decorators.cache import never_cache
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy

class BMSAdminSite(AdminSite):

    site_title = "BMS网站管理"
    site_header = ugettext_lazy('后台管理')
    @never_cache
    def index(self, request, extra_context=None):
        """
        Displays the main admin index page, which lists all of the installed
        apps that have been registered in this site.
        """
        app_list = self.get_app_list(request)

        context = dict(
            self.each_context(request),
            title=self.index_title,
            app_list=app_list,
        )
        context.update(extra_context or {})

        request.current_app = self.name

        return TemplateResponse(request, self.index_template or 'admin/index.html', context)
    def each_context(self, request):
        """
        Returns a dictionary of variables to put in the template context for
        *every* page in the admin site.

        For sites running on a subpath, use the SCRIPT_NAME value if site_url
        hasn't been customized.
        """
        script_name = request.META['SCRIPT_NAME']
        site_url = script_name if self.site_url == '/' and script_name else self.site_url
        ##把用户的groupID传给template
        # if Group.objects.filter(id = request.user.id):
        #     group_context = Group.objects.get(id = request.user.id).id
        # else:
        #     group_context = 0
        try:
            group_context = Group.objects.get(user=request.user).name
        except:
            group_context = 0


        return {
            'site_title': self.site_title,
            'site_header': self.site_header,
            'site_url': site_url,
            'has_permission': self.has_permission(request),
            'group_id' : group_context,
            'available_apps': self.get_app_list(request),
        }
BMS_admin_site = BMSAdminSite()
BMS_admin_site.register(User, UserAdmin)
BMS_admin_site.register(Group, GroupAdmin)

