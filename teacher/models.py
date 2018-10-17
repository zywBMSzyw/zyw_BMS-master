from django.db import models
from django.contrib.auth import admin
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser

# class Realbio_User(AbstractUser):
#     is_teacher = models.NullBooleanField(blank=True,null=True,verbose_name="是否是老师")
#     is_projectcharge = models.NullBooleanField(blank=True,null=True,verbose_name="是否是项目主管")
#     is_tester =  models.NullBooleanField(blank=True,null=True,verbose_name="是否是实验员")
#     is_saler = models.NullBooleanField(blank=True, null=True, verbose_name="是否是销售代表")
#
#     class Meta:
#         verbose_name = "用户信息"
#         verbose_name_plural = verbose_name
#
#     def __str__(self):
#         return self.username
from django.utils.html import format_html

from BMS.settings import MEDIA_ROOT
import datetime

def upload_to(instance, filename):
    return '/'.join(['teachers',str(datetime.datetime.now().year)+'-'+str(datetime.datetime.now().month),instance.partner,filename])
def upload_to1(instance, filename):
    return '/'.join(['testers',str(datetime.datetime.now().year)+'-'+str(datetime.datetime.now().month),instance.man_to_upload,filename])

class Employee(models.Model):
    name = models.CharField(max_length=200,verbose_name="姓名")
    department = models.CharField(max_length=200,verbose_name="姓名")

    def __str__(self):
        return self.name

class SampleInfoForm(models.Model):

    # sampleinfoformid = models.

    #项目选项
    Project_choices = (
        (1, '微生物宏基因组测序'),
        (2, '微生物扩增子测序------16S'),
        (3, '微生物扩增子测序------ITS'),
        (4, '微生物扩增子测序------古菌；其他'),
        (5, '细菌基因组测序------小片段文库'),
        (6, '细菌基因组测序------PCR-free文库'),
        (7, '细菌基因组测序------2K大片段文库'),
        (8, '细菌基因组测序------5K大片段文库'),
        (9, '细菌基因组测序------SMRT cell DNA 文库'),
        (10, '真菌基因组测序------小片段文库'),
        (11, '真菌基因组测序------PCR-free文库'),
        (12, '真菌基因组测序------2K大片段文库'),
        (13, '真菌基因组测序------5K大片段文库'),
        (14, '真菌基因组测序------SMRT cell DNA 文库'),
        (15, '动植物denovo------180bp'),
        (16, '动植物denovo------300bp'),
        (17, '动植物denovo------500bp'),
        (18, '动植物denovo------2K'),
        (19, '动植物denovo------5K'),
        (20, '动植物denovo------10K'),
        (21, '动植物denovo------20K'),
        (22, '动植物重测序'),
        (23, '人重测序'),
        (24, '外显子测序'),
        (25, '其他'),
    )

    #样品处理选项
    Management_to_the_rest = (
        (1, '项目结束后剩余样品立即返还给客户'),
        (2, '项目结束后剩余样品暂时由锐翌基因保管'),
    )

    #样品状态选项
    Sample_status = (
        (0, '未提交'),
        (1, '已提交，未审核'),
        (2, '已审核')
        )
    #进度
    Sample_jindu = (
        (0, '项目待启动'),
        (1, '项目已完结'),
        )

    #运输状态
    TransForm_Status  = (
        (0, '干冰'),
        (1, '冰袋'),
        (2, '无'),
        (3, '其他'),
        )
    #低温介质到达时状态
    Arrive_Status = (
        (0, '不合格'),
        (1, '合格'),
        )


    #物流信息
    transform_company = models.CharField(max_length=200,verbose_name="运输公司")
    transform_number = models.CharField(max_length=200,verbose_name="快递单号")
    transform_contact = models.ForeignKey(Employee,related_name="物流联系人",verbose_name="物流联系人",null=True,blank=True,
                                          on_delete=models.SET_NULL)
    transform_phone = models.BigIntegerField(verbose_name="寄样联系人电话")
    transform_status = models.IntegerField(choices=TransForm_Status,verbose_name="运输状态",default=2)


    #客户信息
    partner = models.CharField(max_length=200,verbose_name="客户姓名",blank=True,null=True)
    partner_company = models.CharField(max_length=200, verbose_name="合作伙伴单位")
    partner_phone = models.BigIntegerField(verbose_name="合作人联系电话")
    partner_email = models.EmailField(verbose_name="合作邮箱",default='')
    reciver_address = models.CharField(max_length=200,verbose_name="收件地址",default='')
    saler = models.ForeignKey(Employee,related_name="销售联系人",verbose_name="销售代表",blank=True,null=True,on_delete=models.SET_NULL)

    #服务类型
    project_type = models.IntegerField(choices=Project_choices,verbose_name="项目类型",default=1)

    #样品信息
    sample_num = models.IntegerField(verbose_name="样品数量")
    extract_to_pollute_DNA = models.NullBooleanField("DNA提取是否可能有大量非目标DNA污染",default='')
    management_to_rest = models.IntegerField(choices=Management_to_the_rest,
                                             verbose_name="剩余样品处理方式",default=2)
    sample_species = models.CharField(max_length=200, verbose_name="物种",default='')
    sample_diwenjiezhi = models.IntegerField(choices=TransForm_Status,verbose_name="低温保存介质",default=2)

    #上传信息
    # download_model = models.CharField(max_length=200,verbose_name="点击下载表格",default="www.")
    # path_partner = models.CharField(max_length=200,verbose_name="客户上传路径",blank=True,null=True,default='')
    file_teacher = models.FileField(upload_to=upload_to,verbose_name='客户上传文件',blank=True,null=True,default='')
    # file_tester = models.FileField(upload_to=upload_to1,verbose_name='实验室上传文件',blank=True,null=True,default='')
    man_to_upload = models.ForeignKey(User,related_name="上传文件人", verbose_name="公司上传者",blank=True,null=True,
                                                        on_delete=models.SET_NULL)
    time_to_upload = models.DateField(verbose_name="上传时间")
    sampleinfoformid = models.CharField(max_length=200, verbose_name="客户上传表格编号")

    #样品接收信息
    arrive_time = models.DateField(verbose_name="样品接收时间",null=True,blank=True)
    sample_receiver = models.ForeignKey(User,related_name="样品接收人",verbose_name="样品接收人",null=True,blank=True,on_delete=models.SET_NULL)
    sample_checker = models.ForeignKey(User,related_name="物流接收人",verbose_name="样品核对人",blank=True,null=True,on_delete=models.SET_NULL)
    sample_status = models.IntegerField(choices=TransForm_Status,verbose_name="样品状态",default=0)
    sample_jindu = models.IntegerField(choices=Sample_jindu,verbose_name="样品进度",default=0)
    sample_diwenzhuangtai = models.IntegerField(choices=Arrive_Status,verbose_name="低温介质到达时状态",default=0)

    #颜色显示
    color_code = models.CharField(max_length=6,default='')
    color_code1 = models.CharField(max_length=6, default='')

    def __str__(self):
        return self.sampleinfoformid

    class Meta:
        verbose_name = "样品信息"
        verbose_name_plural = "样品信息"


    def file_link(self):
        if self.file_teacher:
            print(self.file_teacher.url)
            return "<a href='{0}'>下载</a>" .format(self.file_teacher.url)
        else:
            return "未上传"

    file_link.allow_tags = True
    file_link.short_description = "已上传信息"

    #状态颜色
    def color_status(self):
        if self.sample_status == 0:
            self.color_code = "red"
        elif self.sample_status == 1:
            self.color_code = "green"
        return format_html(
            '<span style="color: {};">{}</span>',
            self.color_code,
            self.Sample_status[self.sample_status][1],)

    color_status.short_description = "状态"

    #进度颜色
    def jindu_status(self):
        if self.sample_jindu == 1:
            self.color_code1 = "red"
        elif self.sample_jindu == 0:
            self.color_code1 = "blue"
        return format_html(
            '<span style="color: {};">{}</span>',
            self.color_code1,
            self.Sample_jindu[self.sample_jindu][1],)

    jindu_status.short_description = "进度"
class SampleInfo(models.Model):
    #样品种类
    Type_of_Sample = (
        (1, 'g DNA'),
        (2, '组织'),
        (3, '细胞'),
        (4, '土壤'),
        (5, '粪便其他未提取（请描述）'),
    )
    # #样品状态
    # Status_of_Sample = (
    #     (1, '已入库'),
    #     (2, '已立项'),
    # )
    #样品保存介质
    Preservation_medium = (
        (1, '纯水'),
        (2, 'TE buffer'),
        (3, '无水乙醇'),
        (4, 'Trizol其他'),
    )

    #是否经过RNase处理
    Is_RNase_processing = (
        (1, '是'),
        (2, '否'),
    )

    #概要
    sampleinfoform = models.ForeignKey(SampleInfoForm,verbose_name="对应样品概要编号",blank=True,null=True,on_delete=models.CASCADE)
    sample_name = models.CharField(max_length=50,verbose_name="样品名称")
    sample_receiver_name = models.CharField(max_length=50,verbose_name="实际接收样品名称") #*
    density = models.DecimalField('浓度ng/uL', max_digits=5, decimal_places=3, blank=True,null=True)
    volume = models.DecimalField('体积uL', max_digits=5, decimal_places=3,blank=True, null=True)
    purity = models.CharField(max_length=200,verbose_name="纯度",blank=True,null=True)
    tube_number = models.IntegerField(verbose_name="管数量") #*
    is_extract = models.NullBooleanField(verbose_name="是否需要提取",default=False)
    remarks = models.TextField(verbose_name="备注",blank=True,null=True)
    #数据量要求
    data_request = models.CharField(max_length=200,verbose_name="数据量要求",blank=True,null=True)

    sample_type = models.IntegerField(choices=Type_of_Sample,verbose_name="样品类型",default=1)
    # sample_status = models.IntegerField(choices=Status_of_Sample,verbose_name="样品状态",default=1)
    #样品编号
    # sample_id = models
    # sample_used = models.CharField(max_length=200,verbose_name="样品提取用量")
    # sample_rest = models.CharField(max_length=200,verbose_name="样品剩余用量")
    # density_checked = models.DecimalField('浓度ng/uL(公司检测)', max_digits=5, decimal_places=3, null=True)
    # volume_checked = models.DecimalField('体积uL(公司检测)', max_digits=5, decimal_places=3, null=True)
    # D260_280 = models.DecimalField(max_digits=8,decimal_places=1,verbose_name="D260/280")
    # D260_230 = models.DecimalField(max_digits=8,decimal_places=1,verbose_name="D260/230")
    # species = models.CharField(max_length=200,verbose_name="物种")
    # preservation_medium = models.IntegerField(choices=Preservation_medium,verbose_name="样品保存介质",default=1)
    # is_RNase_processing = models.IntegerField(choices=Is_RNase_processing,verbose_name="是否经过RNase处理",default=1)

    #DNA质检
    # quality_control_conclusion = models.TextField(verbose_name="质检报告")

    #跑胶
    # sample_loading = models.CharField(max_length=200,verbose_name="上样量")
    # integrity = models.CharField(max_length=200,verbose_name="完整性")
    # note_running_glue = models.TextField('备注(跑胶)', blank=True, null=True)

    #文库质检
    # lib_code = models.CharField('文库号', max_length=20, null=True)
    # index = models.CharField('Index', max_length=20, null=True)
    # lib_volume = models.DecimalField('体积uL(文库)', max_digits=5, decimal_places=3, null=True)
    # lib_concentration = models.DecimalField('浓度ng/uL(文库)', max_digits=5, decimal_places=3, null=True)
    # lib_total = models.DecimalField('总量ng(文库)', max_digits=5, decimal_places=3, null=True)
    # lib_result = models.NullBooleanField('结论(文库)', null=True)
    # lib_note = models.TextField('备注(文库)', blank=True, null=True)

    def __str__(self):
        return self.sample_name

    class Meta:
        verbose_name = "详细样品信息"
        verbose_name_plural = "详细样品信息"
