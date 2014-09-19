# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'SoftwareCollection.copr_username'
        db.delete_column('scls_softwarecollection', 'copr_username')

        # Deleting field 'SoftwareCollection.copr_name'
        db.delete_column('scls_softwarecollection', 'copr_name')

        # Adding field 'SoftwareCollection.has_content'
        db.add_column('scls_softwarecollection', 'has_content',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'Copr.last_modified'
        db.add_column('scls_copr', 'last_modified',
                      self.gf('django.db.models.fields.DateTimeField')(null=True),
                      keep_default=False)

        # Deleting field 'Repo.enabled'
        db.delete_column('scls_repo', 'enabled')

        # Adding field 'Repo.last_synced'
        db.add_column('scls_repo', 'last_synced',
                      self.gf('django.db.models.fields.DateTimeField')(null=True),
                      keep_default=False)

        # Adding field 'Repo.has_content'
        db.add_column('scls_repo', 'has_content',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


    def backwards(self, orm):

        # User chose to not deal with backwards NULL issues for 'SoftwareCollection.copr_username'
        raise RuntimeError("Cannot reverse this migration. 'SoftwareCollection.copr_username' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'SoftwareCollection.copr_username'
        db.add_column('scls_softwarecollection', 'copr_username',
                      self.gf('django.db.models.fields.CharField')(max_length=100),
                      keep_default=False)


        # User chose to not deal with backwards NULL issues for 'SoftwareCollection.copr_name'
        raise RuntimeError("Cannot reverse this migration. 'SoftwareCollection.copr_name' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'SoftwareCollection.copr_name'
        db.add_column('scls_softwarecollection', 'copr_name',
                      self.gf('django.db.models.fields.CharField')(max_length=200),
                      keep_default=False)

        # Deleting field 'SoftwareCollection.has_content'
        db.delete_column('scls_softwarecollection', 'has_content')

        # Deleting field 'Copr.last_modified'
        db.delete_column('scls_copr', 'last_modified')

        # Adding field 'Repo.enabled'
        db.add_column('scls_repo', 'enabled',
                      self.gf('django.db.models.fields.BooleanField')(default=True),
                      keep_default=False)

        # Deleting field 'Repo.last_synced'
        db.delete_column('scls_repo', 'last_synced')

        # Deleting field 'Repo.has_content'
        db.delete_column('scls_repo', 'has_content')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'to': "orm['auth.Permission']", 'symmetrical': 'False'})
        },
        'auth.permission': {
            'Meta': {'object_name': 'Permission', 'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)"},
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
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'to': "orm['auth.Group']", 'symmetrical': 'False', 'related_name': "'user_set'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'to': "orm['auth.Permission']", 'symmetrical': 'False', 'related_name': "'user_set'"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'db_table': "'django_content_type'", 'object_name': 'ContentType', 'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'scls.copr': {
            'Meta': {'object_name': 'Copr', 'unique_together': "(('username', 'name'),)"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'scls.repo': {
            'Meta': {'object_name': 'Repo', 'unique_together': "(('scl', 'name'),)"},
            'copr': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['scls.Copr']", 'related_name': "'repos'"}),
            'copr_url': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'download_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'has_content': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_synced': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'scl': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['scls.SoftwareCollection']", 'related_name': "'repos'"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '150'})
        },
        'scls.score': {
            'Meta': {'object_name': 'Score', 'unique_together': "(('scl', 'user'),)"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'scl': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['scls.SoftwareCollection']", 'related_name': "'scores'"}),
            'score': ('django.db.models.fields.SmallIntegerField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'scls.softwarecollection': {
            'Meta': {'object_name': 'SoftwareCollection', 'unique_together': "(('maintainer', 'name'),)"},
            'approved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'auto_sync': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'collaborators': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'to': "orm['auth.User']", 'symmetrical': 'False', 'related_name': "'softwarecollection_set'"}),
            'coprs': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['scls.Copr']", 'symmetrical': 'False'}),
            'create_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'download_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'has_content': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instructions': ('django.db.models.fields.TextField', [], {}),
            'issue_tracker': ('django.db.models.fields.URLField', [], {'blank': 'True', 'max_length': '200', 'default': "'https://bugzilla.redhat.com/enter_bug.cgi?product=softwarecollections.org'"}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'last_synced': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'maintainer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'related_name': "'maintained_softwarecollection_set'"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'need_sync': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'policy': ('django.db.models.fields.CharField', [], {'max_length': '3', 'default': "'DEV'"}),
            'requires': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['scls.SoftwareCollection']", 'symmetrical': 'False', 'related_name': "'required_by'"}),
            'review_req': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'score': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True'}),
            'score_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '150'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'upstream_url': ('django.db.models.fields.URLField', [], {'blank': 'True', 'max_length': '200'})
        }
    }

    complete_apps = ['scls']