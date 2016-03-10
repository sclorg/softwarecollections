# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def migrate_centos_repos(apps, schema_editor):
    CentOSRepo          = apps.get_model('scls', 'CentOSRepo')
    OtherRepo           = apps.get_model('scls', 'OtherRepo')
    SoftwareCollection  = apps.get_model('scls', 'SoftwareCollection')

    OTHER_REPOS_BY_CENTOS_REPO_ID = {}

    for centos_repo in CentOSRepo.objects.all():
        other_repo = OtherRepo()
        other_repo.name     = 'CentOS'
        other_repo.version  = centos_repo.version
        other_repo.variant  = centos_repo.prefix
        other_repo.arch     = centos_repo.arch
        other_repo.icon     = 'centos'
        other_repo.url      = 'http://mirror.centos.org/centos/{version}/sclo/{arch}/{prefix}/'.format(
            version         = centos_repo.version,
            arch            = centos_repo.arch,
            prefix          = centos_repo.prefix,
        )
        other_repo.command  = 'yum install {}'.format(centos_repo.release_package)
        other_repo.save()
        OTHER_REPOS_BY_CENTOS_REPO_ID[centos_repo.id] = other_repo

    for scl in SoftwareCollection.objects.all():
        for centos_repo in scl.centos_repos.all():
            scl.other_repos.add(OTHER_REPOS_BY_CENTOS_REPO_ID[centos_repo.id])



class Migration(migrations.Migration):

    dependencies = [
        ('scls', '0002_centos_repos'),
    ]

    operations = [
        migrations.CreateModel(
            name='OtherRepo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('name', models.CharField(max_length=20, verbose_name='Distribution name')),
                ('version', models.CharField(max_length=20, verbose_name='Distribution version')),
                ('variant', models.CharField(max_length=20, verbose_name='Variant', blank=True, default='')),
                ('arch', models.CharField(max_length=20, verbose_name='Architecture')),
                ('icon', models.CharField(max_length=20, choices=[('centos', 'centos'), ('rhel', 'rhel'), ('fedora', 'fedora'), ('epel', 'epel')], verbose_name='Icon')),
                ('url', models.CharField(max_length=200, verbose_name='URL', blank=True, default='')),
                ('command', models.TextField(verbose_name='Command')),
                ('last_modified', models.DateTimeField(null=True, editable=False, verbose_name='Last modified')),
                ('last_synced', models.DateTimeField(null=True, editable=False, verbose_name='Last synced')),
            ],
            options={
                'ordering': ('name', 'version', 'variant', 'arch'),
                'verbose_name': 'Other repo',
                'verbose_name_plural': 'Other repos',
            },
        ),
        migrations.AlterUniqueTogether(
            name='otherrepo',
            unique_together=set([('name', 'version', 'variant', 'arch')]),
        ),
        migrations.AddField(
            model_name='softwarecollection',
            name='other_repos',
            field=models.ManyToManyField(to='scls.OtherRepo', blank=True, verbose_name='Other repos'),
        ),
        migrations.RunPython(migrate_centos_repos),
        migrations.RemoveField(
            model_name='softwarecollection',
            name='centos_repos',
        ),
        migrations.DeleteModel(
            name='CentOSRepo',
        ),
    ]
