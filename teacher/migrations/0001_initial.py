# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2018-10-16 08:42
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import teacher.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='姓名')),
                ('department', models.CharField(max_length=200, verbose_name='姓名')),
            ],
        ),
        migrations.CreateModel(
            name='SampleInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sample_name', models.CharField(max_length=50, verbose_name='样品名称')),
                ('sample_receiver_name', models.CharField(max_length=50, verbose_name='实际接收样品名称')),
                ('density', models.DecimalField(blank=True, decimal_places=3, max_digits=5, null=True, verbose_name='浓度ng/uL')),
                ('volume', models.DecimalField(blank=True, decimal_places=3, max_digits=5, null=True, verbose_name='体积uL')),
                ('purity', models.CharField(blank=True, max_length=200, null=True, verbose_name='纯度')),
                ('tube_number', models.IntegerField(verbose_name='管数量')),
                ('is_extract', models.NullBooleanField(default=False, verbose_name='是否需要提取')),
                ('remarks', models.TextField(blank=True, null=True, verbose_name='备注')),
                ('data_request', models.CharField(blank=True, max_length=200, null=True, verbose_name='数据量要求')),
                ('sample_type', models.IntegerField(choices=[(1, 'g DNA'), (2, '组织'), (3, '细胞'), (4, '土壤'), (5, '粪便其他未提取（请描述）')], default=1, verbose_name='样品类型')),
            ],
            options={
                'verbose_name': '详细样品信息',
                'verbose_name_plural': '详细样品信息',
            },
        ),
        migrations.CreateModel(
            name='SampleInfoForm',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transform_company', models.CharField(max_length=200, verbose_name='运输公司')),
                ('transform_number', models.CharField(max_length=200, verbose_name='快递单号')),
                ('transform_phone', models.BigIntegerField(verbose_name='寄样联系人电话')),
                ('transform_status', models.IntegerField(choices=[(0, '干冰'), (1, '冰袋'), (2, '无'), (3, '其他')], default=2, verbose_name='运输状态')),
                ('partner', models.CharField(blank=True, max_length=200, null=True, verbose_name='客户姓名')),
                ('partner_company', models.CharField(max_length=200, verbose_name='合作伙伴单位')),
                ('partner_phone', models.BigIntegerField(verbose_name='合作人联系电话')),
                ('partner_email', models.EmailField(default='', max_length=254, verbose_name='合作邮箱')),
                ('reciver_address', models.CharField(default='', max_length=200, verbose_name='收件地址')),
                ('project_type', models.IntegerField(choices=[(1, '微生物宏基因组测序'), (2, '微生物扩增子测序------16S'), (3, '微生物扩增子测序------ITS'), (4, '微生物扩增子测序------古菌；其他'), (5, '细菌基因组测序------小片段文库'), (6, '细菌基因组测序------PCR-free文库'), (7, '细菌基因组测序------2K大片段文库'), (8, '细菌基因组测序------5K大片段文库'), (9, '细菌基因组测序------SMRT cell DNA 文库'), (10, '真菌基因组测序------小片段文库'), (11, '真菌基因组测序------PCR-free文库'), (12, '真菌基因组测序------2K大片段文库'), (13, '真菌基因组测序------5K大片段文库'), (14, '真菌基因组测序------SMRT cell DNA 文库'), (15, '动植物denovo------180bp'), (16, '动植物denovo------300bp'), (17, '动植物denovo------500bp'), (18, '动植物denovo------2K'), (19, '动植物denovo------5K'), (20, '动植物denovo------10K'), (21, '动植物denovo------20K'), (22, '动植物重测序'), (23, '人重测序'), (24, '外显子测序'), (25, '其他')], default=1, verbose_name='项目类型')),
                ('sample_num', models.IntegerField(verbose_name='样品数量')),
                ('extract_to_pollute_DNA', models.NullBooleanField(default='', verbose_name='DNA提取是否可能有大量非目标DNA污染')),
                ('management_to_rest', models.IntegerField(choices=[(1, '项目结束后剩余样品立即返还给客户'), (2, '项目结束后剩余样品暂时由锐翌基因保管')], default=2, verbose_name='剩余样品处理方式')),
                ('sample_species', models.CharField(default='', max_length=200, verbose_name='物种')),
                ('sample_diwenjiezhi', models.IntegerField(choices=[(0, '干冰'), (1, '冰袋'), (2, '无'), (3, '其他')], default=2, verbose_name='低温保存介质')),
                ('file_teacher', models.FileField(blank=True, default='', null=True, upload_to=teacher.models.upload_to, verbose_name='客户上传文件')),
                ('time_to_upload', models.DateField(verbose_name='上传时间')),
                ('sampleinfoformid', models.CharField(max_length=200, verbose_name='客户上传表格编号')),
                ('arrive_time', models.DateField(blank=True, null=True, verbose_name='样品接收时间')),
                ('sample_status', models.IntegerField(choices=[(0, '干冰'), (1, '冰袋'), (2, '无'), (3, '其他')], default=0, verbose_name='样品状态')),
                ('sample_jindu', models.IntegerField(choices=[(0, '项目待启动'), (1, '项目已完结')], default=0, verbose_name='样品进度')),
                ('sample_diwenzhuangtai', models.IntegerField(choices=[(0, '不合格'), (1, '合格')], default=0, verbose_name='低温介质到达时状态')),
                ('color_code', models.CharField(default='', max_length=6)),
                ('color_code1', models.CharField(default='', max_length=6)),
                ('man_to_upload', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='上传文件人', to=settings.AUTH_USER_MODEL, verbose_name='公司上传者')),
                ('saler', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='销售联系人', to='teacher.Employee', verbose_name='销售代表')),
                ('sample_checker', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='物流接收人', to=settings.AUTH_USER_MODEL, verbose_name='样品核对人')),
                ('sample_receiver', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='样品接收人', to=settings.AUTH_USER_MODEL, verbose_name='样品接收人')),
                ('transform_contact', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='物流联系人', to='teacher.Employee', verbose_name='物流联系人')),
            ],
            options={
                'verbose_name': '样品信息',
                'verbose_name_plural': '样品信息',
            },
        ),
        migrations.AddField(
            model_name='sampleinfo',
            name='sampleinfoform',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='teacher.SampleInfoForm', verbose_name='对应样品概要编号'),
        ),
    ]
