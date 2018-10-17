from django.contrib import admin
from .models import SampleInfo, QcTask, ExtTask, LibTask
from pm.models import Project
from django import forms
from django.contrib import messages
from datetime import date, timedelta, datetime
from django.utils.html import format_html
from notification.signals import notify
from import_export import fields
from import_export import resources
from import_export.admin import ImportExportActionModelAdmin
from BMS.admin_bms import BMS_admin_site


def add_business_days(from_date, number_of_days):
    to_date = from_date
    if number_of_days >= 0:
        while number_of_days:
            to_date += timedelta(1)
            if to_date.weekday() < 5:
                number_of_days -= 1
    else:
        while number_of_days:
            to_date -= timedelta(1)
            if to_date.weekday() < 5:
                number_of_days += 1
    return to_date


class SampleInfoResource(resources.ModelResource):
    def get_export_headers(self):
        return ["id","项目","样品类型","物种","样品名称","体积uL","浓度ng/uL","收样日期","样品核对","备注"]
    def get_diff_headers(self):
        return ["id","项目","样品类型","物种","样品名称","体积uL","浓度ng/uL","收样日期","样品核对","备注"]
    def init_instance(self, row=None):
        if not row:
            row = {}
        instance = self._meta.model()
        for attr, value in row.items():
            setattr(instance, attr, value)
        instance.project = Project.objects.get(id=row['项目'])
        instance.type = row['样品类型']
        instance.species = row['物种']
        instance.name = row['样品名称']
        instance.volume = row['体积uL']
        instance.concentration = row['浓度ng/uL']
        instance.receive_date = datetime.strptime(row['收样日期'],'%Y-%m-%d')
        instance.check = row['样品核对']
        instance.note = row['备注']
        return instance
    class Meta:
        model = SampleInfo
        skip_unchanged = True
        fields = ('id','project__contract__name','type','species','name','volume','concentration',
                  'receive_date','check','note')
        export_order = ('id','project__contract__name','type','species','name','volume','concentration',
                  'receive_date','check','note')


class SampleInfoForm(forms.ModelForm):
    def clean_note(self):
        if self.cleaned_data['check'] is False and not self.cleaned_data['note']:
            raise forms.ValidationError('未通过核验的样品需备注')
        return self.cleaned_data['note']


class SampleInfoAdmin(ImportExportActionModelAdmin):
    resource_class = SampleInfoResource
    form = SampleInfoForm
    list_display = ['contract', 'project', 'type', 'species', 'name', 'volume', 'concentration', 'receive_date',
                    'check', 'note']
    list_display_links = ['name']
    list_filter = ['check']
    actions = ['make_pass']
    fields = (('contract', 'contract_name', 'project', 'customer'), ('name', 'receive_date'), 'type', 'species',
              'volume', 'concentration', 'check', 'note')
    raw_id_fields = ['project']
    # change_list_template = "pm/chang_list_custom.html"
    search_fields = ['project__contract__contract_number']

    def contract(self, obj):
        return obj.project.contract
    contract.short_description = '合同'

    def contract_name(self, obj):
        return obj.project.contract.name
    contract_name.short_description = '合同名'

    def customer(self, obj):
        return obj.project.customer
    customer.short_description = '客户'

    def make_pass(self, request, queryset):
        rows_updated = queryset.update(check=True)
        if rows_updated:
            self.message_user(request, '%s 个样品核验通过' % rows_updated)
            #样品信息核对，提醒相应销售人员
            notify.send(request.user, recipient=queryset[0].project.contract.salesman, verb='核对了样品信息',description="项目名称：%s 此次核对的样品数量：%s"%(queryset[0].project.name,rows_updated))
        else:
            self.message_user(request, '%s 未成功操作标记核验通过' % rows_updated, level=messages.ERROR)
    make_pass.short_description = '标记所选样品核验通过'

    def save_model(self, request, obj, form, change):
        if obj.check is False and not obj.note:
            messages.set_level(request, messages.ERROR)
            self.message_user(request, '不通过核验时需要进行备注', level=messages.ERROR)
        else:
            obj.save()
            #样品信息核对，提醒相应销售人员
            notify.send(request.user, recipient=obj.project.contract.salesman, verb='核对了样品信息',description="项目名称：%s 样品名称：%s"%(obj.project.name,obj.project.contract.name))

    def get_queryset(self, request):
        qs = super(SampleInfoAdmin, self).get_queryset(request)
        if request.user.is_superuser or request.user.has_perm('lims.add_sampleinfo'):
            return qs
        return qs.filter(project__contract__salesman=request.user)

    def get_actions(self, request):
        actions = super(SampleInfoAdmin, self).get_actions(request)
        if not request.user.has_perm('lims.delete_sampleinfo'):
            actions = None
        return actions

    def get_readonly_fields(self, request, obj=None):
        if not request.user.has_perm('lims.delete_sampleinfo'):
            return ['contract', 'contract_name', 'project', 'customer', 'name', 'receive_date', 'type', 'species',
                    'volume', 'concentration', 'check', 'note']
        return ['contract', 'contract_name', 'customer']

    def change_view(self, request, object_id, form_url='', extra_context=None):
        # 没有删除意向权限人员查看页面时隐藏所有按钮
        extra_context = extra_context or {}
        if not request.user.has_perm('lims.delete_sampleinfo'):
            extra_context['really_hide_save_and_add_another_damnit'] = True
            extra_context['show_save'] = False
            extra_context['show_delete_link'] = False
            extra_context['show_save_as_new'] = False
            extra_context['show_save_and_add_another'] = False
            extra_context['show_save_and_continue'] = False
        return super(SampleInfoAdmin, self).change_view(request, object_id, form_url, extra_context=extra_context)
    def add_view(self, request, form_url='', extra_context=None):
        # 没有删除意向权限人员查看页面时隐藏所有按钮
        extra_context = extra_context or {}
        if not request.user.has_perm('lims.delete_sampleinfo'):
            extra_context['really_hide_save_and_add_another_damnit'] = True
            extra_context['show_save'] = False
            extra_context['show_delete_link'] = False
            extra_context['show_save_as_new'] = False
            extra_context['show_save_and_add_another'] = False
            extra_context['show_save_and_continue'] = False
        return super(SampleInfoAdmin, self).add_view(request, form_url, extra_context=extra_context)


class ExtTaskForm(forms.ModelForm):
    def clean_note(self):
        if self.cleaned_data['result'] is False and not self.cleaned_data['note']:
            raise forms.ValidationError('提取失败的样品需备注')
        return self.cleaned_data['note']


class ExtTaskAdmin(admin.ModelAdmin):
    form = ExtTaskForm
    list_display = ['contract', 'project', 'sample_name', 'receive_date', 'left_days', 'date', 'operator', 'result',
                    'note']
    list_display_links = ['sample_name']
    list_filter = ['result']
    actions = ['make_pass']
    fields = (('contract', 'contract_name', 'project', 'customer'), ('sample_name', 'receive_date'), 'result', 'note')

    def contract(self, obj):
        return obj.sample.project.contract
    contract.short_description = '合同'

    def contract_name(self, obj):
        return obj.sample.project.contract.name
    contract_name.short_description = '合同名'

    def customer(self, obj):
        return obj.sample.project.customer
    customer.short_description = '客户'

    def project(self, obj):
        return obj.sample.project
    project.short_description = '项目'

    def sample_name(self, obj):
        return obj.sample.name
    sample_name.short_description = '样品'

    def receive_date(self, obj):
        return obj.sample.receive_date
    receive_date.short_description = '收样日期'

    def left_days(self, obj):
        if obj.date:
            return '完成'
        due_date = add_business_days(obj.sub_date, obj.sample.project.ext_cycle)
        left = (due_date - date.today()).days
        if left >= 0:
            return '余%s天' % left
        else:
            return format_html('<span style="color:{};">{}</span>', 'red', '延%s天' % -left)
    left_days.short_description = '剩余周期'

    def operator(self, obj):
        if obj.staff:
            name = obj.staff.last_name + obj.staff.first_name
            if name:
                return name
            return obj.staff
        return ''
    operator.short_description = '实验员'

    def make_pass(self, request, queryset):
        rows_updated = queryset.update(result=True, date=date.today(), staff=request.user)
        if rows_updated:
            self.message_user(request, '%s 个样品提取成功' % rows_updated)
            #样品提取成，提醒相应销售人员
            notify.send(request.user, recipient=queryset[0].project.contract.salesman, verb='提取样品成功',description="项目名称：%s 此次核对的样品数量：%s"%(queryset[0].project.name,rows_updated))
        else:
            self.message_user(request, '%s 未能操作标记为提取成功' % rows_updated, level=messages.ERROR)
    make_pass.short_description = '标记所选样品提取成功'

    def save_model(self, request, obj, form, change):
        if obj.result is None:
            obj.date = None
            obj.staff = None
        else:
            obj.date = date.today()
            obj.staff = request.user
        obj.save()
        #样品提取成功，提醒相应销售人员
        notify.send(request.user, recipient=obj.sample.project.contract.salesman, verb='核对了样品信息',description="项目名称：%s 样品名称：%s"%(obj.sample.project.name,obj.sample.project.contract.name))

    def get_queryset(self, request):
        qs = super(ExtTaskAdmin, self).get_queryset(request)
        if request.user.is_superuser or request.user.has_perm('lims.add_exttask'):
            return qs
        return qs.filter(sample__project__contract__salesman=request.user)

    def get_actions(self, request):
        actions = super(ExtTaskAdmin, self).get_actions(request)
        if not request.user.has_perm('lims.delete_exttask'):
            actions = None
        return actions

    def get_readonly_fields(self, request, obj=None):
        if not request.user.has_perm('lims.delete_exttask'):
            return ['contract', 'contract_name', 'project', 'customer', 'sample_name', 'receive_date', 'result', 'note']
        return ['contract', 'contract_name', 'project', 'customer', 'sample_name', 'receive_date']


# class QcTaskForm(forms.ModelForm):
#     def clean_note(self):
#         if self.cleaned_data['result'] in [2, 3] and not self.cleaned_data['note']:
#             raise forms.ValidationError('质检不合格的样品需备注')
#         return self.cleaned_data['note']
#
#
# class QcTaskAdmin(admin.ModelAdmin):
#     form = QcTaskForm
#     list_display = ['contract', 'project', 'sample_name', 'receive_date', 'left_days', 'date', 'volume', 'concentration',
#                     'total', 'operator', 'result', 'note']
#     list_display_links = ['sample_name']
#     list_filter = ['result']
#     actions = ['make_pass']
#     fields = (('contract', 'contract_name', 'project', 'customer'), ('sample_name', 'receive_date'), 'volume',
#               'concentration', 'total', 'result', 'note')
#
#     def contract(self, obj):
#         return obj.sample.project.contract
#     contract.short_description = '合同'
#
#     def contract_name(self, obj):
#         return obj.sample.project.contract.name
#     contract_name.short_description = '合同名'
#
#     def customer(self, obj):
#         return obj.sample.project.customer
#     customer.short_description = '客户'
#
#     def project(self, obj):
#         return obj.sample.project
#     project.short_description = '项目'
#
#     def sample_name(self, obj):
#         return obj.sample.name
#     sample_name.short_description = '样品'
#
#     def receive_date(self, obj):
#         return obj.sample.receive_date
#     receive_date.short_description = '收样日期'
#
#     def left_days(self, obj):
#         if obj.date:
#             return '完成'
#         due_date = add_business_days(obj.sub_date, obj.sample.project.qc_cycle)
#         left = (due_date - date.today()).days
#         if left >= 0:
#             return '余%s天' % left
#         else:
#             return format_html('<span style="color:{};">{}</span>', 'red', '延%s天' % -left)
#     left_days.short_description = '剩余周期'
#
#     def operator(self, obj):
#         if obj.staff:
#             name = obj.staff.last_name + obj.staff.first_name
#             if name:
#                 return name
#             return obj.staff
#         return ''
#     operator.short_description = '实验员'
#
#     def make_pass(self, request, queryset):
#         rows_updated = queryset.update(result=1, date=date.today(), staff=request.user)
#         if rows_updated:
#             self.message_user(request, '%s 个样品质检合格' % rows_updated)
#             #样品质检合格，提醒相应销售人员
#             notify.send(request.user, recipient=queryset[0].project.contract.salesman, verb='样品质检合格',description="项目名称：%s 此次核对的样品数量：%s"%(queryset[0].project.name,rows_updated))
#         else:
#             self.message_user(request, '%s 未能操作标记为质检合格' % rows_updated, level=messages.ERROR)
#     make_pass.short_description = '标记所选样品质检合格'
#
#     def save_model(self, request, obj, form, change):
#         if obj.result == 0:
#             obj.volume = None
#             obj.concentration = None
#             obj.total = None
#             obj.note = None
#             obj.date = None
#             obj.staff = None
#         else:
#             obj.date = date.today()
#             obj.staff = request.user
#         obj.save()
#         #样品质检合格，提醒相应销售人员
#         notify.send(request.user, recipient=obj.project.contract.salesman, verb='样品质检合格',description="项目名称：%s 样品名称：%s"%(obj.project.name,obj.project.contract.name))
#
#     def get_queryset(self, request):
#         qs = super(QcTaskAdmin, self).get_queryset(request)
#         if request.user.is_superuser or request.user.has_perm('lims.add_qctask'):
#             return qs
#         return qs.filter(sample__project__contract__salesman=request.user)
#
#     def get_actions(self, request):
#         actions = super(QcTaskAdmin, self).get_actions(request)
#         if not request.user.has_perm('lims.delete_qctask'):
#             actions = None
#         return actions
#
#     def get_readonly_fields(self, request, obj=None):
#         if not request.user.has_perm('lims.delete_qctask'):
#             return ['contract', 'contract_name', 'project', 'customer', 'sample_name', 'receive_date', 'volume',
#                     'concentration', 'total', 'result', 'note']
#         return ['contract', 'contract_name', 'project', 'customer', 'sample_name', 'receive_date']


class LibTaskForm(forms.ModelForm):
    def clean_note(self):
        if self.cleaned_data['result'] is False and not self.cleaned_data['note']:
            raise forms.ValidationError('建库不合格的样品需备注')
        return self.cleaned_data['note']


class LibTaskAdmin(admin.ModelAdmin):
    form = LibTaskForm
    list_display = ['contract', 'project', 'sample_name', 'receive_date', 'left_days', 'date', 'type', 'sample_code',
                    'lib_code', 'index', 'length', 'volume', 'concentration', 'total', 'operator', 'result', 'note']
    list_display_links = ['sample_name']
    list_filter = ['result']
    actions = ['make_pass']
    fields = (('contract', 'contract_name', 'project', 'customer'), ('sample_name', 'receive_date'), 'type',
              'sample_code', 'lib_code', 'index', 'length', 'volume', 'concentration', 'total', 'result', 'note')

    def contract(self, obj):
        return obj.sample.project.contract
    contract.short_description = '合同'

    def contract_name(self, obj):
        return obj.sample.project.contract.name
    contract_name.short_description = '合同名'

    def customer(self, obj):
        return obj.sample.project.customer
    customer.short_description = '客户'

    def project(self, obj):
        return obj.sample.project
    project.short_description = '项目'

    def sample_name(self, obj):
        return obj.sample.name
    sample_name.short_description = '样品'

    def receive_date(self, obj):
        return obj.sample.receive_date
    receive_date.short_description = '收样日期'

    def left_days(self, obj):
        if obj.date:
            return '完成'
        due_date = add_business_days(obj.sub_date, obj.sample.project.lib_cycle)
        left = (due_date - date.today()).days
        if left >= 0:
            return '余%s天' % left
        else:
            return format_html('<span style="color:{};">{}</span>', 'red', '延%s天' % -left)
    left_days.short_description = '剩余周期'

    def operator(self, obj):
        if obj.staff:
            name = obj.staff.last_name + obj.staff.first_name
            if name:
                return name
            return obj.staff
        return ''
    operator.short_description = '实验员'

    def make_pass(self, request, queryset):
        rows_updated = queryset.update(result=True, date=date.today(), staff=request.user)
        if rows_updated:
            self.message_user(request, '%s 个样品建库合格' % rows_updated)
            #样品建库合格，提醒相应销售人员
            notify.send(request.user, recipient=queryset[0].project.contract.salesman, verb='样品建库合格',description="项目名称：%s 此次核对的样品数量：%s"%(queryset[0].project.name,rows_updated))
        else:
            self.message_user(request, '%s 未能操作标记为建库合格' % rows_updated, level=messages.ERROR)
    make_pass.short_description = '标记所选样品建库合格'

    def save_model(self, request, obj, form, change):
        if obj.result is None:
            obj.date = None
            obj.staff = None
            obj.type = None
            obj.sample_code = None
            obj.lib_code = None
            obj.index = None
            obj.length = None
            obj.volume = None
            obj.concentration = None
            obj.total = None
            obj.note = None
        else:
            obj.date = date.today()
            obj.staff = request.user
        obj.save()
        #样品建库合格，提醒相应销售人员
        notify.send(request.user, recipient=obj.project.contract.salesman, verb='样品建库合格',description="项目名称：%s 样品名称：%s"%(obj.project.name,obj.project.contract.name))

    def get_queryset(self, request):
        qs = super(LibTaskAdmin, self).get_queryset(request)
        if request.user.is_superuser or request.user.has_perm('lims.add_libtask'):
            return qs
        return qs.filter(sample__project__contract__salesman=request.user)

    def get_actions(self, request):
        actions = super(LibTaskAdmin, self).get_actions(request)
        if not request.user.has_perm('lims.delete_libtask'):
            actions = None
        return actions

    def get_readonly_fields(self, request, obj=None):
        if not request.user.has_perm('lims.delete_libtask'):
            return ['contract', 'contract_name', 'project', 'customer', 'sample_name', 'receive_date', 'type',
                    'sample_code', 'lib_code', 'index', 'length', 'volume', 'concentration', 'total', 'result', 'note']
        return ['contract', 'contract_name', 'project', 'customer', 'sample_name', 'receive_date']


# admin.site.register(SampleInfo, SampleInfoAdmin)
# admin.site.register(ExtTask, ExtTaskAdmin)
# # admin.site.register(QcTask, QcTaskAdmin)
# admin.site.register(LibTask, LibTaskAdmin)

BMS_admin_site.register(SampleInfo, SampleInfoAdmin)
BMS_admin_site.register(ExtTask, ExtTaskAdmin)
# admin.site.register(QcTask, QcTaskAdmin)
BMS_admin_site.register(LibTask, LibTaskAdmin)
