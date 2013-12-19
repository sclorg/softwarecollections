# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from django.utils.timezone import now


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Repo'
        db.create_table('scls_repo', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('scl', self.gf('django.db.models.fields.related.ForeignKey')(related_name='repos', to=orm['scls.SoftwareCollection'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('copr_url', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('create_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('last_sync_date', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('auto_sync', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('need_sync', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('download_count', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('scls', ['Repo'])

        # Adding unique constraint on 'Repo', fields ['scl', 'name']
        db.create_unique('scls_repo', ['scl_id', 'name'])

        # Adding field 'SoftwareCollection.download_count'
        db.add_column('scls_softwarecollection', 'download_count',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)

        # Adding field 'SoftwareCollection.create_date'
        db.add_column('scls_softwarecollection', 'create_date',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True, default=now()),
                      keep_default=False)

        # Adding field 'SoftwareCollection.last_sync_date'
        db.add_column('scls_softwarecollection', 'last_sync_date',
                      self.gf('django.db.models.fields.DateTimeField')(null=True),
                      keep_default=False)

        # Adding field 'SoftwareCollection.approval_req'
        db.add_column('scls_softwarecollection', 'approval_req',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'SoftwareCollection.auto_sync'
        db.add_column('scls_softwarecollection', 'auto_sync',
                      self.gf('django.db.models.fields.BooleanField')(default=True),
                      keep_default=False)


    def backwards(self, orm):
        # Removing unique constraint on 'Repo', fields ['scl', 'name']
        db.delete_unique('scls_repo', ['scl_id', 'name'])

        # Deleting model 'Repo'
        db.delete_table('scls_repo')

        # Deleting field 'SoftwareCollection.download_count'
        db.delete_column('scls_softwarecollection', 'download_count')

        # Deleting field 'SoftwareCollection.create_date'
        db.delete_column('scls_softwarecollection', 'create_date')

        # Deleting field 'SoftwareCollection.last_sync_date'
        db.delete_column('scls_softwarecollection', 'last_sync_date')

        # Deleting field 'SoftwareCollection.approval_req'
        db.delete_column('scls_softwarecollection', 'approval_req')

        # Deleting field 'SoftwareCollection.auto_sync'
        db.delete_column('scls_softwarecollection', 'auto_sync')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True', 'symmetrical': 'False'})
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
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'user_set'", 'to': "orm['auth.Group']", 'blank': 'True', 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'user_set'", 'to': "orm['auth.Permission']", 'blank': 'True', 'symmetrical': 'False'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'db_table': "'django_content_type'", 'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType'},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'scls.repo': {
            'Meta': {'object_name': 'Repo', 'unique_together': "(('scl', 'name'),)"},
            'auto_sync': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'copr_url': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'create_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'download_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_sync_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'need_sync': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'scl': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'repos'", 'to': "orm['scls.SoftwareCollection']"})
        },
        'scls.score': {
            'Meta': {'object_name': 'Score', 'unique_together': "(('scl', 'user'),)"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'scl': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'scores'", 'to': "orm['scls.SoftwareCollection']"}),
            'score': ('django.db.models.fields.SmallIntegerField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'scls.softwarecollection': {
            'Meta': {'object_name': 'SoftwareCollection', 'unique_together': "(('username', 'name'),)"},
            'approval_req': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'approved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'auto_sync': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'collaborators': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'softwarecollection_set'", 'to': "orm['auth.User']", 'blank': 'True', 'symmetrical': 'False'}),
            'create_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'download_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instructions': ('django.db.models.fields.TextField', [], {}),
            'last_sync_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'maintainer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'maintained_softwarecollection_set'", 'to': "orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'need_sync': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'policy': ('django.db.models.fields.TextField', [], {}),
            'score': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True'}),
            'score_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '150'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['scls']
