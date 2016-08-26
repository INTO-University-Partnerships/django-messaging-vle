from django.contrib.auth import get_user_model
from django.test import TestCase

from vle.models import CourseKVStore, GroupKVStore, CourseMember, GroupMember
from vle.sync import _sync_course_kv_store, _sync_group_kv_store, _sync_course_member, _sync_group_member


class FullSyncTestCase(TestCase):

    def setUp(self):
        self.users = {}
        for first_name in [u'Cersei', u'Jaime', u'Tyrion', u'Tywin']:
            u = get_user_model().objects.create_user(
                username='%s.lannister' % first_name.lower(),
                email='%s.lannister@into.uk.com' % first_name.lower(),
                first_name=first_name,
                last_name='Lannister',
                password='Wibble123!'
            )
            self.users[first_name] = u

    def test_sync_course_kv_store(self):
        """
        001 should be updated
        002 should be created
        003 shouldn't need changing
        004 should be deleted
        """

        # seed the database
        CourseKVStore.objects.create(vle_course_id='001', name='How to')
        CourseKVStore.objects.create(vle_course_id='003', name='How to train your dragon')
        CourseKVStore.objects.create(vle_course_id='004', name='How to')
        CourseMember.objects.create(user=self.users['Cersei'], vle_course_id='003')
        GroupKVStore.objects.create(vle_course_id='003', vle_group_id='003a', name='Doomed')
        GroupMember.objects.create(user=self.users['Cersei'], vle_course_id='003', vle_group_id='003a')
        CourseMember.objects.create(user=self.users['Cersei'], vle_course_id='004')
        GroupKVStore.objects.create(vle_course_id='004', vle_group_id='004a', name='Doomed')
        GroupMember.objects.create(user=self.users['Cersei'], vle_course_id='004', vle_group_id='004a')

        # synchronize the data
        course_kv_store = [
            {
                u'vle_course_id': '001',
                u'name': 'How to win the Game of Thrones',
            },
            {
                u'vle_course_id': '002',
                u'name': 'How to defend the wall',
            },
            {
                u'vle_course_id': '003',
                u'name': 'How to train your dragon',
            },
        ]
        _sync_course_kv_store(course_kv_store)

        # expectations
        self.assertEqual(1, CourseKVStore.objects.filter(vle_course_id='001', name='How to win the Game of Thrones').count())
        self.assertEqual(1, CourseKVStore.objects.filter(vle_course_id='002', name='How to defend the wall').count())
        self.assertEqual(1, CourseKVStore.objects.filter(vle_course_id='003', name='How to train your dragon').count())
        self.assertEqual(0, CourseKVStore.objects.filter(vle_course_id='004').count())
        self.assertEqual(3, CourseKVStore.objects.all().count())
        self.assertEqual(1, CourseMember.objects.filter(user=self.users['Cersei'], vle_course_id='003').count())
        self.assertEqual(1, GroupMember.objects.filter(user=self.users['Cersei'], vle_course_id='003', vle_group_id='003a').count())
        self.assertEqual(0, CourseMember.objects.filter(user=self.users['Cersei'], vle_course_id='004').count())
        self.assertEqual(0, GroupMember.objects.filter(user=self.users['Cersei'], vle_course_id='004', vle_group_id='004a').count())
        self.assertEqual(1, CourseMember.objects.all().count())
        self.assertEqual(1, GroupMember.objects.all().count())

    def test_sync_group_kv_store(self):
        """
        001a should be updated
        001b should be created
        001c shouldn't need changing
        001d should be deleted
        """

        # seed the database
        GroupKVStore.objects.create(vle_course_id='001', vle_group_id='001a', name='Overwrite me')
        GroupKVStore.objects.create(vle_course_id='001', vle_group_id='001c', name='Group 001c')
        GroupKVStore.objects.create(vle_course_id='001', vle_group_id='001d', name='Group 001d')
        GroupMember.objects.create(user=self.users['Cersei'], vle_course_id='001', vle_group_id='001a')
        GroupMember.objects.create(user=self.users['Cersei'], vle_course_id='001', vle_group_id='001c')
        GroupMember.objects.create(user=self.users['Cersei'], vle_course_id='001', vle_group_id='001d')

        # synchronize the data
        group_kv_store = [
            {
                u'vle_course_id': '001',
                u'vle_group_id': '001a',
                u'name': 'Group 001a',
            },
            {
                u'vle_course_id': '001',
                u'vle_group_id': '001b',
                u'name': 'Group 001b',
            },
            {
                u'vle_course_id': '001',
                u'vle_group_id': '001c',
                u'name': 'Group 001c',
            },
        ]
        _sync_group_kv_store(group_kv_store)

        # expectations
        self.assertEqual(1, GroupKVStore.objects.filter(vle_course_id='001', vle_group_id='001a', name='Group 001a').count())
        self.assertEqual(1, GroupKVStore.objects.filter(vle_course_id='001', vle_group_id='001b', name='Group 001b').count())
        self.assertEqual(1, GroupKVStore.objects.filter(vle_course_id='001', vle_group_id='001c', name='Group 001c').count())
        self.assertEqual(0, GroupKVStore.objects.filter(vle_course_id='001', vle_group_id='001d').count())
        self.assertEqual(3, GroupKVStore.objects.all().count())
        self.assertEqual(1, GroupMember.objects.filter(user=self.users['Cersei'], vle_course_id='001', vle_group_id='001a').count())
        self.assertEqual(1, GroupMember.objects.filter(user=self.users['Cersei'], vle_course_id='001', vle_group_id='001c').count())
        self.assertEqual(0, GroupMember.objects.filter(user=self.users['Cersei'], vle_course_id='001', vle_group_id='001d').count())
        self.assertEqual(2, GroupMember.objects.all().count())

    def test_sync_course_member(self):
        # seed the database
        CourseMember.objects.create(user=self.users['Cersei'], vle_course_id='001')
        CourseMember.objects.create(user=self.users['Tyrion'], vle_course_id='001', is_tutor=True)
        CourseMember.objects.create(user=self.users['Tywin'], vle_course_id='001')

        # synchronize the data
        course_member = [
            {
                u'username': 'cersei.lannister',
                u'vle_course_id': '001',
                u'is_tutor': True,
            },
            {
                u'username': 'tyrion.lannister',
                u'vle_course_id': '001',
                u'is_tutor': False,
            },
            {
                u'username': 'jaime.lannister',
                u'vle_course_id': '001',
                u'is_tutor': False,
            },
            {
                u'username': 'unknown.user',
                u'vle_course_id': '001',
                u'is_tutor': False,
            },
        ]
        _sync_course_member(course_member)

        # expectations
        self.assertEqual(1, CourseMember.objects.filter(user=self.users['Cersei'], vle_course_id='001', is_tutor=True).count())
        self.assertEqual(1, CourseMember.objects.filter(user=self.users['Tyrion'], vle_course_id='001', is_tutor=False).count())
        self.assertEqual(0, CourseMember.objects.filter(user=self.users['Tywin'], vle_course_id='001').count())
        self.assertEqual(1, CourseMember.objects.filter(user=self.users['Jaime'], vle_course_id='001', is_tutor=False).count())
        self.assertEqual(3, CourseMember.objects.all().count())

    def test_sync_group_member(self):
        # seed the database
        GroupMember.objects.create(user=self.users['Cersei'], vle_course_id='001', vle_group_id='001a')
        GroupMember.objects.create(user=self.users['Tyrion'], vle_course_id='001', vle_group_id='001a')
        GroupMember.objects.create(user=self.users['Tywin'], vle_course_id='001', vle_group_id='001a')

        # synchronize the data
        group_member = [
            {
                u'username': 'cersei.lannister',
                u'vle_course_id': '001',
                u'vle_group_id': '001a',
            },
            {
                u'username': 'tyrion.lannister',
                u'vle_course_id': '001',
                u'vle_group_id': '001a',
            },
            {
                u'username': 'jaime.lannister',
                u'vle_course_id': '001',
                u'vle_group_id': '001a',
            },
            {
                u'username': 'unknown.user',
                u'vle_course_id': '001',
                u'vle_group_id': '001a',
            },
        ]
        _sync_group_member(group_member)

        # expectations
        self.assertEqual(1, GroupMember.objects.filter(user=self.users['Cersei'], vle_course_id='001', vle_group_id='001a').count())
        self.assertEqual(1, GroupMember.objects.filter(user=self.users['Tyrion'], vle_course_id='001', vle_group_id='001a').count())
        self.assertEqual(0, GroupMember.objects.filter(user=self.users['Tywin'], vle_course_id='001', vle_group_id='001a').count())
        self.assertEqual(1, GroupMember.objects.filter(user=self.users['Jaime'], vle_course_id='001', vle_group_id='001a').count())
        self.assertEqual(3, GroupMember.objects.all().count())
