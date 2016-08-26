import json

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.http.response import HttpResponse, HttpResponseRedirect
from django.utils.encoding import force_str
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import CourseKVStore, CourseMember, GroupKVStore, GroupMember
from .decorators import basic_auth
from .sync import full_sync


@staff_member_required
def full_sync_view(request):
    messages.add_message(request, messages.INFO, full_sync())
    return HttpResponseRedirect(reverse('admin:app_list', args=('vle',)))


@csrf_exempt  # has to be the first decorator, apparently, or it doesn't work
@basic_auth(settings.VLE_SYNC_BASIC_AUTH)
@require_http_methods(['POST'])
def create_course(request):
    """
    create a new CourseKVStore
    """

    # get the data from the request
    data = json.loads(force_str(request.body))
    vle_course_id = data.get('vle_course_id', '')
    name = data.get('name', '')

    # make sure both fields were given
    if not vle_course_id or not name:
        return _error400(_('Must specify vle_course_id and name'))

    # check CourseKVStore doesn't already exist
    if CourseKVStore.objects.filter(vle_course_id=vle_course_id).exists():
        return _error400(_('Course with given vle_course_id already exists'))

    # create CourseKVStore
    CourseKVStore.objects.create(vle_course_id=vle_course_id, name=name)

    # return JSON response
    return _success200(_('Course created successfully!'))


@csrf_exempt
@basic_auth(settings.VLE_SYNC_BASIC_AUTH)
@require_http_methods(['POST'])
def update_course(request):
    """
    update a CourseKVStore (and all related models matching its vle_course_id)
    its vle_course_id or name may change, hence old_vle_course_id is needed to identify it
    """

    # get the data from the request
    data = json.loads(force_str(request.body))
    old_vle_course_id = data.get('old_vle_course_id', '')
    vle_course_id = data.get('vle_course_id', '')
    name = data.get('name', '')

    # make sure all fields were given
    if not old_vle_course_id or not vle_course_id or not name:
        return _error400(_('Must specify old_vle_course_id, vle_course_id, name'))

    # check CourseKVStore given by old_vle_course_id actually exists
    if not CourseKVStore.objects.filter(vle_course_id=old_vle_course_id).exists():
        return _error400(_('Course with given old_vle_course_id does not exist'))

    # update course
    course = CourseKVStore.objects.get(vle_course_id=old_vle_course_id)
    course.vle_course_id = vle_course_id
    course.name = name
    course.save()

    # update all 3 related models
    CourseMember.objects.filter(vle_course_id=old_vle_course_id).update(vle_course_id=vle_course_id)
    GroupKVStore.objects.filter(vle_course_id=old_vle_course_id).update(vle_course_id=vle_course_id)
    GroupMember.objects.filter(vle_course_id=old_vle_course_id).update(vle_course_id=vle_course_id)

    # return JSON response
    return _success200(_('Course updated successfully!'))


@csrf_exempt
@basic_auth(settings.VLE_SYNC_BASIC_AUTH)
@require_http_methods(['POST'])
def delete_course(request):
    """
    delete an existing CourseKVStore (and all related models matching its vle_course_id)
    """

    # get the data from the request
    data = json.loads(force_str(request.body))
    vle_course_id = data.get('vle_course_id', '')

    # make sure vle_course_id was given
    if not vle_course_id:
        return _error400(_('Must specify vle_course_id'))

    # check CourseKVStore given by vle_course_id actually exists
    if not CourseKVStore.objects.filter(vle_course_id=vle_course_id).exists():
        return _error400(_('Course with given vle_course_id does not exist'))

    # delete course
    CourseKVStore.objects.get(vle_course_id=vle_course_id).delete()
    CourseMember.objects.filter(vle_course_id=vle_course_id).delete()
    GroupKVStore.objects.filter(vle_course_id=vle_course_id).delete()
    GroupMember.objects.filter(vle_course_id=vle_course_id).delete()

    # return JSON response
    return _success200(_('Course deleted successfully!'))


@csrf_exempt
@basic_auth(settings.VLE_SYNC_BASIC_AUTH)
@require_http_methods(['POST'])
def add_course_members(request):
    """
    add new CourseMembers
    """

    # get the data from the request
    data = json.loads(force_str(request.body))
    vle_course_id = data.get('vle_course_id', '')
    usernames = data.get('usernames', [])

    # make sure vle_course_id and usernames were given
    if not vle_course_id or not usernames:
        return _error400(_('Must specify vle_course_id and usernames'))

    # check CourseKVStore given by vle_course_id actually exists
    if not CourseKVStore.objects.filter(vle_course_id=vle_course_id).exists():
        return _error400(_('Course with given vle_course_id does not exist'))

    # make each user a member
    for username in usernames:
        try:
            user = get_user_model().objects.get(username=username)
            if not CourseMember.objects.filter(vle_course_id=vle_course_id, user=user).exists():
                CourseMember.objects.create(vle_course_id=vle_course_id, user=user)
        except get_user_model().DoesNotExist:
            pass

    # return JSON response
    return _success200(_('Course members added successfully!'))


@csrf_exempt
@basic_auth(settings.VLE_SYNC_BASIC_AUTH)
@require_http_methods(['POST'])
def remove_course_members(request):
    """
    remove existing CourseMembers
    """

    # get the data from the request
    data = json.loads(force_str(request.body))
    vle_course_id = data.get('vle_course_id', '')
    usernames = data.get('usernames', [])

    # make sure vle_course_id and usernames were given
    if not vle_course_id or not usernames:
        return _error400(_('Must specify vle_course_id and usernames'))

    # check CourseKVStore given by vle_course_id actually exists
    if not CourseKVStore.objects.filter(vle_course_id=vle_course_id).exists():
        return _error400(_('Course with given vle_course_id does not exist'))

    # remove each user as a member
    for username in usernames:
        try:
            user = get_user_model().objects.get(username=username)
            if CourseMember.objects.filter(vle_course_id=vle_course_id, user=user).exists():
                CourseMember.objects.filter(vle_course_id=vle_course_id, user=user).delete()
            if GroupMember.objects.filter(vle_course_id=vle_course_id, user=user).exists():
                GroupMember.objects.filter(vle_course_id=vle_course_id, user=user).delete()
        except get_user_model().DoesNotExist:
            pass

    # return JSON response
    return _success200(_('Course members removed successfully!'))


@csrf_exempt
@basic_auth(settings.VLE_SYNC_BASIC_AUTH)
@require_http_methods(['POST'])
def add_tutor(request):
    """
    make the given user a tutor of the given course
    """

    # get the data from the request
    data = json.loads(force_str(request.body))
    vle_course_id = data.get('vle_course_id', '')
    username = data.get('username', '')

    # make sure vle_course_id and usernames were given
    if not vle_course_id or not username:
        return _error400(_('Must specify vle_course_id and username'))

    # make sure the user exists
    try:
        user = get_user_model().objects.get(username=username)
    except get_user_model().DoesNotExist:
        return _error400(_('User does not exist'))

    # make sure the user is a course member
    if not CourseMember.objects.filter(vle_course_id=vle_course_id, user=user).exists():
        return _error400(_('User is not a course member'))

    # make the user a tutor
    cm = CourseMember.objects.get(vle_course_id=vle_course_id, user=user)
    cm.is_tutor = True
    cm.save()

    # return JSON response
    return _success200(_('Tutor added successfully!'))


@csrf_exempt
@basic_auth(settings.VLE_SYNC_BASIC_AUTH)
@require_http_methods(['POST'])
def remove_tutor(request):
    """
    remove the given user as a tutor of the given course
    """

    # get the data from the request
    data = json.loads(force_str(request.body))
    vle_course_id = data.get('vle_course_id', '')
    username = data.get('username', '')

    # make sure vle_course_id and usernames were given
    if not vle_course_id or not username:
        return _error400(_('Must specify vle_course_id and username'))

    # make sure the user exists
    try:
        user = get_user_model().objects.get(username=username)
    except get_user_model().DoesNotExist:
        return _error400(_('User does not exist'))

    # make sure the user is a course member
    if not CourseMember.objects.filter(vle_course_id=vle_course_id, user=user).exists():
        return _error400(_('User is not a course member'))

    # remove the user as a tutor
    cm = CourseMember.objects.get(vle_course_id=vle_course_id, user=user)
    cm.is_tutor = False
    cm.save()

    # return JSON response
    return _success200(_('Tutor removed successfully!'))


@csrf_exempt
@basic_auth(settings.VLE_SYNC_BASIC_AUTH)
@require_http_methods(['POST'])
def create_group(request):
    """
    create a new GroupKVStore
    """

    # get the data from the request
    data = json.loads(force_str(request.body))
    vle_course_id = data.get('vle_course_id', '')
    vle_group_id = data.get('vle_group_id', '')
    name = data.get('name', '')

    # make sure all fields were given
    if not vle_course_id or not vle_group_id or not name:
        return _error400(_('Must specify vle_course_id, vle_group_id, name'))

    # check CourseKVStore exists
    if not CourseKVStore.objects.filter(vle_course_id=vle_course_id).exists():
        return _error400(_('Course with given vle_course_id does not exist'))

    # check GroupKVStore doesn't already exist
    if GroupKVStore.objects.filter(vle_course_id=vle_course_id, vle_group_id=vle_group_id).exists():
        return _error400(_('Group with given vle_course_id and vle_group_id already exists'))

    # create CourseKVStore
    GroupKVStore.objects.create(vle_course_id=vle_course_id, vle_group_id=vle_group_id, name=name)

    # return JSON response
    return _success200(_('Group created successfully!'))


@csrf_exempt
@basic_auth(settings.VLE_SYNC_BASIC_AUTH)
@require_http_methods(['POST'])
def update_group(request):
    """
    update a GroupKVStore (and related model GroupMember matching its vle_course_id and vle_group_id)
    its vle_group_id or name may change, hence old_vle_group_id is needed to identify it
    (its vle_course_id cannot change as groups cannot be reparented in the VLE)
    """

    # get the data from the request
    data = json.loads(force_str(request.body))
    vle_course_id = data.get('vle_course_id', '')
    old_vle_group_id = data.get('old_vle_group_id', '')
    vle_group_id = data.get('vle_group_id', '')
    name = data.get('name', '')

    # make sure all fields were given
    if not vle_course_id or not old_vle_group_id or not vle_group_id or not name:
        return _error400(_('Must specify vle_course_id, old_vle_group_id, vle_group_id, name'))

    # check GroupKVStore given by vle_course_id and old_vle_group_id actually exists
    if not GroupKVStore.objects.filter(vle_course_id=vle_course_id, vle_group_id=old_vle_group_id).exists():
        return _error400(_('Group with given vle_course_id and old_vle_group_id does not exist'))

    # update group
    group = GroupKVStore.objects.get(vle_course_id=vle_course_id, vle_group_id=old_vle_group_id)
    group.vle_group_id = vle_group_id
    group.name = name
    group.save()

    # update related model
    GroupMember.objects.filter(vle_course_id=vle_course_id, vle_group_id=old_vle_group_id).update(vle_group_id=vle_group_id)

    # return JSON response
    return _success200(_('Group updated successfully!'))


@csrf_exempt
@basic_auth(settings.VLE_SYNC_BASIC_AUTH)
@require_http_methods(['POST'])
def delete_group(request):
    """
    delete an existing GroupKVStore (and GroupMember related model matching its vle_course_id and vle_group_id)
    """

    # get the data from the request
    data = json.loads(force_str(request.body))
    vle_course_id = data.get('vle_course_id', '')
    vle_group_id = data.get('vle_group_id', '')

    # make sure vle_course_id and vle_group_id were given
    if not vle_course_id or not vle_group_id:
        return _error400(_('Must specify vle_course_id and vle_group_id'))

    # check GroupKVStore given by vle_course_id and vle_group_id actually exists
    if not GroupKVStore.objects.filter(vle_course_id=vle_course_id, vle_group_id=vle_group_id).exists():
        return _error400(_('Group with given vle_course_id and vle_group_id does not exist'))

    # delete group
    GroupKVStore.objects.filter(vle_course_id=vle_course_id, vle_group_id=vle_group_id).delete()
    GroupMember.objects.filter(vle_course_id=vle_course_id, vle_group_id=vle_group_id).delete()

    # return JSON response
    return _success200(_('Group deleted successfully!'))


@csrf_exempt
@basic_auth(settings.VLE_SYNC_BASIC_AUTH)
@require_http_methods(['POST'])
def add_group_members(request):
    """
    add new GroupMembers
    """

    # get the data from the request
    data = json.loads(force_str(request.body))
    vle_course_id = data.get('vle_course_id', '')
    vle_group_id = data.get('vle_group_id', '')
    usernames = data.get('usernames', [])

    # make sure vle_course_id, vle_group_id and usernames were given
    if not vle_course_id or not vle_group_id or not usernames:
        return _error400(_('Must specify vle_course_id, vle_group_id, usernames'))

    # check CourseKVStore given by vle_course_id actually exists
    if not CourseKVStore.objects.filter(vle_course_id=vle_course_id).exists():
        return _error400(_('Course with given vle_course_id does not exist'))

    # check GroupKVStore given by vle_group_id actually exists
    if not GroupKVStore.objects.filter(vle_course_id=vle_course_id, vle_group_id=vle_group_id).exists():
        return _error400(_('Group with given vle_course_id and vle_group_id does not exist'))

    # make each user a member
    for username in usernames:
        try:
            user = get_user_model().objects.get(username=username)
            course_member = CourseMember.objects.filter(vle_course_id=vle_course_id, user=user).exists()
            group_member = GroupMember.objects.filter(vle_course_id=vle_course_id, vle_group_id=vle_group_id, user=user).exists()
            if course_member and not group_member:
                GroupMember.objects.create(vle_course_id=vle_course_id, vle_group_id=vle_group_id, user=user)
        except get_user_model().DoesNotExist:
            pass

    # return JSON response
    return _success200(_('Group members added successfully!'))


@csrf_exempt
@basic_auth(settings.VLE_SYNC_BASIC_AUTH)
@require_http_methods(['POST'])
def remove_group_members(request):
    """
    remove existing GroupMembers
    """

    # get the data from the request
    data = json.loads(force_str(request.body))
    vle_course_id = data.get('vle_course_id', '')
    vle_group_id = data.get('vle_group_id', '')
    usernames = data.get('usernames', [])

    # make sure vle_course_id and vle_group_id and usernames were given
    if not vle_course_id or not vle_group_id or not usernames:
        return _error400(_('Must specify vle_course_id, vle_group_id, usernames'))

    # check CourseKVStore given by vle_course_id actually exists
    if not CourseKVStore.objects.filter(vle_course_id=vle_course_id).exists():
        return _error400(_('Course with given vle_course_id does not exist'))

    # check GroupKVStore given by vle_group_id actually exists
    if not GroupKVStore.objects.filter(vle_course_id=vle_course_id, vle_group_id=vle_group_id).exists():
        return _error400(_('Group with given vle_course_id and vle_group_id does not exist'))

    # remove each user as a member
    for username in usernames:
        try:
            user = get_user_model().objects.get(username=username)
            if GroupMember.objects.filter(vle_course_id=vle_course_id, vle_group_id=vle_group_id, user=user).exists():
                GroupMember.objects.filter(vle_course_id=vle_course_id, vle_group_id=vle_group_id, user=user).delete()
        except get_user_model().DoesNotExist:
            pass

    # return JSON response
    return _success200(_('Group members removed successfully!'))


def _error400(msg):
    """
    return an http 400 with a given message
    """
    return HttpResponse(json.dumps({
        'errorMessage': msg
    }), content_type='application/json', status=400)


def _success200(msg):
    """
    return an http 200 with a given message
    """
    return HttpResponse(json.dumps({
        'successMessage': msg
    }), content_type='application/json', status=200)
