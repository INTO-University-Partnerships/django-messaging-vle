from django.conf.urls import url

from .views import create_course, update_course, delete_course, add_course_members, remove_course_members
from .views import add_tutor, remove_tutor, create_group, update_group, delete_group, add_group_members, remove_group_members

urlpatterns = [
    url(r'^create/course/$', create_course, name='create_course'),
    url(r'^update/course/$', update_course, name='update_course'),
    url(r'^delete/course/$', delete_course, name='delete_course'),
    url(r'^add/course/members/$', add_course_members, name='add_course_members'),
    url(r'^remove/course/members/$', remove_course_members, name='remove_course_members'),
    url(r'^add/tutor/$', add_tutor, name='add_tutor'),
    url(r'^remove/tutor/$', remove_tutor, name='remove_tutor'),
    url(r'^create/group/$', create_group, name='create_group'),
    url(r'^update/group/$', update_group, name='update_group'),
    url(r'^delete/group/$', delete_group, name='delete_group'),
    url(r'^add/group/members/$', add_group_members, name='add_group_members'),
    url(r'^remove/group/members/$', remove_group_members, name='remove_group_members'),
]
