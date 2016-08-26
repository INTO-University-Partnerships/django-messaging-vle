# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseKVStore',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('vle_course_id', models.CharField(unique=True, max_length=100, db_index=True)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CourseMember',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('vle_course_id', models.CharField(max_length=100, db_index=True)),
                ('is_tutor', models.BooleanField(default=False, db_index=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GroupKVStore',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('vle_course_id', models.CharField(max_length=100, db_index=True)),
                ('vle_group_id', models.CharField(max_length=100, db_index=True)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GroupMember',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('vle_course_id', models.CharField(max_length=100, db_index=True)),
                ('vle_group_id', models.CharField(max_length=100, db_index=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='groupmember',
            unique_together=set([('user', 'vle_course_id', 'vle_group_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='groupkvstore',
            unique_together=set([('vle_course_id', 'vle_group_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='coursemember',
            unique_together=set([('user', 'vle_course_id')]),
        ),
    ]
