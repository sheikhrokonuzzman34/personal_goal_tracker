from django.contrib import admin

from .models import Category, DailyEntry, Goal, GoalProgress, PrayerLog


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'user__username')


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'goal_type', 'start_date', 'end_date', 'target_minutes_per_day', 'is_active')
    list_filter = ('category', 'goal_type', 'is_active')
    search_fields = ('title', 'category__name', 'user__username')


class PrayerInline(admin.TabularInline):
    model = PrayerLog
    extra = 0


class GoalProgressInline(admin.TabularInline):
    model = GoalProgress
    extra = 0


@admin.register(DailyEntry)
class DailyEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'productivity_score', 'prayer_score', 'updated_at')
    list_filter = ('date',)
    search_fields = ('user__username', 'notes')
    inlines = [PrayerInline, GoalProgressInline]


admin.site.register(PrayerLog)
admin.site.register(GoalProgress)
