# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def create_centos_repos(apps, schema_editor):

    CentOSRepo = apps.get_model('scls', 'CentOSRepo')

    for version in [6, 7]:
        for prefix in ['rh', 'sclo']:
            repo = CentOSRepo()
            repo.arch = 'x86_64'
            repo.version = version
            repo.prefix = prefix
            repo.release_package = 'centos-release-scl'
            if prefix == 'rh':
                repo.release_package += '-rh'
            repo.save()


class Migration(migrations.Migration):

    dependencies = [
        ('scls', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CentOSRepo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('version', models.CharField(verbose_name='CentOS version', max_length=20)),
                ('arch', models.CharField(verbose_name='Architecture', max_length=20)),
                ('prefix', models.CharField(verbose_name='Prefix', max_length=20)),
                ('release_package', models.CharField(verbose_name='Release package name', max_length=100)),
                ('last_modified', models.DateTimeField(verbose_name='Last modified', editable=False, null=True)),
                ('last_synced', models.DateTimeField(verbose_name='Last synced', editable=False, null=True)),
            ],
            options={
                'verbose_name': 'CentOS repo',
                'ordering': ('version', 'arch', 'prefix'),
                'verbose_name_plural': 'CentOS repos',
            },
        ),
        migrations.AlterField(
            model_name='softwarecollection',
            name='coprs',
            field=models.ManyToManyField(to='scls.Copr', verbose_name='Copr projects', blank=True),
        ),
        migrations.AlterUniqueTogether(
            name='centosrepo',
            unique_together=set([('version', 'arch', 'prefix')]),
        ),
        migrations.AddField(
            model_name='softwarecollection',
            name='centos_repos',
            field=models.ManyToManyField(to='scls.CentOSRepo', verbose_name='CentOS repos', blank=True),
        ),
        migrations.RunPython(create_centos_repos),
    ]
