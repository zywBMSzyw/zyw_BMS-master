from django.db import models


class Invoice(models.Model):
    invoice = models.OneToOneField(
        'mm.Invoice',
        verbose_name='发票',
    )
    invoice_code = models.CharField('发票号码', max_length=12, unique=True)
    date = models.DateField('开票日期', null=True)
    tracking_number = models.CharField('快递单号', max_length=15, blank=True)
    send_date = models.DateField('寄出日期', null=True,blank=True)
    income_date = models.DateField('到账日期', null=True)
    income = models.DecimalField('到账金额',null=True,max_digits=12,decimal_places=2)
    tax_amount = models.DecimalField('开票税率', max_digits=9, decimal_places=2)
    invoice_file = models.FileField('电子发票', upload_to='uploadsInvoice/%Y/%m',null=True)

    class Meta:
        verbose_name = '发票管理'
        verbose_name_plural = '发票管理'

    def file_link(self):
        if self.invoice_file:
            return "<a href='%s'>下载</a>" % (self.invoice_file.url,)
        else:
            return "未上传"
    file_link.short_description = "电子发票"
    file_link.allow_tags = True

    def __str__(self):
        return '%s' % self.invoice_code


class Bill(models.Model):
    invoice = models.ForeignKey(Invoice, verbose_name='发票')
    income = models.DecimalField('到账金额', max_digits=9, decimal_places=2)
    date = models.DateField('到账日期')

    class Meta:
        verbose_name = '进账管理'
        verbose_name_plural = '进帐管理'

    def __str__(self):
        return '%f' % self.income
