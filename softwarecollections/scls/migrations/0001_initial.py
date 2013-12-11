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
            ('username', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('instructions', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('update_freq', self.gf('django.db.models.fields.CharField')(max_length=2)),
            ('rebase_policy', self.gf('django.db.models.fields.CharField')(max_length=2)),
            ('maturity', self.gf('django.db.models.fields.CharField')(max_length=2)),
            ('score', self.gf('django.db.models.fields.SmallIntegerField')(null=True)),
            ('need_sync', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('maintainer', self.gf('django.db.models.fields.related.ForeignKey')(related_name='maintained_softwarecollection_set', to=orm['auth.User'])),
        ))
        db.send_create_signal('scls', ['SoftwareCollection'])

        # Adding unique constraint on 'SoftwareCollection', fields ['username', 'name']
        db.create_unique('scls_softwarecollection', ['username', 'name'])

        # Adding M2M table for field collaborators on 'SoftwareCollection'
        m2m_table_name = db.shorten_name('scls_softwarecollection_collaborators')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('softwarecollection', models.ForeignKey(orm['scls.softwarecollection'], null=False)),
            ('user', models.ForeignKey(orm['auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['softwarecollection_id', 'user_id'])

        # Adding model 'Score'
        db.create_table('scls_score', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('scl', self.gf('django.db.models.fields.related.ForeignKey')(related_name='scores', to=orm['scls.SoftwareCollection'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('score', self.gf('django.db.models.fields.SmallIntegerField')()),
        ))
        db.send_create_signal('scls', ['Score'])

        # Adding unique constraint on 'Score', fields ['scl', 'user']
        db.create_unique('scls_score', ['scl_id', 'user_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'Score', fields ['scl', 'user']
        db.delete_unique('scls_score', ['scl_id', 'user_id'])

        # Removing unique constraint on 'SoftwareCollection', fields ['username', 'name']
        db.delete_unique('scls_softwarecollection', ['username', 'name'])

        # Deleting model 'SoftwareCollection'
        db.delete_table('scls_softwarecollection')

        # Removing M2M table for field collaborators on 'SoftwareCollection'
        db.delete_table(db.shorten_name('scls_softwarecollection_collaborators'))

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
            'Meta': {'object_name': 'ContentType', 'db_table': "'django_content_type'", 'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
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
            'collaborators': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'blank': 'True', 'symmetrical': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instructions': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'maintainer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'maintained_softwarecollection_set'", 'to': "orm['auth.User']"}),
            'maturity': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'need_sync': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'rebase_policy': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'score': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '150'}),
            'update_freq': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['scls']