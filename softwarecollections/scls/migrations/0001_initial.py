# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django.core.validators
import re


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Copr',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('username', models.CharField(help_text='Username of Copr user (Note that the packages must be built in Copr.)', verbose_name='Copr User', max_length=100)),
                ('name', models.CharField(help_text='Name of Copr Project to import packages from', verbose_name='Copr Project', max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Repo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('slug', models.SlugField(max_length=150, editable=False)),
                ('name', models.CharField(verbose_name='Name', max_length=50)),
                ('copr_url', models.CharField(verbose_name='Copr URL', max_length=200)),
                ('download_count', models.IntegerField(editable=False, default=0)),
                ('last_synced', models.DateTimeField(verbose_name='Last synced', editable=False, null=True)),
                ('has_content', models.BooleanField(verbose_name='Has content', default=False)),
                ('copr', models.ForeignKey(related_name='repos', to='scls.Copr')),
            ],
        ),
        migrations.CreateModel(
            name='Score',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('score', models.SmallIntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)])),
            ],
        ),
        migrations.CreateModel(
            name='SoftwareCollection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('slug', models.CharField(max_length=150, db_index=True, editable=False)),
                ('name', models.CharField(help_text='Name without spaces (It will be part of the url and RPM name.)', verbose_name='Name', max_length=100, validators=[django.core.validators.RegexValidator(re.compile('^[a-zA-Z0-9][a-zA-Z0-9_.+-]*$', 32), 'Enter a valid name consisting of letters, numbers, underscores, hyphens, pluses or dots.', 'invalid')])),
                ('upstream_url', models.URLField(verbose_name='Project homepage', blank=True)),
                ('issue_tracker', models.URLField(verbose_name='Issue Tracker', default='https://bugzilla.redhat.com/enter_bug.cgi?product=softwarecollections.org', blank=True)),
                ('title', models.CharField(verbose_name='Title', max_length=200)),
                ('description', models.TextField(verbose_name='Description')),
                ('instructions', models.TextField(help_text='Leave empty to use generic instructions', verbose_name='Instructions', blank=True)),
                ('policy', models.CharField(verbose_name='Policy', max_length=3, choices=[('DEV', '<p><strong>Unpublished</strong>: Collections not listed publicly. For projects in development stages before public release or projects for personal use. </p>\n'), ('Q-D', '<p><strong>Incubator</strong>: Early-stage or experimental projects. May not be updated beyond the existing build. Not suitable for long-term use. </p>\n'), ('COM', '<p><strong>Community Project</strong>: Maintained by upstream communities of developers. The software is cared for, but the developers make no commitments to update the repositories in a timely manner. </p>\n'), ('PRO', '<p><strong>Professional project</strong>: Stable and secure release. Receives regular bug and security fixes. Ready for production deployments. </p>\n')], default='DEV')),
                ('score', models.SmallIntegerField(editable=False, null=True)),
                ('score_count', models.IntegerField(editable=False, default=0)),
                ('download_count', models.IntegerField(editable=False, default=0)),
                ('create_date', models.DateTimeField(verbose_name='Creation date', auto_now_add=True)),
                ('last_modified', models.DateTimeField(verbose_name='Last modified', editable=False, null=True)),
                ('last_synced', models.DateTimeField(verbose_name='Last synced', editable=False, null=True)),
                ('has_content', models.BooleanField(verbose_name='Has content', default=False)),
                ('approved', models.BooleanField(verbose_name='Approved', default=False)),
                ('review_req', models.BooleanField(verbose_name='Review requested', default=False)),
                ('auto_sync', models.BooleanField(help_text='Enable periodic synchronization with related Copr project', verbose_name='Auto sync', default=False)),
                ('need_sync', models.BooleanField(verbose_name='Needs sync with coprs', default=True)),
                ('collaborators', models.ManyToManyField(verbose_name='Collaborators', related_name='softwarecollection_set', to=settings.AUTH_USER_MODEL, blank=True)),
                ('coprs', models.ManyToManyField(verbose_name='Copr projects', to='scls.Copr')),
                ('maintainer', models.ForeignKey(verbose_name='Maintainer', related_name='maintained_softwarecollection_set', to=settings.AUTH_USER_MODEL)),
                ('requires', models.ManyToManyField(related_name='required_by', editable=False, to='scls.SoftwareCollection')),
            ],
        ),
        migrations.AddField(
            model_name='score',
            name='scl',
            field=models.ForeignKey(related_name='scores', to='scls.SoftwareCollection'),
        ),
        migrations.AddField(
            model_name='score',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='repo',
            name='scl',
            field=models.ForeignKey(related_name='repos', to='scls.SoftwareCollection'),
        ),
        migrations.AlterUniqueTogether(
            name='copr',
            unique_together=set([('username', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='softwarecollection',
            unique_together=set([('maintainer', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='score',
            unique_together=set([('scl', 'user')]),
        ),
        migrations.AlterUniqueTogether(
            name='repo',
            unique_together=set([('scl', 'name')]),
        ),
    ]
