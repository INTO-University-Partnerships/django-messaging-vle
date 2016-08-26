from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.six import moves, python_2_unicode_compatible


@python_2_unicode_compatible
class CourseMember(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    vle_course_id = models.CharField(max_length=100, db_index=True)
    is_tutor = models.BooleanField(default=False, db_index=True)

    def __str__(self):
        t = (
            ' '.join([self.user.first_name, self.user.last_name]),
            u'tutor in' if self.is_tutor else u'member of',
            self.vle_course_id,
        )
        return u'"%s" is a %s course "%s"' % t

    class Meta:
        unique_together = ('user', 'vle_course_id',)


@python_2_unicode_compatible
class GroupMember(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    vle_course_id = models.CharField(max_length=100, db_index=True)
    vle_group_id = models.CharField(max_length=100, db_index=True)

    def __str__(self):
        t = (
            ' '.join([self.user.first_name, self.user.last_name]),
            self.vle_group_id,
            self.vle_course_id,
        )
        return u'"%s" is a member of group "%s" (in course "%s")' % t

    @classmethod
    def get_groups_filter(cls, ids):
        """
        given a list of pairs (i.e. two-tuples) of (vle_course_id, vle_group_id), returns a groups filter
        """
        qs = [Q(vle_course_id=p[0], vle_group_id=p[1]) for p in ids]
        return moves.reduce(lambda q1, q2: q1 | q2, qs)

    class Meta:
        unique_together = ('user', 'vle_course_id', 'vle_group_id',)


@python_2_unicode_compatible
class CourseKVStore(models.Model):
    vle_course_id = models.CharField(max_length=100, db_index=True, unique=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        t = (
            self.vle_course_id,
            self.name,
        )
        return u'vle_course_id "%s" has name "%s"' % t


@python_2_unicode_compatible
class GroupKVStore(models.Model):
    vle_course_id = models.CharField(max_length=100, db_index=True)
    vle_group_id = models.CharField(max_length=100, db_index=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        t = (
            self.vle_course_id,
            self.vle_group_id,
            self.name,
        )
        return u'vle_course_id, vle_group_id "%s|%s" has name "%s"' % t

    class Meta:
        unique_together = ('vle_course_id', 'vle_group_id',)


def expand_user_group_course_ids_to_user_ids(delimiter, user_ids, group_ids, course_ids):
    """
    gets all the users in the given groups and courses
    """

    # start off with a list of user_ids
    ids = []
    ids.extend(user_ids)

    # for groups, append each user in each group
    if group_ids:
        group_ids = map(lambda x: x.split(delimiter), group_ids)
        ids.extend(GroupMember.objects.filter(GroupMember.get_groups_filter(group_ids)).values_list('user__id', flat=True))

    # for courses, append each user in each course
    if course_ids:
        ids.extend(CourseMember.objects.filter(vle_course_id__in=course_ids).values_list('user__id', flat=True))

    # return user ids
    return sorted(set(ids))
