from django.contrib import admin
from .models import DailyEntry, Goal, OtherTask, PrayerLog, SkillLog, StudyLog


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'goal_type', 'start_date', 'end_date', 'is_active')
    list_filter = ('category', 'goal_type', 'is_active')
    search_fields = ('title', 'user__username')


class PrayerInline(admin.TabularInline):
    model = PrayerLog
    extra = 0


class StudyInline(admin.StackedInline):
    model = StudyLog
    extra = 0


class SkillInline(admin.StackedInline):
    model = SkillLog
    extra = 0


class OtherTaskInline(admin.TabularInline):
    model = OtherTask
    extra = 0


@admin.register(DailyEntry)
class DailyEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'productivity_score', 'prayer_score', 'updated_at')
    list_filter = ('date',)
    search_fields = ('user__username', 'notes')
    inlines = [PrayerInline, StudyInline, SkillInline, OtherTaskInline]


admin.site.register(PrayerLog)
admin.site.register(StudyLog)
admin.site.register(SkillLog)
admin.site.register(OtherTask)
