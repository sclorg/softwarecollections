# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."
        # Note: Don't use "from appname.models import ModelName". 
        # Use orm.ModelName to refer to models in this application,
        # and orm['appname.ModelName'] for models in other applications.

        for scl in orm.SoftwareCollection.objects.all():
            # get or create Copr instance
            try:
                copr = orm.Copr.objects.get(username=scl.copr_username, name=scl.copr_name)
            except:
                copr = orm.Copr(username=scl.copr_username, name=scl.copr_name)
                copr.save()
            # link scl with copr
            scl.coprs = [copr]
            # delete disabled repos
            # (they need to be deleted one by one for Repo.delete to be called)
            for repo in scl.repos.filter(enabled=False):
                repo.delete()
            scl.repos.update(copr=copr)

            # move repo dirs and create symlinks
            import os
            from django.conf import settings
            for repo in scl.repos.all():
                try:
                    repo_id = '-'.join([copr.username, copr.name, repo.name])
                    os.rename(
                        os.path.join(settings.REPOS_ROOT, scl.slug, repo.name),
                        os.path.join(settings.REPOS_ROOT, scl.slug, repo_id)
                    )
                    os.symlink(repo_id, os.path.join(settings.REPOS_ROOT, scl.slug, repo.name))
                except FileNotFoundError:
                    pass


    def backwards(self, orm):
        "Write your backwards methods here."
        for scl in orm.SoftwareCollection.objects.all():
            # pick one copr 
            copr = scl.coprs.all()[0]
            scl.copr_username = copr.username
            scl.copr_name     = copr.name
            scl.save()

    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'unique': 'True'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'symmetrical': 'False', 'to': "orm['auth.Permission']"})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'blank': 'True', 'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True', 'symmetrical': 'False', 'related_name': "'user_set'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True', 'symmetrical': 'False', 'related_name': "'user_set'"}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'unique': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'scls.copr': {
            'Meta': {'object_name': 'Copr'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'scls.repo': {
            'Meta': {'unique_together': "(('scl', 'name'),)", 'object_name': 'Repo'},
            'copr': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['scls.Copr']", 'related_name': "'repos'", 'null': 'True'}),
            'copr_url': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'download_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'scl': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'repos'", 'to': "orm['scls.SoftwareCollection']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '150'})
        },
        'scls.score': {
            'Meta': {'unique_together': "(('scl', 'user'),)", 'object_name': 'Score'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'scl': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'scores'", 'to': "orm['scls.SoftwareCollection']"}),
            'score': ('django.db.models.fields.SmallIntegerField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'scls.softwarecollection': {
            'Meta': {'unique_together': "(('maintainer', 'name'),)", 'object_name': 'SoftwareCollection'},
            'approved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'auto_sync': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'collaborators': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'blank': 'True', 'symmetrical': 'False', 'related_name': "'softwarecollection_set'"}),
            'copr_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'copr_username': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'coprs': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['scls.Copr']"}),
            'create_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'download_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instructions': ('django.db.models.fields.TextField', [], {}),
            'issue_tracker': ('django.db.models.fields.URLField', [], {'blank': 'True', 'default': "'https://bugzilla.redhat.com/enter_bug.cgi?product=softwarecollections.org'", 'max_length': '200'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'last_synced': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'maintainer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'maintained_softwarecollection_set'", 'to': "orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'need_sync': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'policy': ('django.db.models.fields.CharField', [], {'default': "'DEV'", 'max_length': '3'}),
            'requires': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['scls.SoftwareCollection']", 'blank': 'True', 'symmetrical': 'False', 'related_name': "'required_by'"}),
            'review_req': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'score': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True'}),
            'score_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '150'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'upstream_url': ('django.db.models.fields.URLField', [], {'blank': 'True', 'max_length': '200'})
        }
    }

    complete_apps = ['scls']
    symmetrical = True
