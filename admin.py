from django.contrib import admin

from .models import CourseMember, GroupMember, CourseKVStore, GroupKVStore


class CourseMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'vle_course_id', 'is_tutor',)
    list_filter = ('is_tutor',)
    search_fields = ('user__first_name', 'user__last_name', 'user__username', 'user__email', 'vle_course_id',)


class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'vle_course_id', 'vle_group_id',)
    search_fields = ('user__first_name', 'user__last_name', 'user__username', 'user__email', 'vle_course_id', 'vle_group_id',)


class CourseKVStoreAdmin(admin.ModelAdmin):
    list_display = ('vle_course_id', 'name',)
    list_editable = ('name',)
    search_fields = ('vle_course_id', 'name',)


class GroupKVStoreAdmin(admin.ModelAdmin):
    list_display = ('vle_course_id', 'vle_group_id', 'name',)
    list_editable = ('name',)
    search_fields = ('vle_course_id', 'vle_group_id', 'name',)


admin.site.register(CourseMember, CourseMemberAdmin)
admin.site.register(GroupMember, GroupMemberAdmin)
admin.site.register(CourseKVStore, CourseKVStoreAdmin)
admin.site.register(GroupKVStore, GroupKVStoreAdmin)
