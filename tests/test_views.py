import base64
import json

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.translation import gettext as _
from django.utils.encoding import force_str

from vle.models import CourseKVStore, CourseMember, GroupKVStore, GroupMember


def _get_auth_headers():
    joined = ':'.join([settings.VLE_SYNC_BASIC_AUTH[0], settings.VLE_SYNC_BASIC_AUTH[1]])
    b = b'Basic ' + base64.b64encode(joined.encode('utf-8'))
    return {
        'HTTP_AUTHORIZATION': force_str(b)
    }


class CreateCourseCase(TestCase):

    def setUp(self):
        self.auth_headers = _get_auth_headers()

    def test_create_course_no_vle_course_id(self):
        # make a request
        post_data = {
            'name': 'Zero Zero One',
        }
        response = self.client.post(reverse('create_course'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Must specify vle_course_id and name'), data.get('errorMessage', ''))

    def test_create_course_no_name(self):
        # make a request
        post_data = {
            'vle_course_id': '001',
        }
        response = self.client.post(reverse('create_course'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Must specify vle_course_id and name'), data.get('errorMessage', ''))

    def test_create_course_already_exists(self):
        CourseKVStore.objects.create(vle_course_id='001', name='foobar')

        # make a request
        post_data = {
            'vle_course_id': '001',
            'name': 'wibble',
        }
        response = self.client.post(reverse('create_course'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Course with given vle_course_id already exists'), data.get('errorMessage', ''))

    def test_create_course_successfully(self):
        # make a request
        post_data = {
            'vle_course_id': '001',
            'name': 'Zero Zero One',
        }
        response = self.client.post(reverse('create_course'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it was successful
        self.assertEqual(200, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Course created successfully!'), data.get('successMessage', ''))

        # check the instance
        course = CourseKVStore.objects.get(vle_course_id='001')
        self.assertEqual('Zero Zero One', course.name)


class UpdateCourseTestCase(TestCase):

    password = 'Wibble123!'

    def setUp(self):
        self.users = {}
        for first_name in [u'Cersei', u'Jaime', u'Tyrion', u'Tywin']:
            u = get_user_model().objects.create_user(
                username='%s.lannister' % first_name.lower(),
                email='%s.lannister@into.uk.com' % first_name.lower(),
                first_name=first_name,
                last_name='Lannister',
                password=self.password
            )
            self.users[first_name] = u

        self.auth_headers = _get_auth_headers()

    def test_update_course_missing_fields(self):
        # make a request
        post_data = {}
        response = self.client.post(reverse('update_course'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Must specify old_vle_course_id, vle_course_id, name'), data.get('errorMessage', ''))

    def test_update_course_does_not_exist(self):
        # make a request
        post_data = {
            'old_vle_course_id': '001',
            'vle_course_id': '002',
            'name': 'wibble',
        }
        response = self.client.post(reverse('update_course'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Course with given old_vle_course_id does not exist'), data.get('errorMessage', ''))

    def test_update_course_successfully(self):
        CourseKVStore.objects.create(vle_course_id='001', name='foobar')
        CourseMember.objects.create(user=self.users['Cersei'], vle_course_id='001')
        GroupKVStore.objects.create(vle_course_id='001', vle_group_id='001a')
        GroupMember.objects.create(user=self.users['Cersei'], vle_course_id='001', vle_group_id='001a')

        # make a request
        post_data = {
            'old_vle_course_id': '001',
            'vle_course_id': '002',
            'name': 'Zero Zero Two',
        }
        response = self.client.post(reverse('update_course'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it was successful
        self.assertEqual(200, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Course updated successfully!'), data.get('successMessage', ''))

        # check the instance
        course = CourseKVStore.objects.get(vle_course_id='002')
        self.assertEqual('Zero Zero Two', course.name)

        # check there's only one CourseKVStore
        self.assertEqual(1, CourseKVStore.objects.all().count())

        # check the related models were also updated
        self.assertEqual(1, CourseMember.objects.filter(vle_course_id='002', user=self.users['Cersei']).count())
        self.assertEqual(1, GroupKVStore.objects.filter(vle_course_id='002', vle_group_id='001a').count())
        self.assertEqual(1, GroupMember.objects.filter(vle_course_id='002', user=self.users['Cersei']).count())


class DeleteCourseTestCase(TestCase):

    password = 'Wibble123!'

    def setUp(self):
        self.users = {}
        for first_name in [u'Cersei', u'Jaime', u'Tyrion', u'Tywin']:
            u = get_user_model().objects.create_user(
                username='%s.lannister' % first_name.lower(),
                email='%s.lannister@into.uk.com' % first_name.lower(),
                first_name=first_name,
                last_name='Lannister',
                password=self.password
            )
            self.users[first_name] = u

        self.auth_headers = _get_auth_headers()

    def test_delete_course_missing_field(self):
        # make a request
        post_data = {}
        response = self.client.post(reverse('delete_course'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Must specify vle_course_id'), data.get('errorMessage', ''))

    def test_delete_course_does_not_exist(self):
        # make a request
        post_data = {
            'vle_course_id': '001',
        }
        response = self.client.post(reverse('delete_course'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Course with given vle_course_id does not exist'), data.get('errorMessage', ''))

    def test_delete_course_successfully(self):
        # 001
        CourseKVStore.objects.create(vle_course_id='001', name='foobar')
        CourseMember.objects.create(user=self.users['Cersei'], vle_course_id='001')
        GroupKVStore.objects.create(vle_course_id='001', vle_group_id='001a')
        GroupMember.objects.create(user=self.users['Cersei'], vle_course_id='001', vle_group_id='001a')

        # 002
        CourseKVStore.objects.create(vle_course_id='002', name='foobar')
        CourseMember.objects.create(user=self.users['Cersei'], vle_course_id='002')
        GroupKVStore.objects.create(vle_course_id='002', vle_group_id='002a')
        GroupMember.objects.create(user=self.users['Cersei'], vle_course_id='002', vle_group_id='002a')

        # make a request
        post_data = {
            'vle_course_id': '001',
        }
        response = self.client.post(reverse('delete_course'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it was successful
        self.assertEqual(200, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Course deleted successfully!'), data.get('successMessage', ''))

        # check there's no CourseKVStore
        self.assertEqual(0, CourseKVStore.objects.filter(vle_course_id='001').count())

        # check the related models were also deleted
        self.assertEqual(0, CourseMember.objects.filter(vle_course_id='001', user=self.users['Cersei']).count())
        self.assertEqual(0, GroupKVStore.objects.filter(vle_course_id='001', vle_group_id='001a').count())
        self.assertEqual(0, GroupMember.objects.filter(vle_course_id='001', user=self.users['Cersei']).count())

        # check the '002' course hasn't been deleted
        self.assertEqual(1, CourseKVStore.objects.filter(vle_course_id='002').count())
        self.assertEqual(1, CourseMember.objects.filter(vle_course_id='002', user=self.users['Cersei']).count())
        self.assertEqual(1, GroupKVStore.objects.filter(vle_course_id='002', vle_group_id='002a').count())
        self.assertEqual(1, GroupMember.objects.filter(vle_course_id='002', user=self.users['Cersei']).count())


class AddCourseMembersTestCase(TestCase):

    password = 'Wibble123!'

    def setUp(self):
        self.users = {}
        for first_name in [u'Cersei', u'Jaime', u'Tyrion', u'Tywin']:
            u = get_user_model().objects.create_user(
                username='%s.lannister' % first_name.lower(),
                email='%s.lannister@into.uk.com' % first_name.lower(),
                first_name=first_name,
                last_name='Lannister',
                password=self.password
            )
            self.users[first_name] = u

        self.auth_headers = _get_auth_headers()

    def test_add_course_members_no_vle_course_id(self):
        # make a request
        post_data = {
            'usernames': [
                ('cersei.lannister', False),
            ],
        }
        response = self.client.post(reverse('add_course_members'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Must specify vle_course_id and usernames'), data.get('errorMessage', ''))

    def test_add_course_members_no_usernames(self):
        # make a request
        post_data = {
            'vle_course_id': '001',
        }
        response = self.client.post(reverse('add_course_members'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Must specify vle_course_id and usernames'), data.get('errorMessage', ''))

    def test_add_course_members_course_does_not_exist(self):
        # make a request
        post_data = {
            'vle_course_id': '001',
            'usernames': [
                self.users['Cersei'].username,
                self.users['Tywin'].username,
            ]
        }
        response = self.client.post(reverse('add_course_members'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Course with given vle_course_id does not exist'), data.get('errorMessage', ''))

    def test_add_course_members_successfully(self):
        CourseKVStore.objects.create(vle_course_id='001')
        CourseMember.objects.create(vle_course_id='001', user=self.users['Cersei'])

        # make a request
        post_data = {
            'vle_course_id': '001',
            'usernames': [
                self.users['Cersei'].username,
                self.users['Tywin'].username,
                self.users['Jaime'].username,
            ]
        }
        response = self.client.post(reverse('add_course_members'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it was successful
        self.assertEqual(200, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Course members added successfully!'), data.get('successMessage', ''))

        # check membership
        self.assertEqual(1, CourseMember.objects.filter(vle_course_id='001', is_tutor=False, user=self.users['Cersei']).count())
        self.assertEqual(1, CourseMember.objects.filter(vle_course_id='001', is_tutor=False, user=self.users['Tywin']).count())
        self.assertEqual(1, CourseMember.objects.filter(vle_course_id='001', is_tutor=False, user=self.users['Jaime']).count())

    def test_add_course_members_ignores_invalid_username(self):
        CourseKVStore.objects.create(vle_course_id='001')
        CourseMember.objects.create(vle_course_id='001', user=self.users['Cersei'])

        # make a request
        post_data = {
            'vle_course_id': '001',
            'usernames': [
                'invalid_001',
                'invalid_002',
                'invalid_003',
            ],
        }
        response = self.client.post(reverse('add_course_members'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it was successful
        self.assertEqual(200, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Course members added successfully!'), data.get('successMessage', ''))

        # check membership
        self.assertEqual(1, CourseMember.objects.filter(vle_course_id='001', user=self.users['Cersei']).count())


class RemoveCourseMembersTestCase(TestCase):

    password = 'Wibble123!'

    def setUp(self):
        self.users = {}
        for first_name in [u'Cersei', u'Jaime', u'Tyrion', u'Tywin']:
            u = get_user_model().objects.create_user(
                username='%s.lannister' % first_name.lower(),
                email='%s.lannister@into.uk.com' % first_name.lower(),
                first_name=first_name,
                last_name='Lannister',
                password=self.password
            )
            self.users[first_name] = u

        self.auth_headers = _get_auth_headers()

    def test_remove_course_members_no_vle_course_id(self):
        # make a request
        post_data = {
            'usernames': ['cersei.lannister'],
        }
        response = self.client.post(reverse('remove_course_members'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Must specify vle_course_id and usernames'), data.get('errorMessage', ''))

    def test_remove_course_members_no_usernames(self):
        # make a request
        post_data = {
            'vle_course_id': '001',
        }
        response = self.client.post(reverse('remove_course_members'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Must specify vle_course_id and usernames'), data.get('errorMessage', ''))

    def test_remove_course_members_course_does_not_exist(self):
        # make a request
        post_data = {
            'vle_course_id': '001',
            'usernames': [self.users['Cersei'].username, self.users['Tywin'].username]
        }
        response = self.client.post(reverse('remove_course_members'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Course with given vle_course_id does not exist'), data.get('errorMessage', ''))

    def test_remove_course_members_successfully(self):
        CourseKVStore.objects.create(vle_course_id='001')
        CourseKVStore.objects.create(vle_course_id='002')
        users = [self.users['Cersei'], self.users['Tywin'], self.users['Jaime'], self.users['Tyrion']]
        list(map(lambda u: CourseMember.objects.create(vle_course_id='001', user=u), users))
        list(map(lambda u: CourseMember.objects.create(vle_course_id='002', user=u), users))

        # make a request
        post_data = {
            'vle_course_id': '001',
            'usernames': [self.users['Cersei'].username, self.users['Tywin'].username, self.users['Jaime'].username]
        }
        response = self.client.post(reverse('remove_course_members'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it was successful
        self.assertEqual(200, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Course members removed successfully!'), data.get('successMessage', ''))

        # check membership
        self.assertEqual(0, CourseMember.objects.filter(vle_course_id='001', user=self.users['Cersei']).count())
        self.assertEqual(0, CourseMember.objects.filter(vle_course_id='001', user=self.users['Tywin']).count())
        self.assertEqual(0, CourseMember.objects.filter(vle_course_id='001', user=self.users['Jaime']).count())
        self.assertEqual(1, CourseMember.objects.filter(vle_course_id='001', user=self.users['Tyrion']).count())
        self.assertEqual(1, CourseMember.objects.filter(vle_course_id='002', user=self.users['Cersei']).count())
        self.assertEqual(1, CourseMember.objects.filter(vle_course_id='002', user=self.users['Tywin']).count())
        self.assertEqual(1, CourseMember.objects.filter(vle_course_id='002', user=self.users['Jaime']).count())
        self.assertEqual(1, CourseMember.objects.filter(vle_course_id='002', user=self.users['Tyrion']).count())

    def test_remove_course_members_ignores_invalid_username(self):
        CourseKVStore.objects.create(vle_course_id='001')
        CourseMember.objects.create(vle_course_id='001', user=self.users['Cersei'])

        # make a request
        post_data = {
            'vle_course_id': '001',
            'usernames': ['invalid_001', 'invalid_002', 'invalid_003'],
        }
        response = self.client.post(reverse('remove_course_members'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it was successful
        self.assertEqual(200, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Course members removed successfully!'), data.get('successMessage', ''))

        # check membership
        self.assertEqual(1, CourseMember.objects.filter(vle_course_id='001', user=self.users['Cersei']).count())

    def test_remove_course_membership_also_removes_group_membership(self):
        CourseKVStore.objects.create(vle_course_id='001')
        CourseMember.objects.create(vle_course_id='001', user=self.users['Cersei'])
        GroupKVStore.objects.create(vle_course_id='001', vle_group_id='001a')
        GroupMember.objects.create(vle_course_id='001', vle_group_id='001a', user=self.users['Cersei'])

        # make a request
        post_data = {
            'vle_course_id': '001',
            'usernames': [self.users['Cersei'].username],
        }
        response = self.client.post(reverse('remove_course_members'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it was successful
        self.assertEqual(200, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Course members removed successfully!'), data.get('successMessage', ''))

        # check membership
        self.assertEqual(0, CourseMember.objects.filter(vle_course_id='001', user=self.users['Cersei']).count())
        self.assertEqual(0, GroupMember.objects.filter(vle_course_id='001', vle_group_id='001a', user=self.users['Cersei']).count())


class AddTutorTestCase(TestCase):

    password = 'Wibble123!'

    def setUp(self):
        self.users = {}
        for first_name in [u'Cersei', u'Jaime', u'Tyrion', u'Tywin']:
            u = get_user_model().objects.create_user(
                username='%s.lannister' % first_name.lower(),
                email='%s.lannister@into.uk.com' % first_name.lower(),
                first_name=first_name,
                last_name='Lannister',
                password=self.password
            )
            self.users[first_name] = u

        self.auth_headers = _get_auth_headers()

    def test_add_tutor_no_vle_course_id(self):
        # make a request
        post_data = {
            'username': self.users['Cersei'].username,
        }
        response = self.client.post(reverse('add_tutor'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Must specify vle_course_id and username'), data.get('errorMessage', ''))

    def test_add_tutor_no_username(self):
        # make a request
        post_data = {
            'vle_course_id': '001',
        }
        response = self.client.post(reverse('add_tutor'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Must specify vle_course_id and username'), data.get('errorMessage', ''))

    def test_add_tutor_user_does_not_exist(self):
        CourseKVStore.objects.create(vle_course_id='001')

        # make a request
        post_data = {
            'vle_course_id': '001',
            'username': 'does.not.exist',
        }
        response = self.client.post(reverse('add_tutor'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('User does not exist'), data.get('errorMessage', ''))

    def test_add_tutor_not_course_member(self):
        CourseKVStore.objects.create(vle_course_id='001')

        # make a request
        post_data = {
            'vle_course_id': '001',
            'username': self.users['Cersei'].username,
        }
        response = self.client.post(reverse('add_tutor'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('User is not a course member'), data.get('errorMessage', ''))

    def test_add_tutor_successfully(self):
        CourseKVStore.objects.create(vle_course_id='001')
        CourseMember.objects.create(vle_course_id='001', user=self.users['Cersei'])

        # make a request
        post_data = {
            'vle_course_id': '001',
            'username': self.users['Cersei'].username,
        }
        response = self.client.post(reverse('add_tutor'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it was successful
        self.assertEqual(200, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Tutor added successfully!'), data.get('successMessage', ''))

        # check Cersei is now a tutor
        self.assertEqual(1, CourseMember.objects.filter(vle_course_id='001', is_tutor=True, user=self.users['Cersei']).count())


class RemoveTutorTestCase(TestCase):

    password = 'Wibble123!'

    def setUp(self):
        self.users = {}
        for first_name in [u'Cersei', u'Jaime', u'Tyrion', u'Tywin']:
            u = get_user_model().objects.create_user(
                username='%s.lannister' % first_name.lower(),
                email='%s.lannister@into.uk.com' % first_name.lower(),
                first_name=first_name,
                last_name='Lannister',
                password=self.password
            )
            self.users[first_name] = u

        self.auth_headers = _get_auth_headers()

    def test_remove_tutor_no_vle_course_id(self):
        # make a request
        post_data = {
            'username': self.users['Cersei'].username,
        }
        response = self.client.post(reverse('remove_tutor'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Must specify vle_course_id and username'), data.get('errorMessage', ''))

    def test_remove_tutor_no_username(self):
        # make a request
        post_data = {
            'vle_course_id': '001',
        }
        response = self.client.post(reverse('remove_tutor'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Must specify vle_course_id and username'), data.get('errorMessage', ''))

    def test_remove_tutor_user_does_not_exist(self):
        CourseKVStore.objects.create(vle_course_id='001')

        # make a request
        post_data = {
            'vle_course_id': '001',
            'username': 'does.not.exist',
        }
        response = self.client.post(reverse('remove_tutor'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('User does not exist'), data.get('errorMessage', ''))

    def test_remove_tutor_not_course_member(self):
        CourseKVStore.objects.create(vle_course_id='001')

        # make a request
        post_data = {
            'vle_course_id': '001',
            'username': self.users['Cersei'].username,
        }
        response = self.client.post(reverse('remove_tutor'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('User is not a course member'), data.get('errorMessage', ''))

    def test_remove_tutor_successfully(self):
        CourseKVStore.objects.create(vle_course_id='001')
        CourseMember.objects.create(vle_course_id='001', is_tutor=True, user=self.users['Cersei'])

        # make a request
        post_data = {
            'vle_course_id': '001',
            'username': self.users['Cersei'].username,
        }
        response = self.client.post(reverse('remove_tutor'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it was successful
        self.assertEqual(200, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Tutor removed successfully!'), data.get('successMessage', ''))

        # check Cersei is no longer a tutor
        self.assertEqual(0, CourseMember.objects.filter(vle_course_id='001', is_tutor=True, user=self.users['Cersei']).count())

        # check Cersei is still a course member
        self.assertEqual(1, CourseMember.objects.filter(vle_course_id='001', is_tutor=False, user=self.users['Cersei']).count())


class CreateGroupTestCase(TestCase):

    def setUp(self):
        self.auth_headers = _get_auth_headers()

    def test_create_group_no_vle_course_id(self):
        # make a request
        post_data = {
            'vle_group_id': '001a',
            'name': 'Zero Zero One',
        }
        response = self.client.post(reverse('create_group'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Must specify vle_course_id, vle_group_id, name'), data.get('errorMessage', ''))

    def test_create_group_no_vle_group_id(self):
        # make a request
        post_data = {
            'vle_course_id': '001',
            'name': 'Zero Zero One',
        }
        response = self.client.post(reverse('create_group'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Must specify vle_course_id, vle_group_id, name'), data.get('errorMessage', ''))

    def test_create_group_no_name(self):
        # make a request
        post_data = {
            'vle_course_id': '001',
            'vle_group_id': '001a',
        }
        response = self.client.post(reverse('create_group'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Must specify vle_course_id, vle_group_id, name'), data.get('errorMessage', ''))

    def test_create_group_already_exists(self):
        CourseKVStore.objects.create(vle_course_id='001')
        GroupKVStore.objects.create(vle_course_id='001', vle_group_id='001a', name='foobar')

        # make a request
        post_data = {
            'vle_course_id': '001',
            'vle_group_id': '001a',
            'name': 'irrelevant',
        }
        response = self.client.post(reverse('create_group'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Group with given vle_course_id and vle_group_id already exists'), data.get('errorMessage', ''))

    def test_create_group_without_existing_course(self):
        # make a request
        post_data = {
            'vle_course_id': '001',
            'vle_group_id': '001a',
            'name': 'Zero Zero One A',
        }
        response = self.client.post(reverse('create_group'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Course with given vle_course_id does not exist'), data.get('errorMessage', ''))

    def test_create_group_successfully(self):
        CourseKVStore.objects.create(vle_course_id='001', name='irrelevant')

        # make a request
        post_data = {
            'vle_course_id': '001',
            'vle_group_id': '001a',
            'name': 'Zero Zero One A',
        }
        response = self.client.post(reverse('create_group'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it was successful
        self.assertEqual(200, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Group created successfully!'), data.get('successMessage', ''))

        # check the instance
        group = GroupKVStore.objects.get(vle_course_id='001', vle_group_id='001a')
        self.assertEqual('Zero Zero One A', group.name)


class UpdateGroupTestCase(TestCase):

    password = 'Wibble123!'

    def setUp(self):
        self.users = {}
        for first_name in [u'Cersei', u'Jaime', u'Tyrion', u'Tywin']:
            u = get_user_model().objects.create_user(
                username='%s.lannister' % first_name.lower(),
                email='%s.lannister@into.uk.com' % first_name.lower(),
                first_name=first_name,
                last_name='Lannister',
                password=self.password
            )
            self.users[first_name] = u

        self.auth_headers = _get_auth_headers()

    def test_update_group_missing_fields(self):
        # make a request
        post_data = {}
        response = self.client.post(reverse('update_group'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Must specify vle_course_id, old_vle_group_id, vle_group_id, name'), data.get('errorMessage', ''))

    def test_update_group_missing_vle_group_id(self):
        # make a request
        post_data = {
            'vle_course_id': '001',
            'old_vle_group_id': '001a',
            'name': 'irrelevant',
        }
        response = self.client.post(reverse('update_group'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Must specify vle_course_id, old_vle_group_id, vle_group_id, name'), data.get('errorMessage', ''))

    def test_update_group_does_not_exist(self):
        # make a request
        post_data = {
            'vle_course_id': '001',
            'old_vle_group_id': '001a',
            'vle_group_id': '001b',
            'name': 'irrelevant',
        }
        response = self.client.post(reverse('update_group'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Group with given vle_course_id and old_vle_group_id does not exist'), data.get('errorMessage', ''))

    def test_update_group_successfully(self):
        CourseKVStore.objects.create(vle_course_id='001', name='foobar')
        CourseMember.objects.create(user=self.users['Cersei'], vle_course_id='001')
        GroupKVStore.objects.create(vle_course_id='001', vle_group_id='001a')
        GroupMember.objects.create(user=self.users['Cersei'], vle_course_id='001', vle_group_id='001a')

        # make a request
        post_data = {
            'vle_course_id': '001',
            'old_vle_group_id': '001a',
            'vle_group_id': '001b',
            'name': 'Zero Zero One B',
        }
        response = self.client.post(reverse('update_group'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it was successful
        self.assertEqual(200, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Group updated successfully!'), data.get('successMessage', ''))

        # check the instance
        group = GroupKVStore.objects.get(vle_course_id='001', vle_group_id='001b')
        self.assertEqual('Zero Zero One B', group.name)

        # check there's only one GroupKVStore
        self.assertEqual(1, GroupKVStore.objects.all().count())

        # check the related models were also updated
        self.assertEqual(1, GroupMember.objects.filter(vle_course_id='001', vle_group_id='001b', user=self.users['Cersei']).count())


class DeleteGroupTestCase(TestCase):

    password = 'Wibble123!'

    def setUp(self):
        self.users = {}
        for first_name in [u'Cersei', u'Jaime', u'Tyrion', u'Tywin']:
            u = get_user_model().objects.create_user(
                username='%s.lannister' % first_name.lower(),
                email='%s.lannister@into.uk.com' % first_name.lower(),
                first_name=first_name,
                last_name='Lannister',
                password=self.password
            )
            self.users[first_name] = u

        self.auth_headers = _get_auth_headers()

    def test_delete_group_missing_field(self):
        # make a request
        post_data = {}
        response = self.client.post(reverse('delete_group'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Must specify vle_course_id and vle_group_id'), data.get('errorMessage', ''))

    def test_delete_group_does_not_exist(self):
        # make a request
        post_data = {
            'vle_course_id': '001',
            'vle_group_id': '001a',
        }
        response = self.client.post(reverse('delete_group'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Group with given vle_course_id and vle_group_id does not exist'), data.get('errorMessage', ''))

    def test_delete_group_successfully(self):
        # 001
        CourseKVStore.objects.create(vle_course_id='001', name='foobar')
        CourseMember.objects.create(user=self.users['Cersei'], vle_course_id='001')
        GroupKVStore.objects.create(vle_course_id='001', vle_group_id='001a')
        GroupKVStore.objects.create(vle_course_id='001', vle_group_id='001b')
        GroupMember.objects.create(user=self.users['Cersei'], vle_course_id='001', vle_group_id='001a')
        GroupMember.objects.create(user=self.users['Cersei'], vle_course_id='001', vle_group_id='001b')

        # 002
        CourseKVStore.objects.create(vle_course_id='002', name='foobar')
        CourseMember.objects.create(user=self.users['Cersei'], vle_course_id='002')
        GroupKVStore.objects.create(vle_course_id='002', vle_group_id='002a')
        GroupMember.objects.create(user=self.users['Cersei'], vle_course_id='002', vle_group_id='002a')

        # make a request
        post_data = {
            'vle_course_id': '001',
            'vle_group_id': '001a',
        }
        response = self.client.post(reverse('delete_group'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it was successful
        self.assertEqual(200, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Group deleted successfully!'), data.get('successMessage', ''))

        # check there's no GroupKVStore
        self.assertEqual(0, GroupKVStore.objects.filter(vle_course_id='001', vle_group_id='001a').count())

        # check the other GroupKVStore hasn't been deleted
        self.assertEqual(1, GroupKVStore.objects.filter(vle_course_id='001', vle_group_id='001b').count())

        # check the related models were also deleted
        self.assertEqual(1, CourseMember.objects.filter(vle_course_id='001', user=self.users['Cersei']).count())
        self.assertEqual(0, GroupKVStore.objects.filter(vle_course_id='001', vle_group_id='001a').count())
        self.assertEqual(0, GroupMember.objects.filter(vle_course_id='001', vle_group_id='001a', user=self.users['Cersei']).count())

        # check the other GroupKVStore membership hasn't been deleted
        self.assertEqual(1, GroupMember.objects.filter(vle_course_id='001', vle_group_id='001b', user=self.users['Cersei']).count())

        # check the '002' course or its group hasn't been deleted
        self.assertEqual(1, CourseKVStore.objects.filter(vle_course_id='002').count())
        self.assertEqual(1, CourseMember.objects.filter(vle_course_id='002', user=self.users['Cersei']).count())
        self.assertEqual(1, GroupKVStore.objects.filter(vle_course_id='002', vle_group_id='002a').count())
        self.assertEqual(1, GroupMember.objects.filter(vle_course_id='002', user=self.users['Cersei']).count())


class AddGroupMembersTestCase(TestCase):

    password = 'Wibble123!'

    def setUp(self):
        self.users = {}
        for first_name in [u'Cersei', u'Jaime', u'Tyrion', u'Tywin']:
            u = get_user_model().objects.create_user(
                username='%s.lannister' % first_name.lower(),
                email='%s.lannister@into.uk.com' % first_name.lower(),
                first_name=first_name,
                last_name='Lannister',
                password=self.password
            )
            self.users[first_name] = u

        self.auth_headers = _get_auth_headers()

    def test_add_group_members_no_vle_course_id(self):
        # make a request
        post_data = {
            'vle_group_id': '001a',
            'usernames': [self.users['Cersei'].username],
        }
        response = self.client.post(reverse('add_group_members'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Must specify vle_course_id, vle_group_id, usernames'), data.get('errorMessage', ''))

    def test_add_group_members_no_vle_group_id(self):
        # make a request
        post_data = {
            'vle_course_id': '001',
            'usernames': [self.users['Cersei'].username],
        }
        response = self.client.post(reverse('add_group_members'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Must specify vle_course_id, vle_group_id, usernames'), data.get('errorMessage', ''))

    def test_add_group_members_no_usernames(self):
        # make a request
        post_data = {
            'vle_course_id': '001',
            'vle_group_id': '001a',
        }
        response = self.client.post(reverse('add_group_members'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Must specify vle_course_id, vle_group_id, usernames'), data.get('errorMessage', ''))

    def test_add_group_members_group_does_not_exist(self):
        CourseKVStore.objects.create(vle_course_id='001', name='irrelevant')

        # make a request
        post_data = {
            'vle_course_id': '001',
            'vle_group_id': '001a',
            'usernames': [self.users['Cersei'].username, self.users['Tywin'].username],
        }
        response = self.client.post(reverse('add_group_members'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Group with given vle_course_id and vle_group_id does not exist'), data.get('errorMessage', ''))

    def test_add_group_members_successfully(self):
        CourseKVStore.objects.create(vle_course_id='001')
        CourseMember.objects.create(vle_course_id='001', user=self.users['Cersei'])
        CourseMember.objects.create(vle_course_id='001', user=self.users['Tywin'])
        CourseMember.objects.create(vle_course_id='001', user=self.users['Jaime'])
        GroupKVStore.objects.create(vle_course_id='001', vle_group_id='001a')

        # make a request
        post_data = {
            'vle_course_id': '001',
            'vle_group_id': '001a',
            'usernames': [self.users['Cersei'].username, self.users['Tywin'].username, self.users['Jaime'].username],
        }
        response = self.client.post(reverse('add_group_members'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it was successful
        self.assertEqual(200, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Group members added successfully!'), data.get('successMessage', ''))

        # check membership of groups
        self.assertEqual(1, GroupMember.objects.filter(vle_course_id='001', vle_group_id='001a', user=self.users['Cersei']).count())
        self.assertEqual(1, GroupMember.objects.filter(vle_course_id='001', vle_group_id='001a', user=self.users['Tywin']).count())
        self.assertEqual(1, GroupMember.objects.filter(vle_course_id='001', vle_group_id='001a', user=self.users['Jaime']).count())

    def test_add_group_members_ignores_non_course_members(self):
        CourseKVStore.objects.create(vle_course_id='001')
        CourseMember.objects.create(vle_course_id='001', user=self.users['Tywin'])
        GroupKVStore.objects.create(vle_course_id='001', vle_group_id='001a')

        # make a request
        post_data = {
            'vle_course_id': '001',
            'vle_group_id': '001a',
            'usernames': [self.users['Cersei'].username, self.users['Tywin'].username, self.users['Jaime'].username],
        }
        response = self.client.post(reverse('add_group_members'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it was successful
        self.assertEqual(200, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Group members added successfully!'), data.get('successMessage', ''))

        # check membership of groups
        self.assertEqual(0, GroupMember.objects.filter(vle_course_id='001', vle_group_id='001a', user=self.users['Cersei']).count())
        self.assertEqual(1, GroupMember.objects.filter(vle_course_id='001', vle_group_id='001a', user=self.users['Tywin']).count())
        self.assertEqual(0, GroupMember.objects.filter(vle_course_id='001', vle_group_id='001a', user=self.users['Jaime']).count())

    def test_add_group_members_ignores_invalid_username(self):
        CourseKVStore.objects.create(vle_course_id='001')
        CourseMember.objects.create(vle_course_id='001', user=self.users['Cersei'])
        GroupKVStore.objects.create(vle_course_id='001', vle_group_id='001a')
        GroupMember.objects.create(vle_course_id='001', vle_group_id='001a', user=self.users['Cersei'])

        # make a request
        post_data = {
            'vle_course_id': '001',
            'vle_group_id': '001a',
            'usernames': ['invalid_001', 'invalid_002', 'invalid_003'],
        }
        response = self.client.post(reverse('add_group_members'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it was successful
        self.assertEqual(200, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Group members added successfully!'), data.get('successMessage', ''))

        # check membership
        self.assertEqual(1, CourseMember.objects.filter(vle_course_id='001', user=self.users['Cersei']).count())
        self.assertEqual(1, GroupMember.objects.filter(vle_course_id='001', vle_group_id='001a', user=self.users['Cersei']).count())


class RemoveGroupMembersTestCase(TestCase):

    password = 'Wibble123!'

    def setUp(self):
        self.users = {}
        for first_name in [u'Cersei', u'Jaime', u'Tyrion', u'Tywin']:
            u = get_user_model().objects.create_user(
                username='%s.lannister' % first_name.lower(),
                email='%s.lannister@into.uk.com' % first_name.lower(),
                first_name=first_name,
                last_name='Lannister',
                password=self.password
            )
            self.users[first_name] = u

        self.auth_headers = _get_auth_headers()

    def test_remove_group_members_no_vle_course_id(self):
        # make a request
        post_data = {
            'vle_group_id': '001a',
            'usernames': ['cersei.lannister'],
        }
        response = self.client.post(reverse('remove_group_members'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Must specify vle_course_id, vle_group_id, usernames'), data.get('errorMessage', ''))

    def test_remove_group_members_no_vle_group_id(self):
        CourseKVStore.objects.create(vle_course_id='001')

        # make a request
        post_data = {
            'vle_course_id': '001',
            'usernames': ['cersei.lannister'],
        }
        response = self.client.post(reverse('remove_group_members'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Must specify vle_course_id, vle_group_id, usernames'), data.get('errorMessage', ''))

    def test_remove_group_members_no_usernames(self):
        # make a request
        post_data = {
            'vle_course_id': '001',
            'vle_group_id': '001a',
        }
        response = self.client.post(reverse('remove_group_members'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Must specify vle_course_id, vle_group_id, usernames'), data.get('errorMessage', ''))

    def test_remove_group_members_course_does_not_exist(self):
        GroupKVStore.objects.create(vle_course_id='does_not_exist', vle_group_id='001a')

        # make a request
        post_data = {
            'vle_course_id': '001',
            'vle_group_id': '001a',
            'usernames': [self.users['Cersei'].username, self.users['Tywin'].username]
        }
        response = self.client.post(reverse('remove_group_members'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Course with given vle_course_id does not exist'), data.get('errorMessage', ''))

    def test_remove_group_members_group_does_not_exist(self):
        CourseKVStore.objects.create(vle_course_id='001')

        # make a request
        post_data = {
            'vle_course_id': '001',
            'vle_group_id': '001a',
            'usernames': [self.users['Cersei'].username, self.users['Tywin'].username]
        }
        response = self.client.post(reverse('remove_group_members'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it wasn't successful
        self.assertEqual(400, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Group with given vle_course_id and vle_group_id does not exist'), data.get('errorMessage', ''))

    def test_remove_group_members_successfully(self):
        CourseKVStore.objects.create(vle_course_id='001')
        GroupKVStore.objects.create(vle_course_id='001', vle_group_id='001a')
        GroupKVStore.objects.create(vle_course_id='001', vle_group_id='001b')
        CourseKVStore.objects.create(vle_course_id='002')
        GroupKVStore.objects.create(vle_course_id='002', vle_group_id='002a')
        users = [self.users['Tyrion'], self.users['Cersei'], self.users['Tywin']]
        list(map(lambda u: CourseMember.objects.create(vle_course_id='001', user=u), users))
        list(map(lambda u: CourseMember.objects.create(vle_course_id='002', user=u), users))
        list(map(lambda u: GroupMember.objects.create(vle_course_id='001', vle_group_id='001a', user=u), users))
        list(map(lambda u: GroupMember.objects.create(vle_course_id='001', vle_group_id='001b', user=u), users))
        list(map(lambda u: GroupMember.objects.create(vle_course_id='002', vle_group_id='002a', user=u), users))

        # make a request
        post_data = {
            'vle_course_id': '001',
            'vle_group_id': '001a',
            'usernames': [self.users['Cersei'].username, self.users['Tywin'].username, self.users['Tyrion'].username]
        }
        response = self.client.post(reverse('remove_group_members'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it was successful
        self.assertEqual(200, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Group members removed successfully!'), data.get('successMessage', ''))

        # check course membership (which shouldn't be effected)
        self.assertEqual(1, CourseMember.objects.filter(vle_course_id='001', user=self.users['Tyrion']).count())
        self.assertEqual(1, CourseMember.objects.filter(vle_course_id='001', user=self.users['Cersei']).count())
        self.assertEqual(1, CourseMember.objects.filter(vle_course_id='001', user=self.users['Tywin']).count())
        self.assertEqual(1, CourseMember.objects.filter(vle_course_id='002', user=self.users['Tyrion']).count())
        self.assertEqual(1, CourseMember.objects.filter(vle_course_id='002', user=self.users['Cersei']).count())
        self.assertEqual(1, CourseMember.objects.filter(vle_course_id='002', user=self.users['Tywin']).count())

        # check group membership of 001b (which shouldn't be effected)
        self.assertEqual(1, GroupMember.objects.filter(vle_course_id='001', vle_group_id='001b', user=self.users['Tyrion']).count())
        self.assertEqual(1, GroupMember.objects.filter(vle_course_id='001', vle_group_id='001b', user=self.users['Cersei']).count())
        self.assertEqual(1, GroupMember.objects.filter(vle_course_id='001', vle_group_id='001b', user=self.users['Tywin']).count())

        # check group membership of 002a (which shouldn't be effected)
        self.assertEqual(1, GroupMember.objects.filter(vle_course_id='002', vle_group_id='002a', user=self.users['Tyrion']).count())
        self.assertEqual(1, GroupMember.objects.filter(vle_course_id='002', vle_group_id='002a', user=self.users['Cersei']).count())
        self.assertEqual(1, GroupMember.objects.filter(vle_course_id='002', vle_group_id='002a', user=self.users['Tywin']).count())

        # check group membership of 001a
        self.assertEqual(0, GroupMember.objects.filter(vle_course_id='001', vle_group_id='001a', user=self.users['Tyrion']).count())
        self.assertEqual(0, GroupMember.objects.filter(vle_course_id='001', vle_group_id='001a', user=self.users['Cersei']).count())
        self.assertEqual(0, GroupMember.objects.filter(vle_course_id='001', vle_group_id='001a', user=self.users['Tywin']).count())

    def test_remove_group_members_ignores_invalid_username(self):
        CourseKVStore.objects.create(vle_course_id='001')
        GroupKVStore.objects.create(vle_course_id='001', vle_group_id='001a')
        CourseMember.objects.create(vle_course_id='001', user=self.users['Cersei'])
        GroupMember.objects.create(vle_course_id='001', vle_group_id='001a', user=self.users['Cersei'])

        # make a request
        post_data = {
            'vle_course_id': '001',
            'vle_group_id': '001a',
            'usernames': ['invalid_001', 'invalid_002', 'invalid_003'],
        }
        response = self.client.post(reverse('remove_group_members'), content_type='application/json', data=json.dumps(post_data), **self.auth_headers)

        # check it was successful
        self.assertEqual(200, response.status_code)

        # check the JSON
        data = json.loads(force_str(response.content))
        self.assertEqual(_('Group members removed successfully!'), data.get('successMessage', ''))

        # check membership
        self.assertEqual(1, CourseMember.objects.filter(vle_course_id='001', user=self.users['Cersei']).count())
        self.assertEqual(1, GroupMember.objects.filter(vle_course_id='001', vle_group_id='001a', user=self.users['Cersei']).count())
