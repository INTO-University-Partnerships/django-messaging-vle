from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _

import requests

from .models import CourseKVStore, GroupKVStore, CourseMember, GroupMember


def full_sync():
    # request all data requiring synchronization from Moodle
    response = requests.get(
        '%s/local/messaging/' % settings.MOODLEWWWROOT,
        auth=settings.VLE_SYNC_BASIC_AUTH
    )

    # return error message
    if response.status_code != 200:
        e = response.json()
        return e['errorMessage']

    # sync each of the four models
    d = response.json()
    _sync_course_kv_store(d['course_kv_store'])
    _sync_group_kv_store(d['group_kv_store'])
    _sync_course_member(d['course_member'])
    _sync_group_member(d['group_member'])

    return _('Full VLE synchronization completed successfully')


def _sync_course_kv_store(course_kv_store):
    # orphaned ids to delete
    to_delete = list(CourseKVStore.objects.all().values_list('vle_course_id', flat=True))

    # create or update each item
    for item in course_kv_store:
        obj, created = CourseKVStore.objects.get_or_create(vle_course_id=item['vle_course_id'])
        obj.name = item['name']
        obj.save()
        if item['vle_course_id'] in to_delete:
            to_delete.remove(item['vle_course_id'])

    # delete orphans
    if to_delete:
        CourseKVStore.objects.filter(vle_course_id__in=to_delete).delete()
        GroupKVStore.objects.filter(vle_course_id__in=to_delete).delete()
        CourseMember.objects.filter(vle_course_id__in=to_delete).delete()
        GroupMember.objects.filter(vle_course_id__in=to_delete).delete()


def _sync_group_kv_store(group_kv_store):
    # orphaned ids to delete
    to_delete = list(GroupKVStore.objects.all().values_list('vle_course_id', 'vle_group_id'))

    # create or update each item
    for item in group_kv_store:
        obj, created = GroupKVStore.objects.get_or_create(vle_course_id=item['vle_course_id'], vle_group_id=item['vle_group_id'])
        obj.name = item['name']
        obj.save()
        if (item['vle_course_id'], item['vle_group_id']) in to_delete:
            to_delete.remove((item['vle_course_id'], item['vle_group_id']))

    # delete orphans
    if to_delete:
        GroupKVStore.objects.filter(GroupMember.get_groups_filter(to_delete)).delete()
        GroupMember.objects.filter(GroupMember.get_groups_filter(to_delete)).delete()


def _sync_course_member(course_member):
    # orphaned ids to delete
    to_delete = list(CourseMember.objects.all().values_list('id', flat=True))

    # create or update each item
    for item in course_member:
        try:
            user = get_user_model().objects.get(username=item['username'])
            obj, created = CourseMember.objects.get_or_create(user=user, vle_course_id=item['vle_course_id'])
            obj.is_tutor = item['is_tutor']
            obj.save()
            if obj.pk in to_delete:
                to_delete.remove(obj.pk)
        except get_user_model().DoesNotExist:
            pass

    # delete orphans
    if to_delete:
        CourseMember.objects.filter(pk__in=to_delete).delete()


def _sync_group_member(group_member):
    # orphaned ids to delete
    to_delete = list(GroupMember.objects.all().values_list('id', flat=True))

    # create or update each item
    for item in group_member:
        try:
            user = get_user_model().objects.get(username=item['username'])
            obj, created = GroupMember.objects.get_or_create(user=user, vle_course_id=item['vle_course_id'], vle_group_id=item['vle_group_id'])
            if obj.pk in to_delete:
                to_delete.remove(obj.pk)
        except get_user_model().DoesNotExist:
            pass

    # delete orphans
    if to_delete:
        GroupMember.objects.filter(pk__in=to_delete).delete()
