from django.contrib import admin
from .models import Invoice, Contract,InvoiceTitle
from fm.models import Invoice as fm_Invoice
from fm.models import Bill
from django.contrib import messages
from datetime import datetime
from django.utils.html import format_html
from django import forms
from django.forms.models import BaseInlineFormSet
from daterange_filter.filter import DateRangeFilter
from django.contrib.admin.views.main import ChangeList
from django.db.models import Sum
from django.contrib.auth.models import User
from import_export import resources
from import_export.admin import ImportExportActionModelAdmin,ExportActionModelAdmin
from import_export import fields
from import_export.widgets import ForeignKeyWidget
from notification.signals import notify
from operator import is_not
from functools import partial
from django.utils import formats
from BMS.admin_bms import BMS_admin_site

class InvoiceTitleAdmin(ImportExportActionModelAdmin):
    """
    Admin class for InvoiceTitle
    """
    list_display = ('title', 'tariffItem')
    fields = ('title', 'tariffItem')
    search_fields = ['title','tariffItem']


class InvoiceForm(forms.ModelForm):
    # 开票金额与合同对应款期额校验 #22
    def clean_amount(self):
        obj_contract = Contract.objects.filter(contract_number=self.cleaned_data['contract']).first()
        if self.cleaned_data['period'] == 'FIS':
            q = Invoice.objects.filter(contract=self.cleaned_data['contract']).filter(period='FIS')\
                .aggregate(Sum('amount'))
            # if q['amount__sum'] + self.cleaned_data['amount'] > obj_contract.fis_amount:
            #     raise forms.ValidationError('首款已开票金额%s元，超出可开票总额' % q['amount__sum'])
        if self.cleaned_data['period'] == 'FIN':
            q = Invoice.objects.filter(contract=self.cleaned_data['contract']).filter(period='FIN')\
                .aggregate(Sum('amount'))
            # if q['amount__sum'] + self.cleaned_data['amount'] > obj_contract.fin_amount:
            #     raise forms.ValidationError('尾款已开票金额%s元，超出可开票总额' % q['amount__sum'])
        return self.cleaned_data['amount']


class InvoiceAdmin(admin.ModelAdmin):
    """
    Admin class for invoice
    """
    form = InvoiceForm
    list_display = ('contract', 'title', 'period', 'amount', 'issuingUnit','note', 'submit')
    actions = ['make_invoice_submit']
    list_display_links = None
    fields = ('contract','title','issuingUnit','period', 'amount','type','content', 'note')

    def make_invoice_submit(self, request, queryset):
        """
        批量提交开票申请
        """
        i = ''
        n = 0
        for obj in queryset:
            if not obj.submit:
                i = fm_Invoice.objects.create(invoice=obj)
                obj.submit = True
                obj.save()
                #新的开票申请 通知财务部5
                for j in User.objects.filter(groups__id=5):
                    notify.send(request.user, recipient=j, verb='提交了开票申请',description="合同名称：%s %s"%(obj.contract.name,obj.period))
            else:
                n += 1
        if i:
            self.message_user(request, '%s 个开票申请已成功提交到财务' % i)
        if n:
            self.message_user(request, '%s 个开票申请已提交过，不能再次提交' % n, level=messages.ERROR)
    make_invoice_submit.short_description = '提交开票申请到财务'


class InvoiceInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super(InvoiceInlineFormSet, self).clean()
        total = {}
        total['fis'] = 0
        total['fin'] = 0
        for form in self.forms:
            if not form.is_valid():
                return
            if form.cleaned_data and not form.cleaned_data['DELETE']:
                if form.cleaned_data['period'] == 'FIS':
                    total['fis'] += form.cleaned_data['amount']
                if form.cleaned_data['period'] == 'FIN':
                    total['fin'] += form.cleaned_data['amount']
            self.instance.__total__ = total


class InvoiceInline(admin.StackedInline):
    model = Invoice
    formset = InvoiceInlineFormSet
    extra = 1
    fields = ('title','title_tariffItem','issuingUnit','period', 'amount','type','content', 'note')
    raw_id_fields = ('title',)
    readonly_fields = ('title_tariffItem',)

    def title_tariffItem(self, obj):
        return obj.title.tariffItem
    title_tariffItem.short_description = '税号'


class ContractChangeList(ChangeList):
    def get_results(self, *args, **kwargs):
        super(ContractChangeList, self).get_results(*args, **kwargs)
        fis_amount = self.result_list.aggregate(fis_sum=Sum('fis_amount'))
        fin_amount = self.result_list.aggregate(fin_sum=Sum('fin_amount'))
        all_amount = self.result_list.aggregate(all_sum=Sum('all_amount'))
        self.amount = (fis_amount['fis_sum'] or 0) + (fin_amount['fin_sum'] or 0)
        self.amount_input = (all_amount['all_sum'] or 0)


class SaleListFilter(admin.SimpleListFilter):
    title = '业务员'
    parameter_name = 'Sale'

    def lookups(self, request, model_admin):
        qs_sale = User.objects.filter(groups__id=3)
        qs_company = User.objects.filter(groups__id=6)
        value = ['sale'] + list(qs_sale.values_list('username', flat=True)) + \
                ['company'] + list(qs_company.values_list('username', flat=True))
        label = ['销售'] + ['——' + i.last_name + i.first_name for i in qs_sale] + \
                ['公司'] + ['——' + i.last_name + i.first_name for i in qs_company]
        return tuple(zip(value, label))

    def queryset(self, request, queryset):
        if self.value() == 'sale':
            return queryset.filter(salesman__in=list(User.objects.filter(groups__id=3)))
        if self.value() == 'company':
            return queryset.filter(salesman__in=list(User.objects.filter(groups__id=6)))
        qs = User.objects.filter(groups__in=[3, 6])
        for i in qs:
            if self.value() == i.username:
                return queryset.filter(salesman=i)


class ContractResource(resources.ModelResource):
    #按照合同号导出
    contract_number = fields.Field(column_name="合同号",attribute="contract_number")
    contract_name = fields.Field(column_name="合同名称",attribute="name")
    invoice_issuingUnit = fields.Field(column_name="开票单位")
    receive_date = fields.Field(column_name="合同寄到日",attribute="receive_date")
    invoice_times = fields.Field(column_name="开票次数")
    invoice_date = fields.Field(column_name="开票日期")
    invoice_income = fields.Field(column_name="回款金额")
    invoice_income_date = fields.Field(column_name="回款时间")
    contract_type = fields.Field(column_name="类型")
    contract_salesman = fields.Field(column_name="业务员")
    contract_price = fields.Field(column_name="单价",attribute="price")
    contract_range = fields.Field(column_name="价格区间",attribute="range")
    contract_all_amount = fields.Field(column_name="总款额",attribute="all_amount")
    contract_fis_amount = fields.Field(column_name="首款",attribute="fis_amount")
    contract_fin_amount = fields.Field(column_name="尾款",attribute="fin_amount")
    contract_send_date = fields.Field(column_name="合同寄出日",attribute="send_date")
    class Meta:
        model = Contract
        skip_unchanged = True
        fields = ('contract_number','contract_name','invoice_issuingUnit','receive_date','invoice_times','invoice_date','invoice_income',
                  'invoice_income_date','contract_type','contract_salesman','contract_price','contract_range',
                  'contract_all_amount','contract_fis_amount','contract_fin_amount','contract_send_date')
        export_order = ('contract_number','contract_name','invoice_issuingUnit','receive_date','invoice_times','invoice_date','invoice_income',
                        'invoice_income_date','contract_type','contract_salesman','contract_price','contract_range',
                  'contract_all_amount','contract_fis_amount','contract_fin_amount','contract_send_date')
    def dehydrate_invoice_issuingUnit(self,contract):
        invoices = Invoice.objects.filter(contract = contract)
        if invoices:
            return invoices[0].title.title
        return ""
    def dehydrate_invoice_times(self, contract):
        return len(fm_Invoice.objects.filter(invoice__contract=contract))
    def dehydrate_invoice_date(self,contract):
        return  [formats.date_format(date, 'Y-m-d') for date in list(filter(partial(is_not, None),fm_Invoice.objects.filter(invoice__contract=contract).values_list('date',flat=True)))]
    def dehydrate_invoice_income(self, contract):
        return [float(income) for income in list(filter(partial(is_not, None),fm_Invoice.objects.filter(invoice__contract=contract).values_list('income',flat=True)))]
    def dehydrate_invoice_income_date(self, contract):
        return [formats.date_format(income_date, 'Y-m-d') for income_date in list(filter(partial(is_not, None),fm_Invoice.objects.filter(invoice__contract=contract).values_list('income_date',flat=True)))]
    def dehydrate_contract_type(self,contract):
        return contract.get_type_display()
    def dehydrate_contract_range(self,contract):
        return contract.get_range_display()
    def dehydrate_contract_salesman(self,contract):
        return "%s%s"%(contract.salesman.last_name,contract.salesman.first_name)


class ContractAdmin(ExportActionModelAdmin):
    resource_class = ContractResource
    """
    Admin class for Contract
    """
    list_display = ('contract_number', 'name','title_tariffItem', 'type', 'salesman_name', 'price', 'range', 'all_amount', 'fis_income',
                    'fin_income', 'send_date', 'tracking_number', 'receive_date', 'file_link')
    inlines = [
        InvoiceInline,
    ]
    ordering = ['-id']
    fieldsets = (
        ('基本信息', {
            'fields': ('contract_number', 'name', 'type', 'salesman',('contacts','contact_phone'), ('price', 'range'), ('fis_amount', 'fis_amount_in', 'fin_amount', 'fin_amount_in','all_amount'),('contact_note'))
        }),
        ('邮寄信息', {
            'fields': ('tracking_number','send_date','receive_date')
        }),
        ('上传合同', {
            'fields': ('contract_file',)
        })
    )
    raw_id_fields = ['salesman']
    search_fields = ['contract_number', 'name', 'tracking_number']
    actions = ['make_receive']
    def title_tariffItem(self,obj):
        #抬头的单位名称
        invoices = Invoice.objects.filter(contract=obj)
        if invoices:
            return invoices[0].title.title
        return ""
    title_tariffItem.short_description = "单位"
    def salesman_name(self, obj):
        # 销售用户名或姓名显示
        name = obj.salesman.last_name + obj.salesman.first_name
        if name:
            return name
        return obj.salesman
    salesman_name.short_description = '业务员'

    def fis_income(self, obj):
        # 首款到账信息显示
        amount = obj.fis_amount
        if amount==0:
            if not obj.fis_date:
                obj.fis_amount_in = 0
                obj.fis_date = datetime.now().strftime("%Y-%m-%d")
                obj.save()
        income = obj.fis_amount_in or 0

        if amount - income > 0:
            return format_html('<span style="color:{};">{}</span>', 'red', '%s/%s' % (income, amount))
        elif amount - income == 0:
            if amount == 0 :
                return '%s/0'%(income)
            return '%s/%s' % (income, obj.fis_date)
        else:
            return format_html('<span style="color:{};">{}</span>', 'blue','%s/%s/%s' % (income,amount,obj.fis_date))
    fis_income.short_description = '首款'

    def fin_income(self, obj):
        # 尾款到账信息显示
        amount = obj.fin_amount
        if amount==0:
            if not obj.fin_date:
                obj.fin_amount_in = 0
                obj.fin_date = datetime.now().strftime("%Y-%m-%d")
                obj.save()
        income = obj.fin_amount_in or 0
        if amount - income > 0:
            return format_html('<span style="color:{};">{}</span>', 'red', '%s/%s' % (income, amount))
        elif amount - income == 0:
            if amount == 0 :
                return '%s/0'%(income)
            return '%s/%s' % (income, obj.fin_date)
        else:
            return format_html('<span style="color:{};">{}</span>', 'blue','%s/%s/%s' % (income,amount,obj.fin_date))
    fin_income.short_description = '尾款'

    def make_receive(self, request, queryset):
        # 批量记录合同回寄时间戳
        rows_updated = queryset.update(receive_date=datetime.now())
        for obj in queryset:
            if rows_updated:
                #合同寄到日 通知项目管理2
                for j in User.objects.filter(groups__id=2):
                    notify.send(request.user, recipient=j, verb='客户收到新合同',\
                                description="合同号：%s\t合同名称：%s\t合同联系人：%s\t电话：%s"%\
                                            (obj.contract_number,obj.name,obj.contacts,obj.contact_phone))
                self.message_user(request, '%s 个合同寄到登记已完成' % rows_updated)
            else:
                self.message_user(request, '%s 未能成功登记' % rows_updated, level=messages.ERROR)
    make_receive.short_description = '登记所选合同已收到'

    def get_changelist(self, request):
        return ContractChangeList

    def get_list_display_links(self, request, list_display):
        if not request.user.has_perm('mm.add_contract'):
            return
        return ['contract_number']

    def get_actions(self, request):
        actions = super(ContractAdmin, self).get_actions(request)
        if not request.user.has_perm('mm.delete_contract'):
            if "delete_selected" in actions:
                del actions['delete_selected']
            if "make_receive" in actions:
                del actions['make_receive']
        return actions

    # def get_readonly_fields(self, request, obj=None):
        # if obj.send_date:
        #     return ['contract_number', 'name', 'price', 'range', 'fis_amount', 'fin_amount', 'contract_file']
        # return

    def get_formsets_with_inlines(self, request, obj=None):
        for inline in self.get_inline_instances(request, obj):
            if isinstance(inline, InvoiceInline) and obj is None:
                continue
            yield inline.get_formset(request, obj), inline

    def get_queryset(self, request):
        # 只允许管理员,拥有该模型新增权限的人员，销售总监才能查看所有
        haved_perm = False
        for group in request.user.groups.all():
            if group.id == 7:
                haved_perm=True
        qs = super(ContractAdmin, self).get_queryset(request)
        #TODO 给财务开通查询所有合同的权限，暂时先用
        if request.user.is_superuser or request.user.has_perm('mm.add_contract') or haved_perm or request.user.id == 40 or request.user.id == 6:
            return qs
        return qs.filter(salesman=request.user)

    def get_list_filter(self, request):
        #销售总监，admin，有新增权限的人可以看到salelistFilter
        haved_perm = False
        for group in request.user.groups.all():
            if group.id == 7:
                haved_perm=True
        if request.user.is_superuser or request.user.has_perm('mm.add_contract') or haved_perm:
            return [
                SaleListFilter,
                'type',
                ('send_date', DateRangeFilter),
            ]
        # elif haved_perm:
        #     return [
        #         SaleListFilter,
        #         'type',
        #         ('send_date', DateRangeFilter),
        #     ]
        return [
            'type',
            ('send_date', DateRangeFilter),
        ]

    def get_readonly_fields(self, request, obj=None):
        if not request.user.has_perm('mm.delete_contract'):
            return ['contract_number', 'name', 'type', 'salesman','contacts','contact_phone', 'price', 'range', 'fis_amount', 'fin_amount',
                    'all_amount','tracking_number', 'send_date', 'receive_date', 'contract_file']
        return []

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        if instances:
            fis_amount = instances[0].contract.fis_amount
            fin_amount = instances[0].contract.fin_amount
            # if fis_amount >= formset.instance.__total__['fis'] and fin_amount >= formset.instance.__total__['fin']:
            for instance in instances:
                instance.save()
            formset.save_m2m()
            # else:
            #     messages.set_level(request, messages.ERROR)
            #     self.message_user(request, '开票申请总额超过对应款期可开额度,未成功添加开票', level=messages.ERROR)

    def save_model(self, request, obj, form, change):
        """
        1、新增快递单号时自动记录时间戳
        """
        if obj.tracking_number and not obj.send_date:
            obj.send_date = datetime.now()
        elif not obj.tracking_number:
            obj.send_date = None
        if Contract.objects.filter(id=obj.id):
            if obj.receive_date and Contract.objects.filter(id=obj.id)[0].receive_date != obj.receive_date:
                #合同寄到日有变动就 通知项目管理2
                for j in User.objects.filter(groups__id=2):
                    notify.send(request.user, recipient=j, verb='客户收到新合同',\
                                description="合同号：%s\t合同名称：%s\t合同联系人：%s\t电话：%s"%\
                                            (obj.contract_number,obj.name,obj.contacts,obj.contact_phone))
        else:
            if obj.receive_date:
                #新增合同时，就有寄到日有变动就 通知项目管理2
                for j in User.objects.filter(groups__id=2):
                    notify.send(request.user, recipient=j, verb='客户收到新合同',\
                                description="合同号：%s\t合同名称：%s\t合同联系人：%s\t电话：%s"%\
                                            (obj.contract_number,obj.name,obj.contacts,obj.contact_phone))
        obj.save()

# admin.site.register(Contract, ContractAdmin)
# admin.site.register(Invoice, InvoiceAdmin)
# admin.site.register(InvoiceTitle,InvoiceTitleAdmin)


BMS_admin_site.register(Contract, ContractAdmin)
BMS_admin_site.register(Invoice, InvoiceAdmin)
BMS_admin_site.register(InvoiceTitle, InvoiceTitleAdmin)
