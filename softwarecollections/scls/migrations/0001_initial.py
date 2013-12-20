# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'SoftwareCollection'
        db.create_table('scls_softwarecollection', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=150)),
            ('name', self.gf('django.db.models.fields.SlugField')(db_index=False, max_length=100)),
            ('copr_username', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('copr_name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('instructions', self.gf('django.db.models.fields.TextField')()),
            ('policy', self.gf('django.db.models.fields.TextField')()),
            ('score', self.gf('django.db.models.fields.SmallIntegerField')(null=True)),
            ('score_count', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('download_count', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('create_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('last_sync_date', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('approved', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('approval_req', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('auto_sync', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('need_sync', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('maintainer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], related_name='maintained_softwarecollection_set')),
        ))
        db.send_create_signal('scls', ['SoftwareCollection'])

        # Adding unique constraint on 'SoftwareCollection', fields ['maintainer', 'name']
        db.create_unique('scls_softwarecollection', ['maintainer_id', 'name'])

        # Adding M2M table for field collaborators on 'SoftwareCollection'
        m2m_table_name = db.shorten_name('scls_softwarecollection_collaborators')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('softwarecollection', models.ForeignKey(orm['scls.softwarecollection'], null=False)),
            ('user', models.ForeignKey(orm['auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['softwarecollection_id', 'user_id'])

        # Adding model 'Repo'
        db.create_table('scls_repo', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('scl', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['scls.SoftwareCollection'], related_name='repos')),
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

        # Adding model 'Score'
        db.create_table('scls_score', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('scl', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['scls.SoftwareCollection'], related_name='scores')),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('score', self.gf('django.db.models.fields.SmallIntegerField')()),
        ))
        db.send_create_signal('scls', ['Score'])

        # Adding unique constraint on 'Score', fields ['scl', 'user']
        db.create_unique('scls_score', ['scl_id', 'user_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'Score', fields ['scl', 'user']
        db.delete_unique('scls_score', ['scl_id', 'user_id'])

        # Removing unique constraint on 'Repo', fields ['scl', 'name']
        db.delete_unique('scls_repo', ['scl_id', 'name'])

        # Removing unique constraint on 'SoftwareCollection', fields ['maintainer', 'name']
        db.delete_unique('scls_softwarecollection', ['maintainer_id', 'name'])

        # Deleting model 'SoftwareCollection'
        db.delete_table('scls_softwarecollection')

        # Removing M2M table for field collaborators on 'SoftwareCollection'
        db.delete_table(db.shorten_name('scls_softwarecollection_collaborators'))

        # Deleting model 'Repo'
        db.delete_table('scls_repo')

        # Deleting model 'Score'
        db.delete_table('scls_score')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True', 'symmetrical': 'False'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)", 'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'object_name': 'Permission'},
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
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True', 'related_name': "'user_set'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True', 'related_name': "'user_set'"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'db_table': "'django_content_type'", 'unique_together': "(('app_label', 'model'),)", 'ordering': "('name',)", 'object_name': 'ContentType'},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'scls.repo': {
            'Meta': {'unique_together': "(('scl', 'name'),)", 'object_name': 'Repo'},
            'auto_sync': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'copr_url': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'create_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'download_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_sync_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'need_sync': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'scl': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['scls.SoftwareCollection']", 'related_name': "'repos'"})
        },
        'scls.score': {
            'Meta': {'unique_together': "(('scl', 'user'),)", 'object_name': 'Score'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'scl': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['scls.SoftwareCollection']", 'related_name': "'scores'"}),
            'score': ('django.db.models.fields.SmallIntegerField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'scls.softwarecollection': {
            'Meta': {'unique_together': "(('maintainer', 'name'),)", 'object_name': 'SoftwareCollection'},
            'approval_req': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'approved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'auto_sync': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'collaborators': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'symmetrical': 'False', 'blank': 'True', 'related_name': "'softwarecollection_set'"}),
            'copr_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'copr_username': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'create_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'download_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instructions': ('django.db.models.fields.TextField', [], {}),
            'last_sync_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'maintainer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'related_name': "'maintained_softwarecollection_set'"}),
            'name': ('django.db.models.fields.SlugField', [], {'db_index': 'False', 'max_length': '100'}),
            'need_sync': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'policy': ('django.db.models.fields.TextField', [], {}),
            'score': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True'}),
            'score_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '150'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['scls']