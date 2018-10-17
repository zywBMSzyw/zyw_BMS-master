from django.contrib import admin
# from .models import Project, QcSubmit, ExtSubmit, LibSubmit
from .models import Project, ExtSubmit, LibSubmit, SeqSubmit, AnaSubmit
from lims.models import SampleInfo, ExtTask, LibTask, SeqTask, AnaTask
from django import forms
from BMS.admin_bms import BMS_admin_site
from datetime import date, timedelta
from fm.models import Bill
from mm.models import Contract
from crm.models import Customer
from teacher.models import SampleInfoForm
from django.db.models import Sum
from django.utils.html import format_html
from django.contrib import messages
from django.contrib.auth.models import User
from notification.signals import notify
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from import_export import fields


# 添加工作日
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


# 期间的收入
def is_period_income(contract, period):
    income = Bill.objects.filter(invoice__invoice__contract=contract).filter(invoice__invoice__period=period)\
            .aggregate(total_income=Sum('income'))['total_income']
    if not income:
        return 0.001  # 未开票
    if period == 'FIS':
        amount = Contract.objects.filter(contract_number=contract)[0].fis_amount
    elif period == 'FIN':
        amount = Contract.objects.filter(contract_number=contract)[0].fin_amount
    return amount - income


class StatusListFilter(admin.SimpleListFilter):
    title = '项目状态'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return (
            ('CNS', '不能启动'),  # (Could not started)
            ('NS', '正常启动'),  # NS(normal start)
            ('ES', '提前启动'),  # ES(Early start)
            ('PA', '立项处理'),  # PA(Project approval)
            ('FIS', '待首款'),
            # ('ENS', '待处理'),
            ('EXT', '提取中'),
            # ('QC', '质检中'),
            ('LIB', '建库中'),
            ('SEQ', '测序中'),
            ('ANA', '分析中'),
            ('FIN', '待尾款'),
            ('FINE', '尾款已到'),
            ('END', '完成'),
        )

    # is_title = '服务类型'
    # is_name = 'is_status'
    #
    # def is_names(self):
    #     return (
    #         ('is_ext', '提取'),
    #         ('is_lib', '建库'),
    #         ('is_seq', '测序'),
    #         ('is_ana', '分析'),
    #     )
    def queryset(self, request, queryset):
        # 不能启动（没有合同号）
        if self.value() == 'CNS':
            return queryset.filter(contract__contract_number=None)
        # 提前启动（低于70%的总金额）
        # if self.value() == 'ES':
        #     return queryset.filter(contract__fis_amount < (0.7*contract__all_amount))
        # 正常启动（70%-100%的总金额）
        # if self.value() == 'NS':
        #     return queryset.filter((contract__fis_amount > (0.7*contract__all_amount)) and (contract__fis_amount < contract__all_amount))
        if self.value() == 'FIS':
            return queryset.filter(contract__fis_date=None)
        # if self.value() == 'ENS':
        #     projects = []
        #     ext_samples = list(set(ExtTask.objects.filter(result=None).values_list('sample__pk', flat=True)))
        #     projects += list(set(SampleInfo.objects.filter(id__in=ext_samples).values_list('project__pk', flat=True)))
        #
        #     # qc_samples = list(set(QcTask.objects.filter(result=None).values_list('sample__pk', flat=True)))
        #     # projects += list(set(SampleInfo.objects.filter(id__in=qc_samples).values_list('project__pk', flat=True)))
        #
        #     lib_samples = list(set(LibTask.objects.filter(result=None).values_list('sample__pk', flat=True)))
        #     projects += list(set(SampleInfo.objects.filter(id__in=lib_samples).values_list('project__pk', flat=True)))
        #
        #     seq_samples = list(set(SeqTask.objects.filter(result=None).values_list('sample__pk', flat=True)))
        #     projects += list(set(SampleInfo.objects.filter(id__in=seq_samples).values_list('project__pk', flat=True)))
        #
        #     ana_samples = list(set(AnaTask.objects.filter(result=None).values_list('sample__pk', flat=True)))
        #     projects += list(set(SampleInfo.objects.filter(id__in=ana_samples).values_list('project__pk', flat=True)))
        #
        #     projects += Project.objects.exclude(seq_start_date=None).filter(seq_end_date=None)\
        #         .values_list('pk', flat=True)
        #     projects += Project.objects.exclude(ana_start_date=None).filter(ana_end_date=None)\
        #         .values_list('pk', flat=True)
        #
        #     projects += Project.objects.exclude(ana_start_date=None).exclude(ana_end_date=None)\
        #         .filter(contract__fin_date=None).values_list('pk', flat=True)
        #     print(projects)
        #     return queryset.exclude(contract__fis_date=None).exclude(id__in=projects)
        if self.value() == 'EXT':
            samples = list(set(ExtTask.objects.filter(result=None).values_list('sample__pk', flat=True)))
            projects = list(set(SampleInfo.objects.filter(id__in=samples).values_list('project__pk', flat=True)))
            return queryset.filter(id__in=projects)
        # if self.value() == 'QC':
        #     samples = list(set(QcTask.objects.filter(result=None).values_list('sample__pk', flat=True)))
        #     projects = list(set(SampleInfo.objects.filter(id__in=samples).values_list('project__pk', flat=True)))
        #     return queryset.filter(id__in=projects)
        if self.value() == 'LIB':
            samples = list(set(LibTask.objects.filter(result=None).values_list('sample__pk', flat=True)))
            projects = list(set(SampleInfo.objects.filter(id__in=samples).values_list('project__pk', flat=True)))
            return queryset.filter(id__in=projects)
        if self.value() == 'SEQ':
            return queryset.exclude(seq_start_date=None).filter(seq_end_date=None)
        if self.value() == 'ANA':
            return queryset.exclude(ana_start_date=None).filter(ana_end_date=None)
        if self.value() == 'FIN':
            return queryset.exclude(ana_start_date=None).exclude(ana_end_date=None).filter(contract__fin_date=None)


# 项目提交表
class ProjectForm(forms.ModelForm):
    def clean_seq_start_date(self):
        if not self.cleaned_data['seq_start_date']:
            return
        project = Project.objects.filter(contract=self.cleaned_data['contract']).filter(name=self.cleaned_data['name'])\
            .first()
        if project.is_confirm == 0:
            raise forms.ValidationError('项目尚未启动，请留空')
        if not project.is_lib:
            return self.cleaned_data['seq_start_date']
        lib_date = project.lib_date
        if not lib_date:
            raise forms.ValidationError('尚未完成建库，无法记录测序时间')
        elif lib_date > self.cleaned_data['seq_start_date']:
            raise forms.ValidationError('测序开始日期不能早于建库完成日期')
        return self.cleaned_data['seq_start_date']

    def clean_ana_start_date(self):
        if not self.cleaned_data['ana_start_date']:
            return
        if 'seq_end_date' not in self.cleaned_data.keys() or not self.cleaned_data['seq_end_date']:
            raise forms.ValidationError('尚未完成测序，无法记录分析时间')
        elif self.cleaned_data['seq_end_date'] > self.cleaned_data['ana_start_date']:
            raise forms.ValidationError('分析开始日期不能早于测序完成日期')
        return self.cleaned_data['ana_start_date']

    def clean_seq_end_date(self):
        if not self.cleaned_data['seq_end_date']:
            return
        if 'seq_start_date' not in self.cleaned_data.keys() or not self.cleaned_data['seq_start_date']:
            raise forms.ValidationError('尚未记录测序开始日期')
        elif self.cleaned_data['seq_end_date'] and self.cleaned_data['seq_start_date'] \
                > self.cleaned_data['seq_end_date']:
            raise forms.ValidationError('完成日期不能早于开始日期')
        return self.cleaned_data['seq_end_date']

    def clean_ana_end_date(self):
        if not self.cleaned_data['ana_end_date']:
            return
        if 'ana_start_date' not in self.cleaned_data.keys() or not self.cleaned_data['ana_start_date']:
            raise forms.ValidationError('尚未记录分析开始日期')
        elif self.cleaned_data['ana_start_date'] > self.cleaned_data['ana_end_date']:
            raise forms.ValidationError('完成日期不能早于开始日期')
        return self.cleaned_data['ana_end_date']

    def clean_report_date(self):
        if not self.cleaned_data['report_date']:
            return
        if 'ana_end_date' not in self.cleaned_data.keys() or not self.cleaned_data['ana_end_date']:
            raise forms.ValidationError('分析尚未完成')
        return self.cleaned_data['report_date']

    def clean_result_date(self):
        if not self.cleaned_data['result_date']:
            return
        if 'ana_end_date' not in self.cleaned_data.keys() or not self.cleaned_data['ana_end_date']:
            raise forms.ValidationError('分析尚未完成')
        return self.cleaned_data['result_date']

    def clean_data_date(self):
        if not self.cleaned_data['data_date']:
            return
        if not Contract.objects.filter(contract_number=self.cleaned_data['contract']).first().fin_date:
            raise forms.ValidationError('尾款未到不能操作该记录')


# class ProjectAdminFormSet(BaseModelFormSet):
#     def clean(self):
#         for p in self.cleaned_data:
#             if not SampleInfo.objects.filter(project=p['id']).count() and p['is_confirm']:
#                 raise forms.ValidationError('未收到样品的项目无法确认启动')

class ProjectResource(resources.ModelResource):

    def init_instance(self, row=None):
        instance = self._meta.model()
        instance.project = Project.objects.get(id=row['contract__contract_number'])
        return instance

    class Meta:
        model = Project
        skip_unchanged = True
        fields = ('id', 'contract__contract_number',)
    # 按照合同号导出
    sub_number = fields.Field(column_name="子项目编号", attribute="sub_number")

    class Meta:
        model = Project
        skip_unchanged = True
        fields = ('sub_number',)
        export_order = ('sub_number',)


# 项目管理
# class ProjectAdmin(ImportExportModelAdmin):
class ProjectAdmin(admin.ModelAdmin):
    resource_class = ProjectResource
    form = ProjectForm
    list_display = ('id', 'contract_number', 'contract_name', 'sub_number', 'sub_project',
                    'customer_name', 'saleman',
                    'project_personnel',
                    # 'sample_type',
                    # 'sample_count',
                    # 'service_type',
                    'is_confirm', 'status',
                    'contract_node', 'ext_status',  'lib_status', 'seq_status', 'ana_status',
                    'report_sub', 'result_sub', 'data_sub',)
    # list_editable = ['is_confirm']
    list_filter = [StatusListFilter]
    fieldsets = (
        ('合同信息', {
             'fields': (('contract', 'contract_name', 'income_notes', 'saleman',),),
        }),
        ('项目信息', {
            'fields': (('customer', 'customer_phone', 'company',),
                       ('sub_number', 'sub_project',),
                       ('project_personnel', 'project_start_time', ),
                       ('sample_types',
                        # 'sample_count',
                        ),
                       ('name',),
                       ('service_type',),
                       ('is_ext', 'is_lib', 'is_seq', 'is_ana',),
                       ('data_amount', 'status',  'pic', 'is_confirm',),)
        }),
        ('节点信息', {
            'fields': ('receive_date',)
        }),
    )
    readonly_fields = ['contract_name', 'income_notes', 'saleman',
                       'customer_phone', 'company',
                       # 'sample_type',
                       # 'sample_count',
                       ]
    raw_id_fields = ['contract',
                     'customer',
                     'project_personnel',
                     'sample_types',
                     ]
    actions = ['make_confirm']
    search_fields = ['id', 'contract__contract_number', ]
    # change_list_template = "pm/chang_list_custom.html"

    # # 关键词搜索
    # def get_search_results(self, request, queryset, search_term):
    #     queryset, use_distinct = super(ProjectAdmin,self).get_search_results(request,queryset,search_term)
    #     try:
    #         search_term_as_int = int(search_term)
    #         queryset |= self.model.objects.filter(age=search_term_as_int)
    #     except:
    #         pass
    #     return request, use_distinct
    def service_types(self,obj):
        return obj.project.is_ext
    service_types.short_description = '服务类型'

    def contract_number(self, obj):
        return obj.contract.contract_number
    contract_number.short_description = '合同编号'

    def contract_name(self, obj):
        return obj.contract.name
    contract_name.short_description = '项目名称'

    def income_notes(self, obj):
        return obj.contract.fis_amount
    income_notes.short_description = '到款的记录'

    def saleman(self, obj):
        return obj.contract.salesman
    saleman.short_description = '销售人员'

    def customer_name(self, obj):
        return obj.customer.name
    customer_name.short_description = '客户姓名'

    def customer_phone(self, obj):
        return obj.customer.contact
    customer_phone.short_description = '客户联系方式'

    def company(self, obj):
        return obj.customer.address
    company.short_description = '客户地址'

    # def sample_type(self, obj):
    #     return obj.sampleinfoform.project_type
    # sample_type.short_description = '样品de类型'

    # def sample_count(self, obj):
    #     return obj.sampleinfo.sample_num
    # sample_count.short_description = '样品de数量'

    # def status(self, obj):
    #     return obj.status.display()
    # status.short_description = '状态'

    # def status(self, obj):
    #     if not is_period_income(obj.contract, 'FIS')
    # <= 0 and is_period_income(obj.contract, 'FIS')!=0.001:#mm.Contract表中的FIS>0
    #         return '待首款'
    #     if obj.data_date:
    #         return '已完成'
    #     if obj.ana_end_date and is_period_income(obj.contract, 'FIN') <= 0 :
    #         return '尾款已到'
    #     if obj.ana_end_date and not is_period_income(obj.contract, 'FIN')
    #  <= 0 and is_period_income(obj.contract, 'FIN') != 0.001:
    #         return '待尾款'
    #     if obj.ana_start_date and not obj.ana_end_date:
    #         return '分析中'
    #     if obj.seq_start_date and not obj.seq_end_date:
    #         return '测序中'
    #     if LibTask.objects.filter(sample__project=obj).filter(result=None).count():
    #         return '建库中'
    #     if QcTask.objects.filter(sample__project=obj).filter(result=None).count():
    #         return '质检中'
    #     if ExtTask.objects.filter(sample__project=obj).filter(result=None).count():
    #         return '提取中'
    #     if is_period_income(obj.contract, 'FIS') == 0 or is_period_income
    # (obj.contract, 'FIN') == 0.001 or is_period_income(obj.contract, 'FIS') == 0.001:
    #         return '待处理'
    # status.short_description = '状态'

    def sample_num(self, obj):
        return SampleInfo.objects.filter(project=obj).count()
    sample_num.short_description = '收样数'

    def receive_date(self, obj):
        qs_sample = SampleInfo.objects.filter(project=obj)
        if qs_sample:
            return qs_sample.last().receive_date.strftime('%Y%m%d')
    receive_date.short_description = '收样时间'

    def contract_node(self, obj):
        if obj.due_date:
            return obj.due_date.strftime('%Y%m%d')
        else:
            return
    contract_node.short_description = '合同节点'

    def report_sub(self, obj):
        if obj.report_date:
            return obj.report_date.strftime('%Y%m%d')
        else:
            return
    report_sub.short_description = '报告提交'

    def result_sub(self, obj):
        if obj.result_date:
            return obj.result_date.strftime('%Y%m%d')
        else:
            return
    result_sub.short_description = '结果提交'

    def data_sub(self, obj):
        if obj.data_date:
            return obj.data_date.strftime('%Y%m%d')
    data_sub.short_description = '数据提交'

    # def ext_status(self, obj):
    #     if not obj.due_date or not obj.is_ext:
    #         return '-'
    #     total = ExtTask.objects.filter(sample__project=obj).count()
    #     done = ExtTask.objects.filter(sample__project=obj).exclude(result=None).count()
    #     if done != total or not total:
    #         obj.ext_date = None
    #         obj.save()
    #         left = (obj.due_date - timedelta(obj.ana_cycle + obj.seq_cycle + obj.lib_cycle + obj.qc_cycle) -
    #                 date.today()).days
    #         if left >= 0:
    #             return '%s/%s-余%s天' % (done, total, left)
    #         else:
    #             return format_html('<span style="color:{};">{}</span>', 'red', '%s/%s-延%s天' % (done, total, -left))
    #     else:
    #         obj.ext_date = ExtTask.objects.filter(sample__project=obj).order_by('-date').first().date
    #         obj.save()
    #         left = (obj.due_date - timedelta(obj.ana_cycle + obj.seq_cycle + obj.lib_cycle + obj.qc_cycle) -
    #                 obj.ext_date).days
    #         if left >= 0:
    #             return '%s-提前%s天' % (obj.ext_date.strftime('%Y%m%d'), left)
    #         else:
    #             return format_html('<span style="color:{};">{}</span>', 'red', '%s-延%s天' %
    #                                (obj.ext_date.strftime('%Y%m%d'), -left))
    # ext_status.short_description = '提取进度'

    def ext_status(self, obj):
        if not obj.due_date or not obj.is_ext:
            return '-'
        total = ExtTask.objects.filter(sample__project=obj).count()
        done = ExtTask.objects.filter(sample__project=obj).exclude(result=None).count()
        if done != total or not total:
            obj.ext_date = None
            obj.save()
            left = (obj.due_date - timedelta(obj.ana_cycle + obj.seq_cycle + obj.lib_cycle) -
                    date.today()).days
            if left >= 0:
                return '%s/%s-余%s天' % (done, total, left)
            else:
                return format_html('<span style="color:{};">{}</span>', 'red', '%s/%s-延%s天' % (done, total, -left))
        else:
            obj.ext_date = ExtTask.objects.filter(sample__project=obj).order_by('-date').first().date
            obj.save()
            left = (obj.due_date - timedelta(obj.ana_cycle + obj.seq_cycle + obj.lib_cycle) -
                    obj.ext_date).days
            if left >= 0:
                return '%s-提前%s天' % (obj.ext_date.strftime('%Y%m%d'), left)
            else:
                return format_html('<span style="color:{};">{}</span>', 'red', '%s-延%s天' %
                                   (obj.ext_date.strftime('%Y%m%d'), -left))
    ext_status.short_description = '提取进度'

    # def qc_status(self, obj):
    #     if not obj.due_date or not obj.is_qc:
    #         return '-'
    #     total = QcTask.objects.filter(sample__project=obj).count()
    #     done = QcTask.objects.filter(sample__project=obj).exclude(result=None).count()
    #     if done != total or not total:
    #         obj.qc_date = None
    #         obj.save()
    #         left = (obj.due_date - timedelta(obj.ana_cycle + obj.seq_cycle + obj.lib_cycle) - date.today()).days
    #         if left >= 0:
    #             return '%s/%s-余%s天' % (done, total, left)
    #         else:
    #             return format_html('<span style="color:{};">{}</span>', 'red', '%s/%s-延%s天' % (done, total, -left))
    #     else:
    #         obj.qc_date = QcTask.objects.filter(sample__project=obj).order_by('-date').first().date
    #         obj.save()
    #         left = (obj.due_date - timedelta(obj.ana_cycle + obj.seq_cycle + obj.lib_cycle) - obj.qc_date).days
    #         if left >= 0:
    #             return '%s-提前%s天' % (obj.qc_date.strftime('%Y%m%d'), left)
    #         else:
    #             return format_html('<span style="color:{};">{}</span>', 'red', '%s-延%s天' %
    #                                (obj.qc_date.strftime('%Y%m%d'), -left))
    # qc_status.short_description = '质检进度'

    def lib_status(self, obj):
        if not obj.due_date or not obj.is_lib:
            return '-'
        total = LibTask.objects.filter(sample__project=obj).count()
        done = LibTask.objects.filter(sample__project=obj).exclude(result=None).count()
        if done != total or not total:
            obj.lib_date = None
            obj.save()
            left = (obj.due_date - timedelta(obj.ana_cycle + obj.seq_cycle) - date.today()).days
            if left >= 0:
                return '%s/%s-余%s天' % (done, total, left)
            else:
                return format_html('<span style="color:{};">{}</span>', 'red', '%s/%s-延%s天' % (done, total, -left))
        else:
            obj.lib_date = LibTask.objects.filter(sample__project=obj).order_by('-date').first().date
            obj.save()
            left = (obj.due_date - timedelta(obj.ana_cycle + obj.seq_cycle) - obj.lib_date).days
            if left >= 0:
                return '%s-提前%s天' % (obj.lib_date.strftime('%Y%m%d'), left)
            else:
                return format_html('<span style="color:{};">{}</span>', 'red', '%s-延%s天' %
                                   (obj.lib_date.strftime('%Y%m%d'), -left))
    lib_status.short_description = '建库进度'

    def seq_status(self, obj):
        if not obj.due_date:
            return '-'
        if not obj.seq_end_date:
            left = (obj.due_date - timedelta(obj.ana_cycle) - date.today()).days
            if left >= 0:
                return '余%s天' % left
            else:
                return format_html('<span style="color:{};">{}</span>', 'red', '延%s天' % -left)
        else:
            left = (obj.due_date - timedelta(obj.ana_cycle) - obj.seq_end_date).days
            if left >= 0:
                return '%s-提前%s天' % (obj.seq_end_date.strftime('%Y%m%d'), left)
            else:
                return format_html('<span style="color:{};">{}</span>', 'red', '%s-延%s天'
                                   % (obj.seq_end_date.strftime('%Y%m%d'), -left))
    seq_status.short_description = '测序进度'

    def ana_status(self, obj):
        if not obj.due_date:
            return '-'
        if not obj.ana_end_date:
            left = (obj.due_date - date.today()).days
            if left >= 0:
                return '余%s天' % left
            else:
                return format_html('<span style="color:{};">{}</span>', 'red', '延%s天' % -left)
        else:
            left = (obj.due_date - obj.ana_end_date).days
            if left >= 0:
                return '%s-提前%s天' % (obj.ana_end_date.strftime('%Y%m%d'), left)
            else:
                return format_html('<span style="color:{};">{}</span>', 'red', '%s-延%s天'
                                   % (obj.ana_end_date.strftime('%Y%m%d'), -left))
    ana_status.short_description = '分析进度'

    # def make_confirm(self, request, queryset):
    #     projects = []
    #     for obj in queryset:
    #         qs = SampleInfo.objects.filter(project=obj)
    #         if not obj.is_ext and not obj.is_qc and not obj.is_lib:
    #             receive_date = qs.last().receive_date
    #             cycle = obj.ext_cycle + obj.qc_cycle + obj.lib_cycle + obj.seq_cycle + obj.ana_cycle
    #             due_date = add_business_days(receive_date, cycle)
    #             obj.due_date = due_date
    #             obj.save()
    #         if qs.count():
    #             projects += list(set(qs.values_list('project__pk', flat=True)))
    #     rows_updated = queryset.filter(id__in=projects).update(is_confirm=True)
    #     select_num = queryset.count()
    #     if rows_updated:
    #         self.message_user(request, '%s 个项目已经完成确认可启动, %s 个项目不含样品无法启动'
    #                           % (rows_updated, select_num-rows_updated))
    #     else:
    #         self.message_user(request, '所选项目不含样品或系统问题无法确认启动', level=messages.ERROR)
    # make_confirm.short_description = '设置所选项目为确认可启动状态'

    # 项目确认
    # def make_confirm(self, request, queryset):
    #     projects = []
    #     for obj in queryset:
    #         qs = SampleInfo.objects.filter(project=obj)
    #         if not obj.is_ext and not obj.is_lib:
    #             receive_date = qs.last().receive_date
    #             cycle = obj.ext_cycle + obj.qc_cycle + obj.lib_cycle + obj.seq_cycle + obj.ana_cycle
    #             due_date = add_business_days(receive_date, cycle)
    #             obj.due_date = due_date
    #             obj.save()
    #         if qs.count():
    #             projects += list(set(qs.values_list('project__pk', flat=True)))
    #     rows_updated = queryset.filter(id__in=projects).update(is_confirm=True)
    #     select_num = queryset.count()
    #     if rows_updated:
    #         self.message_user(request, '%s 个项目已经完成确认可启动, %s 个项目不含样品无法启动'
    #                           % (rows_updated, select_num-rows_updated))
    #     else:
    #         self.message_user(request, '所选项目不含样品或系统问题无法确认启动', level=messages.ERROR)
    # make_confirm.short_description = '设置所选项目为确认可启动状态'

    # def save_model(self, request, obj, form, change):
    #     if obj.due_date:
    #         project = Project.objects.filter(name=obj).first()
    #         old_cycle = project.ext_cycle + project.qc_cycle + project.lib_cycle +
    # project.seq_cycle + project.ana_cycle
    #         new_cycle = obj.ext_cycle + obj.qc_cycle + obj.lib_cycle + obj.seq_cycle + obj.ana_cycle
    #         obj.due_date = add_business_days(project.due_date, new_cycle - old_cycle)
    #     if obj.contract and not obj.id:
    #         obj.save()
    #         # 项目新建，通知实验管理1
    #         for j in User.objects.filter(groups__id=1):
    #             notify.send(request.user, recipient=j, verb='新增了项目', description="项目ID:%s\t合同名称：%s" %
    #                                                                              (obj.id, obj.contract.name))

    # def get_changelist_formset(self, request, **kwargs):
    #     kwargs['formset'] = ProjectAdminFormSet
    #     print(ProjectAdminFormSet)
    #     print(super(ProjectAdmin, self).get_changelist_formset(request, **kwargs))
    #     # if request.user.has_perm('pm.add_project')
    #     return super(ProjectAdmin, self).get_changelist_formset(request, **kwargs)

    def get_list_display_links(self, request, list_display):
        if not request.user.has_perm('pm.add_project'):
            return
        return ['contract_name']

    def get_queryset(self, request):
        # 只允许管理员和拥有该模型新增权限的人员才能查看所有样品
        qs = super(ProjectAdmin, self).get_queryset(request)
        if request.user.is_superuser or request.user.has_perm('pm.add_project'):
            return qs
        return qs.filter(contract__salesman=request.user)

    def get_actions(self, request):
        # 无权限人员取消actions
        actions = super(ProjectAdmin, self).get_actions(request)
        if not request.user.has_perm('pm.add_project'):
            actions = None
        return actions


# 提取提交表
class ExtSubmitForm(forms.ModelForm):

    # 已经提交提取的样品不显示
    def __init__(self, *args, **kwargs):
        forms.ModelForm.__init__(self, *args, **kwargs)
        if 'sample' in self.fields:
            values = ExtTask.objects.all().values_list('sample__pk', flat=True)
            self.fields['sample'].queryset = SampleInfo.is_ext_objects.exclude(id__in=list(set(values)))


# 提取提交管理
class ExtSubmitAdmin(admin.ModelAdmin):
    form = ExtSubmitForm
    list_display = ['ext_slug', 'slug', 'ext_man', 'ext_cycle', 'contract_count', 'project_count', 'sample_count',
                    'date', 'is_submit']
    filter_horizontal = ('sample',)
    fields = ('slug', 'ext_slug', 'ext_man', 'date', 'sample', 'is_submit', 'ext_cycle',)
    raw_id_fields = ['ext_slug', 'ext_man',
                     ]

    # def is_exts(self, obj):
    #     if Project.is_ext:
    #         # return [obj.is_ext.value,
    #         #         # obj.id, obj.contract_number,  obj.contract_name, obj.sub_number, obj.sub_project,
    #         #         # obj.customer_name, obj.saleman,
    #         #         # obj.project_personnel,
    #         #         ]
    #         return obj.is_exts is True
    # is_exts.short_description = '已经提取'

    def contract_count(self, obj):
        return len(set(i.project.contract.contract_number for i in obj.sample.all()))
    contract_count.short_description = '合同数'

    def project_count(self, obj):
        return len(set([i.project.name for i in obj.sample.all()]))
    project_count.short_description = '项目数'

    def sample_count(self, obj):
        return obj.sample.all().count()
    sample_count.short_description = '样品数'

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.is_submit:
            return ['slug', 'date', 'sample', 'is_submit']
        return ['slug', 'date', ]

    def save_model(self, request, obj, form, change):
        # 选中提交复选框时自动记录提交时间
        if obj.is_submit and not obj.date:
            obj.date = date.today()
            projects = []
            for i in set(projects):
                if not i.due_date:
                    cycle = i.ext_cycle + i.lib_cycle + i.seq_cycle + i.ana_cycle
                    i.due_date = add_business_days(date.today(), cycle)
                    i.save()
        obj.save()


# class QcSubmitForm(forms.ModelForm):
#     # 如果需要提取的显示已经合格的样品，已经质检合格的或正在质检的不显示
#     def __init__(self, *args, **kwargs):
#         forms.ModelForm.__init__(self, *args, **kwargs)
#         if 'sample' in self.fields:
#             ext_values = set(SampleInfo.is_ext_objects.values_list('pk', flat=True))\
#                         - set(ExtTask.objects.filter(result=True).values_list('sample__pk', flat=True))
#             qc_values = QcTask.objects.all().values_list('sample__pk', flat=True)
#             self.fields['sample'].queryset = SampleInfo.is_qc_objects.exclude(id__in=list(ext_values))\
#                 .exclude(id__in=list(set(qc_values)))
#
#     def clean(self):
#         self.instance.__sample__ = self.cleaned_data['sample']
#
#
# class QcSubmitAdmin(admin.ModelAdmin):
#     form = QcSubmitForm
#     list_display = ['slug', 'contract_count', 'project_count', 'sample_count', 'date', 'is_submit']
#     filter_horizontal = ('sample',)
#     fields = ('slug', 'date', 'sample', 'is_submit')
#
#     def contract_count(self, obj):
#         return len(set(i.project.contract.contract_number for i in obj.sample.all()))
#     contract_count.short_description = '合同数'
#
#     def project_count(self, obj):
#         return len(set([i.project.name for i in obj.sample.all()]))
#     project_count.short_description = '项目数'
#
#     def sample_count(self, obj):
#         return obj.sample.all().count()
#     sample_count.short_description = '样品数'
#
#     def get_readonly_fields(self, request, obj=None):
#         if obj and obj.is_submit:
#             return ['slug', 'date', 'sample', 'is_submit']
#         return ['slug', 'date']
#
#     def save_model(self, request, obj, form, change):
#         # 选中提交复选框时自动记录提交时间
#         if obj.is_submit and not obj.date:
#             obj.date = date.today()
#             projects = []
#             for sample in form.instance.__sample__:
#                 QcTask.objects.create(sample=sample, sub_date=date.today())
#                 projects.append(sample.project)
#             for i in set(projects):
#                 if not i.due_date:
#                     cycle = i.qc_cycle + i.lib_cycle + i.seq_cycle + i.ana_cycle
#                     i.due_date = add_business_days(date.today(), cycle)
#                     i.save()
#         obj.save()


# class LibSubmitForm(forms.ModelForm):
#     # 如果需要质检的显示已经合格和可以风险建库的样品，已经建库合格的或正在建库的不显示
#     def __init__(self, *args, **kwargs):
#         forms.ModelForm.__init__(self, *args, **kwargs)
#         if 'sample' in self.fields:
#             qc_values = set(SampleInfo.is_ext_objects.values_list('pk', flat=True))\
#                          - set(QcTask.objects.filter(result__in=[1, 2]).values_list('sample__pk', flat=True))
#             lib_values = LibTask.objects.exclude(result=False).values_list('sample__pk', flat=True)
#             self.fields['sample'].queryset = SampleInfo.is_lib_objects.exclude(id__in=list(qc_values))\
#                 .exclude(id__in=list(set(lib_values)))
#
#     def clean(self):
#         self.instance.__sample__ = self.cleaned_data['sample']

# 建库提交表
class LibSubmitForm(forms.ModelForm):
    # 如果需要提取的显示已经合格的样品和风险建库的样品，已经在建库合格的和正在建库的不显示
    def __init__(self, *args, **kwargs):
        forms.ModelForm.__init__(self, *args, **kwargs)
        if 'sample' in self.fields:
            ext_values = set(SampleInfo.is_ext_objects.values_list('pk', flat=True))\
                      - set(ExtTask.objects.filter(result=True).values_list('sample__pk', flat=True))
            lib_values = LibTask.objects.exclude(result=False).values_list('sample__pk', flat=True)
            self.fields['sample'].queryset = SampleInfo.is_lib_objects.exclude(id__in=list(ext_values))\
                .exclude(id__in=list(set(lib_values)))


# 建库提交管理
class LibSubmitAdmin(admin.ModelAdmin):
    form = LibSubmitForm
    list_display = ['lib_slug', 'slug', 'lib_man', 'contract_count', 'project_count', 'sample_count', 'date',
                    'is_submit']
    filter_horizontal = ('sample',)
    fields = ('slug', 'lib_slug', 'lib_man', 'date', 'sample', 'is_submit', 'lib_cycle',)
    raw_id_fields = ['lib_slug', 'lib_man',
                     ]

    def contract_count(self, obj):
        return len(set(i.project.contract.contract_number for i in obj.sample.all()))
    contract_count.short_description = '合同数'

    def project_count(self, obj):
        return len(set([i.project.name for i in obj.sample.all()]))
    project_count.short_description = '项目数'

    def sample_count(self, obj):
        return obj.sample.all().count()
    sample_count.short_description = '样品数'

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.is_submit:
            return ['slug', 'date', 'sample', 'is_submit']
        return ['slug', 'date']

    def save_model(self, request, obj, form, change):
        # 选中提交复选框时自动记录提交时间
        if obj.is_submit and not obj.date:
            obj.date = date.today()
            projects = []
            for i in set(projects):
                if not i.due_date:
                    cycle = i.lib_cycle + i.seq_cycle + i.ana_cycle
                    i.due_date = add_business_days(date.today(), cycle)
                    i.save()
        obj.save()


# 测序提交表
class SeqSubmitForm(forms.ModelForm):
    # pass
    # 如果需要建库的显示已经合格的样品和风险测序的样品，已经在测序合格的和正在测序的不显示
    def __init__(self, *args, **kwargs):
        forms.ModelForm.__init__(self, *args, **kwargs)
        if 'sample' in self.fields:
            lib_values = set(SampleInfo.is_lib_objects.values_list('pk', flat=True)) \
                         - set(LibTask.objects.filter(result=True).values_list('sample__pk', flat=True))
            seq_values = SeqTask.objects.exclude(result=False).values_list('sample__pk', flat=True)
            self.fields['sample'].queryset = SampleInfo.is_lib_objects.exclude(id__in=list(seq_values)) \
                .exclude(id__in=list(set(lib_values)))


# 测序提交管理
class SeqSubmitAdmin(admin.ModelAdmin):
    # form = SeqSubmitForm
    list_display = ['seq_slug', 'slug', 'seq_man', 'contract_count', 'project_count', 'sample_count', 'date', 'is_submit']
    filter_horizontal = ('sample',)
    fields = ('slug', 'seq_slug', 'seq_man', 'date', 'sample', 'is_submit', 'seq_cycle')
    raw_id_fields = ['seq_slug', 'seq_man',
                     ]

    def contract_count(self, obj):
        return len(set(i.project.contract.contract_number for i in obj.sample.all()))

    contract_count.short_description = '合同数'

    def project_count(self, obj):
        return len(set([i.project.name for i in obj.sample.all()]))

    project_count.short_description = '项目数'

    def sample_count(self, obj):
        return obj.sample.all().count()

    sample_count.short_description = '样品数'

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.is_submit:
            return ['slug', 'date', 'sample', 'is_submit']
        return ['slug', 'date']

    def save_model(self, request, obj, form, change):
        # 选中提交复选框时自动记录提交时间
        if obj.is_submit and not obj.date:
            obj.date = date.today()
            projects = []
            for i in set(projects):
                if not i.due_date:
                    cycle = i.lib_cycle + i.seq_cycle + i.ana_cycle
                    i.due_date = add_business_days(date.today(), cycle)
                    i.save()
        obj.save()


# 分析提交表
class AnaSubmitForm(forms.ModelForm):
    # pass
    # 如果需要测序的显示已经合格的样品和风险分析的样品，已经在分析合格的和正在分析的不显示
    def __init__(self, *args, **kwargs):
        forms.ModelForm.__init__(self, *args, **kwargs)
        if 'sample' in self.fields:
            seq_values = set(SampleInfo.is_seq_objects.values_list('pk', flat=True)) \
                         - set(SeqTask.objects.filter(result=True).values_list('sample__pk', flat=True))
            ana_values = AnaTask.objects.exclude(result=False).values_list('sample__pk', flat=True)
            self.fields['sample'].queryset = SampleInfo.is_seq_objects.exclude(id__in=list(ana_values)) \
                .exclude(id__in=list(set(seq_values)))


# 分析提交管理
class AnaSubmitAdmin(admin.ModelAdmin):
    # form = AnaSubmitForm
    list_display = ['slug', 'ana_slug', 'ana_man', 'contract_count', 'project_count', 'sample_count', 'date',
                    'is_submit']
    filter_horizontal = ('sample',)
    fields = ('slug', 'ana_slug', 'ana_man', 'date', 'sample', 'is_submit', 'ana_cycle',)
    raw_id_fields = ['ana_slug', 'ana_man',
                     ]

    def contract_count(self, obj):
        return len(set(i.project.contract.contract_number for i in obj.sample.all()))

    contract_count.short_description = '合同数'

    def project_count(self, obj):
        return len(set([i.project.name for i in obj.sample.all()]))

    project_count.short_description = '项目数'

    def sample_count(self, obj):
        return obj.sample.all().count()

    sample_count.short_description = '样品数'

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.is_submit:
            return ['slug', 'date', 'sample', 'is_submit']
        return ['slug', 'date']

    def save_model(self, request, obj, form, change):
        # 选中提交复选框时自动记录提交时间
        if obj.is_submit and not obj.date:
            obj.date = date.today()
            projects = []
            for i in set(projects):
                if not i.due_date:
                    cycle = i.lib_cycle + i.seq_cycle + i.ana_cycle
                    i.due_date = add_business_days(date.today(), cycle)
                    i.save()
        obj.save()


# admin.site.register(Project, ProjectAdmin)
# # admin.site.register(QcSubmit, QcSubmitAdmin)
# admin.site.register(ExtSubmit, ExtSubmitAdmin)
# admin.site.register(LibSubmit, LibSubmitAdmin)
# admin.site.register(SeqSubmit, SeqSubmitAdmin)
# admin.site.register(AnaSubmit, AnaSubmitAdmin)


BMS_admin_site.register(Project, ProjectAdmin)
# admin.site.register(QcSubmit, QcSubmitAdmin)
BMS_admin_site.register(ExtSubmit, ExtSubmitAdmin)
BMS_admin_site.register(LibSubmit, LibSubmitAdmin)
BMS_admin_site.register(SeqSubmit, SeqSubmitAdmin)
BMS_admin_site.register(AnaSubmit, AnaSubmitAdmin)
