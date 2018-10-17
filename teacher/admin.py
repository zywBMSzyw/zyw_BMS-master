from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.template.response import TemplateResponse
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from import_export import resources
from import_export import fields
from import_export.admin import ImportExportActionModelAdmin, ImportExportMixinBase
from import_export.forms import ConfirmImportForm, ImportForm
from django.utils.translation import ugettext_lazy as _

from BMS.admin_bms import BMS_admin_site

try:
    from django.utils.encoding import force_text
except ImportError:
    from django.utils.encoding import force_unicode as force_text
from teacher.models import SampleInfoForm, SampleInfo
import datetime
from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpResponse
...

# def send(request,):
#     msg=''
#     send_mail('标题','内容',settings.EMAIL_FROM,
#               '目标邮箱',
#               html_message=msg)
#     return HttpResponse('ok')



#选择可编辑字段
def get_editable(obj):
    if obj.sample_status == 2:
        return (obj.sampleinfoformid,)
    else:
        return (obj.sampleinfoformid,)
get_editable.short_description = "点击查看详情"
#编辑可看字段
# def get_display(obj):
#     if obj.sample_status:
#         return (obj.sampleinfoformid,)
#     else:
#         return (obj.sampleinfoformid,obj.time_to_upload,obj.color_status,obj.file_link,obj.jindu_status)

class SampleInline(admin.TabularInline):
    model = SampleInfo
    fields = ['sampleinfoform','sample_name','sample_receiver_name','tube_number','sample_type','is_extract','remarks','data_request']
    readonly_fields = ['sampleinfoform','sample_name','sample_receiver_name','tube_number','is_extract','remarks','data_request','sample_type']

    #设置老师没有导入功能,没有用
    def has_add_permission(self, request):
        try:
            current_group_set = Group.objects.get(user=request.user)
        except:
            return True
        if current_group_set.name == "老师":
            return False
        else:
            return True

#上传管理器
class SampleInfoResource(resources.ModelResource):
    class Meta:
        model = SampleInfo
        skip_unchanged = True
        fields = ('id','sampleinfoform',
        'sample_name', 'sample_receiver_name','sample_type', 'tube_number', 'is_extract', 'remarks','data_request')
        export_order = ('id','sampleinfoform',
        'sample_name', 'sample_receiver_name','sample_type', 'tube_number', 'is_extract', 'remarks','data_request')

    def get_export_headers(self):
        return ["id","概要信息编号","样品名","实际收到样品名","样品类型(1-g DNA,2-组织,3-细胞,4-土壤,5-粪便其他未提取（请描述))","管数","是否需要提取(0-不需要，1-需要)","备注","数据量要求"]

    def init_instance(self, row=None):
        if not row:
            row = {}
        instance = self._meta.model()
        # instance = SampleInfo()
        for attr, value in row.items():
            setattr(instance, attr, value)
        instance.id = str(int(SampleInfo.objects.latest('id').id)+1)
        instance.sampleinfoform = SampleInfoForm.objects.get(sampleinfoformid=row['概要信息编号'])
        instance.sample_name = row['样品名']
        instance.sample_receiver_name = row['实际收到样品名']
        instance.sample_type = row['样品类型(1-g DNA,2-组织,3-细胞,4-土壤,5-粪便其他未提取（请描述))']
        instance.tube_number = row['管数']
        instance.is_extract = row['是否需要提取(0-不需要，1-需要)']
        instance.remarks = row['备注']
        instance.data_request = row['数据量要求']
        send_mail('样品核对通知', '<h3>编号{0}的样品核对信息已上传，请查看核对'.format(instance.sampleinfoform.sampleinfoformid), settings.EMAIL_FROM,
                  [instance.sampleinfoform.partner_email, ],
                  fail_silently=False)
        return instance

    def get_diff_headers(self):
        return ["id","概要信息编号","样品名","实际收到样品名","样品类型(1-g DNA,2-组织,3-细胞,4-土壤,5-粪便其他未提取（请描述))","管数","是否需要提取(0-不需要，1-需要)","备注","数据量要求"]

    # def before_import(self, dataset, using_transactions, dry_run, **kwargs):
    #
    # sample_name = fields.Field(column_name='样品名')
    # sample_receiver_name = fields.Field(column_name='实际收到样品名')
    # sample_type = fields.Field(column_name='样品类型(1-g DNA,2-组织,3-细胞,4-土壤,5-粪便其他未提取（请描述))')
    # tube_number = fields.Field(column_name='管数')
    # is_extract =  fields.Field(column_name='是否需要提取(0-不需要，1-需要)')
    # remarks = fields.Field(column_name='备注')
    # data_request = fields.Field(column_name='数据量要求')

#样品概要管理
class SampleInfoFormAdmin(ImportExportActionModelAdmin):

    resource_class = SampleInfoResource

    inlines = [SampleInline]

    list_per_page = 30

    save_as_continue = False

    save_on_top = False




    list_display = ('sampleinfoformid','time_to_upload','color_status','file_link','jindu_status')
    # list_display = ('sampleinfoformid',get_editable,'time_to_upload','color_status','file_link','jindu_status')

    list_display_links = ('sampleinfoformid',)


    actions = ['make_sampleinfoform_submit','insure_sampleinfoform']

    def get_queryset(self, request):
        qs = super(SampleInfoFormAdmin, self).get_queryset(request)
        try:
            current_group_set = Group.objects.get(user=request.user)
            if current_group_set.name == "实验员":
                return qs
            elif current_group_set.name == "老师":
                return qs.filter(partner=request.user)
        except:
            return qs


    #可以改变增加表单里的内容
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_delete'] = True
        # if not Invoice.objects.get(id=object_id).invoice_code and not request.user.has_perm('fm.add_invoice'):
        extra_context['show_save'] = True
        extra_context['show_save_as_new'] = True
        extra_context['show_save_and_continue'] = False
        return super(SampleInfoFormAdmin, self).change_view(request, object_id, form_url, extra_context=extra_context)
# 设置老师没有导入功能


    def import_action(self, request, *args, **kwargs):

        #只有超级用户和老师不能使用导入功能
        try:
            current_group_set = Group.objects.get(user=request.user)
        except:
            return False
        if current_group_set.name == "老师":
            raise Exception("您不能使用导入功能")

        resource = self.get_import_resource_class()(**self.get_import_resource_kwargs(request, *args, **kwargs))

        context = self.get_import_context_data()

        import_formats = self.get_import_formats()
        form_type = self.get_import_form()
        form = form_type(import_formats,
                         request.POST or None,
                         request.FILES or None)

        if request.POST and form.is_valid():
            input_format = import_formats[
                int(form.cleaned_data['input_format'])
            ]()
            import_file = form.cleaned_data['import_file']
            # first always write the uploaded file to disk as it may be a
            # memory file or else based on settings upload handlers
            tmp_storage = self.write_to_tmp_storage(import_file, input_format)

            # then read the file, using the proper format-specific mode
            # warning, big files may exceed memory
            try:
                data = tmp_storage.read(input_format.get_read_mode())
                if not input_format.is_binary() and self.from_encoding:
                    data = force_text(data, self.from_encoding)
                dataset = input_format.create_dataset(data)
            except UnicodeDecodeError as e:
                return HttpResponse(_(u"<h1>Imported file has a wrong encoding: %s</h1>" % e))
            except Exception as e:
                return HttpResponse(
                    _(u"<h1>%s encountered while trying to read file: %s</h1>" % (type(e).__name__, import_file.name)))
            result = resource.import_data(dataset, dry_run=True,
                                          raise_errors=False,
                                          file_name=import_file.name,
                                          user=request.user)

            context['result'] = result

            if not result.has_errors():
                context['confirm_form'] = ConfirmImportForm(initial={
                    'import_file_name': tmp_storage.name,
                    'original_file_name': import_file.name,
                    'input_format': form.cleaned_data['input_format'],
                })

        context.update(self.admin_site.each_context(request))

        context['title'] = _("Import")
        context['form'] = form
        context['opts'] = self.model._meta
        context['fields'] = [f.column_name for f in resource.get_user_visible_fields()]

        request.current_app = self.admin_site.name
        return TemplateResponse(request, [self.import_template_name],
                                context)

    def write_to_tmp_storage(self, import_file, input_format):
        tmp_storage = self.get_tmp_storage_class()()
        data = bytes()
        for chunk in import_file.chunks():
            data += chunk

        tmp_storage.save(data, input_format.get_read_mode())
        return tmp_storage

    #设置实验员没有增加样本功能
    def has_add_permission(self, request):
        try:
            current_group_set = Group.objects.get(user=request.user)
        except:
            return True
        if current_group_set.name == "实验员":
            return False
        else:
            return True

    #测试
    # def test1(self, request, queryset):
    #     i = ''
    #     n = 0
    #     for obj in queryset:
    #         if obj.sample_status == 2:
    #             obj.sample_status = 0
    #             obj.save()
    #         else:
    #             n += 1


    def save_model(self, request, obj, form, change):
        try:
            current_group_set = Group.objects.get(user=request.user)
            # if current_group_set.name == "实验员":
            #     if not obj.sampleinfoformid:
            #         raise Exception("实验员不能创建样本！")
            #     else:
            #         obj.man_to_upload = request.user
            #         obj.time_to_upload = datetime.datetime.now()
            #         super().save_model(request, obj, form, change)
            if current_group_set.name == "老师":
                if not obj.sampleinfoformid:
                    # print("**********************")
                    # print(str(int(SampleInfoForm.objects.latest("id").id)+1))
                    obj.partner = request.user.username
                    obj.time_to_upload = datetime.datetime.now()
                    obj.sampleinfoformid = request.user.username + '-' +str(datetime.datetime.now().year)+str(datetime.datetime.now().month) + '-'+str(int(SampleInfoForm.objects.latest("id").id)+1)
                super().save_model(request, obj, form, change)
            else:
                super().save_model(request, obj, form, change)
        except:
            super().save_model(request, obj, form, change)

    def get_import_context_data(self, **kwargs):
        return self.get_context_data(**kwargs)

    def get_context_data(self, **kwargs):
        return {}

    def get_import_form(self):
        '''
        Get the form type used to read the import format and file.
        '''
        return ImportForm
    #根据身份获取动作
    def get_actions(self, request):
        actions = super().get_actions(request)
        try:
            current_group_set = Group.objects.get(user=request.user)
        except:
            # print(actions)
            return actions
        if current_group_set.name == "实验员":
            # print(actions)
            del actions['delete_selected']
            del actions['export_admin_action']
            del actions['make_sampleinfoform_submit']
            del actions['insure_sampleinfoform']
            # del actions['test1']
            return actions
        elif current_group_set.name == "老师":
            del actions['delete_selected']
            del actions['export_admin_action']
            return actions

    #提交并发送邮件
    def insure_sampleinfoform(self,request,queryset):
        """
        确认信息
        :param request:
        :param queryset:
        :return:
        """
        i = ''
        n = 0
        for obj in queryset:
            if obj.sample_status == 0:
                obj.sample_status = 1
                msg = "<h3>{0}客户的样品概要信息已上传，请核对</h3>".format(obj.partner)
                send_mail('样品收到通知', '{0}客户的样本已经上传，请查看核对'.format(obj.partner), settings.EMAIL_FROM,
                          ['love949872618@qq.com', ],
                          fail_silently=False)
                obj.save()
            else:
                n += 1

    insure_sampleinfoform.short_description = '样品信息表单提交（并发送邮件）'

    #确认
    def make_sampleinfoform_submit(self, request, queryset):
        """
        提交样品信息表单
        """
        i = ''
        n = 0
        for obj in queryset:
            if obj.sample_status == 1 :
                obj.sample_status = 2
                obj.save()
            else:
                n += 1

    #提示邮件
    make_sampleinfoform_submit.short_description = '样品信息表单确认'

    def get_readonly_fields(self, request, obj=None):
        """  重新定义此函数，限制普通用户所能修改的字段  """
        if request.user.is_superuser:
            self.readonly_fields = []
            return self.readonly_fields
        try:
            current_group_set = Group.objects.get(user=request.user)
            if current_group_set.name == "实验员":
                self.readonly_fields = ('transform_company', 'transform_number',
                                        'transform_contact', 'transform_phone',
                                        'transform_status', 'reciver_address', 'partner', 'partner_company',
                                        'partner_phone', 'partner_email', 'saler',
                                        'sample_receiver', 'sample_checker', 'sample_diwenzhuangtai', 'project_type',
                                        'arrive_time', 'sample_diwenjiezhi',
                                        'sample_num', 'sample_species', 'extract_to_pollute_DNA',
                                        'management_to_rest', 'file_teacher',
                                        "sampleinfoformid", "time_to_upload")
                return self.readonly_fields

            if obj.sample_status:
                self.readonly_fields = ('transform_company','transform_number',
                           'transform_contact','transform_phone',
                           'transform_status','reciver_address','partner', 'partner_company', 'partner_phone','partner_email', 'saler',
                                        'sample_receiver', 'sample_checker', 'sample_diwenzhuangtai','project_type','arrive_time','sample_diwenjiezhi',
                           'sample_num','sample_species','extract_to_pollute_DNA',
                            'management_to_rest','file_teacher',
                            "sampleinfoformid","time_to_upload")
                return self.readonly_fields
        except:
            self.readonly_fields = []
            return self.readonly_fields
        else:
            self.readonly_fields = []
            return self.readonly_fields
        # elif hasattr(obj, 'sample_jindu'):
        #     if obj.sample_jindu:
        #         self.readonly_fields = ('transform_company','transform_number',
        #                    'transform_contact','transform_phone',
        #                    'transform_status','reciver_address','partner', 'partner_company', 'partner_phone','partner_email', 'saler',
        #                                 'sample_receiver', 'sample_checker', 'sample_diwenzhuangtai','project_type','arrive_time','sample_diwenzhuangtai',
        #                    'sample_num','sample_species','extract_to_pollute_DNA',
        #                     'management_to_rest','file_teacher',
        #                     "sampleinfoformid","time_to_upload"
        #                                 )
        #         return self.readonly_fields


    # def change_view(self, request, object_id, form_url='', extra_context=None):
    #     change_obj = DataPaperStore.objects.filter(pk=object_id)
    #     self.get_readonly_fields(request, obj=change_obj)
    #     return super(DataPaperStoreAdmin, self).change_view(request, object_id, form_url, extra_context=extra_context)

    def get_fieldsets(self, request, obj=None):
        fieldsets = ()
        try:
            current_group_set = Group.objects.get(user=request.user)
            if current_group_set.name == "实验员":
                fieldsets = (
            ['物流信息', {
                'fields': ('transform_company','transform_number',
                           'transform_contact','transform_phone',
                           'transform_status','reciver_address'),
            }],['客户信息',{
                'fields': ('partner', 'partner_company', 'partner_phone','partner_email', 'saler'),
            }],['收货信息',{
                'fields': ( 'sample_receiver','sample_checker', 'sample_diwenzhuangtai'),
            }],['服务信息',{
                'fields': ( 'project_type','arrive_time','sample_diwenjiezhi',
                           'sample_num','sample_species','extract_to_pollute_DNA',
                            'management_to_rest','file_teacher',
                            "sampleinfoformid",
                            "time_to_upload"),
                            }])

            elif current_group_set.name == "老师":
                fieldsets = (
                ['物流信息', {
                    'fields': ('transform_company', 'transform_number',
                               'transform_contact', 'transform_phone',
                               'transform_status','reciver_address'),
                }], ['客户信息', {
                    'fields': ( 'partner_company', 'partner_phone','partner_email','saler'),
                }], ['服务信息', {
                    'fields': ('project_type','sample_species','sample_diwenjiezhi',
                               'sample_num', 'extract_to_pollute_DNA',
                               'management_to_rest', 'file_teacher',
                               # "sampleinfoformid",
                               'time_to_upload'),
                }])
        except:
            fieldsets = (
            ['物流信息', {
                'fields': ('transform_company','transform_number',
                           'transform_contact','transform_phone',
                           'transform_status','reciver_address'),
            }],['客户信息',{
                'fields': ('partner', 'partner_company', 'partner_phone','partner_email', 'saler'),
            }],['收货信息',{
                'fields': ( 'man_to_upload','sample_receiver','sample_checker', 'sample_diwenzhuangtai'),
            }],['服务信息',{
                'fields': ( 'project_type','arrive_time','sample_species','sample_diwenzhuangtai',
                           'sample_num','extract_to_pollute_DNA',
                            'management_to_rest','file_teacher',
                            "sampleinfoformid","time_to_upload"),
                            }])
        return fieldsets


    list_filter = ("sample_status",'time_to_upload')
BMS_admin_site.register(SampleInfoForm,SampleInfoFormAdmin)
# admin.site.register(Realbio_User, UserAdmin)
#全站范围内禁用删权限
# admin.site.disable_action('delete_selected')
# admin.site.register(SampleInfo)
# admin.site.register(Product,ProAdmin)
# admin.site.site_header = '杭州锐翌BMS系统'
# admin.site.site_title = '杭州锐翌'




# class SampleInfoAdmin(ImportExportActionModelAdmin):
#     resource_class = SampleInfoResource
#
#
#
# admin.site.register(SampleInfo,SampleInfoAdmin)