# -*- coding: UTF-8 -*-

from django.contrib.auth import get_user_model
from django.test import TestCase

import pytest

from vle.models import CourseMember, GroupMember, GroupKVStore, expand_user_group_course_ids_to_user_ids


class ModelsTestCase(TestCase):

    course001 = '001'
    group001a = '001a'

    def setUp(self):
        self.users = {}
        for first_name in [u'Cersei']:
            u = get_user_model().objects.create_user(
                username='%s.lannister' % first_name.lower(),
                email='%s.lannister@into.uk.com' % first_name.lower(),
                first_name=first_name,
                last_name='Lannister',
                password='Wibble123!'
            )
            self.users[first_name] = u

    def test_course_member_instance_str(self):
        m = CourseMember.objects.create(user=self.users['Cersei'], vle_course_id=self.course001)
        self.assertEqual('"Cersei Lannister" is a member of course "%s"' % self.course001, str(m))

    def test_course_member_tutor_instance_str(self):
        m = CourseMember.objects.create(user=self.users['Cersei'], vle_course_id=self.course001, is_tutor=True)
        self.assertEqual('"Cersei Lannister" is a tutor in course "%s"' % self.course001, str(m))

    def test_group_member_instance_str(self):
        m = GroupMember.objects.create(user=self.users['Cersei'], vle_course_id=self.course001, vle_group_id=self.group001a)
        self.assertEqual('"Cersei Lannister" is a member of group "%s" (in course "%s")' % (self.group001a, self.course001), str(m))

    def test_str(self):
        cm = CourseMember.objects.create(user=self.users['Cersei'], vle_course_id=u'Mucho dinero £££')
        self.assertEqual(type(cm.__str__()), str)

        gm = GroupMember.objects.create(user=self.users['Cersei'], vle_course_id=u'Mucho dinero £££', vle_group_id=u'Mucho dinero £££')
        self.assertEqual(type(gm.__str__()), str)


class GetGroupsFilterTestCase(TestCase):

    password = 'Wibble123!'
    course001 = '001'
    course002 = '002'
    group001 = '001'
    group002 = '002'

    def setUp(self):
        # some groups
        l = [
            (self.course001, self.group001, 'Group One'),
            (self.course001, self.group002, 'Group Two'),
            (self.course002, self.group001, 'Group One'),
            (self.course002, self.group002, 'Group Two'),
        ]
        list(map(lambda p: GroupKVStore.objects.create(vle_course_id=p[0], vle_group_id=p[1], name=p[2]), l))

        # a user
        self.user = get_user_model().objects.create_user(
            username='sansa.stark',
            email='sansa.stark@into.uk.com',
            first_name='Sansa',
            last_name='Stark',
            password=self.password,
        )

        # a super user
        self.admin = get_user_model().objects.create_superuser(
            username='admin',
            email='admin@into.uk.com',
            first_name='Admin',
            last_name='User',
            password=self.password,
        )

    def test_filter(self):
        """
        ensure the list of groups is ONLY those in the list of pairs
        """
        pairs = [
            (self.course001, self.group001),
            (self.course002, self.group001),
        ]
        groups_filter = GroupMember.get_groups_filter(pairs)
        g = GroupKVStore.objects.filter(groups_filter).order_by('vle_course_id', 'vle_group_id')
        self.assertEqual(2, len(g))
        self.assertEqual(self.course001, g[0].vle_course_id)
        self.assertEqual(self.group001, g[0].vle_group_id)
        self.assertEqual(self.course002, g[1].vle_course_id)
        self.assertEqual(self.group001, g[1].vle_group_id)

    def test_exclude(self):
        """
        ensure the list of groups is those NOT in the list of pairs
        """
        pairs = [
            (self.course001, self.group001),
            (self.course002, self.group001),
        ]
        groups_filter = GroupMember.get_groups_filter(pairs)
        g = GroupKVStore.objects.exclude(groups_filter).order_by('vle_course_id', 'vle_group_id')
        self.assertEqual(2, len(g))
        self.assertEqual(self.course001, g[0].vle_course_id)
        self.assertEqual(self.group002, g[0].vle_group_id)
        self.assertEqual(self.course002, g[1].vle_course_id)
        self.assertEqual(self.group002, g[1].vle_group_id)


@pytest.mark.django_db
def test_expand_user_group_course_ids_to_user_ids():
    delimiter = '::'
    first_names = ['Cersei', 'Jaime', 'Tyrion', 'Lancel']

    # create some users
    users = {}
    for first_name in first_names:
        u = get_user_model().objects.create_user(
            username='%s.lannister' % first_name.lower(),
            email='%s.lannister@into.uk.com' % first_name.lower(),
            first_name=first_name,
            last_name='Lannister',
            password='Wibble123!'
        )
        users[first_name] = u

    # put Cersei in the course and the group
    CourseMember.objects.create(vle_course_id='001', user=users['Cersei'])
    GroupMember.objects.create(vle_course_id='001', vle_group_id='001', user=users['Cersei'])

    # put Tyrion and Lancel in the course but not the group
    CourseMember.objects.create(vle_course_id='001', user=users['Tyrion'])
    CourseMember.objects.create(vle_course_id='001', user=users['Lancel'])

    # put Jaime in the course and the group
    CourseMember.objects.create(vle_course_id='001', user=users['Jaime'])
    GroupMember.objects.create(vle_course_id='001', vle_group_id='001', user=users['Jaime'])

    # Cersei, everyone in the group, everyone in the course
    user_ids = [users['Cersei'].id]
    group_ids = [delimiter.join(['001', '001'])]
    course_ids = ['001']
    result = expand_user_group_course_ids_to_user_ids(delimiter, user_ids, group_ids, course_ids)
    assert result == list(map(lambda k: users[k].pk, first_names))
