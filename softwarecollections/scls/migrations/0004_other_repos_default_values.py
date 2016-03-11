# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scls', '0003_other_repos'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otherrepo',
            name='arch',
            field=models.CharField(default='', blank=True, verbose_name='Architecture', max_length=20),
        ),
        migrations.AlterField(
            model_name='otherrepo',
            name='command',
            field=models.TextField(default='', blank=True, verbose_name='Command'),
        ),
        migrations.AlterField(
            model_name='otherrepo',
            name='icon',
            field=models.CharField(default='', blank=True, verbose_name='Icon', choices=[('centos', 'centos'), ('epel', 'epel'), ('fedora', 'fedora'), ('rhel', 'rhel')], max_length=20),
        ),
        migrations.AlterField(
            model_name='otherrepo',
            name='version',
            field=models.CharField(default='', blank=True, verbose_name='Distribution version', max_length=20),
        ),
    ]
