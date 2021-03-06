# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2018-10-16 08:42
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('lims', '0001_initial'),
        ('pm', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='sampleinfo',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pm.Project', verbose_name='项目'),
        ),
        migrations.AddField(
            model_name='qctask',
            name='sample',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lims.SampleInfo', verbose_name='样品'),
        ),
        migrations.AddField(
            model_name='qctask',
            name='staff',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='实验员'),
        ),
        migrations.AddField(
            model_name='libtask',
            name='sample',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lims.SampleInfo', verbose_name='样品'),
        ),
        migrations.AddField(
            model_name='libtask',
            name='staff',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='实验员'),
        ),
        migrations.AddField(
            model_name='exttask',
            name='sample',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lims.SampleInfo', verbose_name='样品'),
        ),
        migrations.AddField(
            model_name='exttask',
            name='staff',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='实验员'),
        ),
        migrations.AlterUniqueTogether(
            name='sampleinfo',
            unique_together=set([('project', 'name', 'receive_date')]),
        ),
    ]
