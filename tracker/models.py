from datetime import timedelta

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Category(models.Model):
    """User-created dynamic category. Example: University Study, New Skill, Health."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        unique_together = ('user', 'name')
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_list')


class Goal(models.Model):
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    SIX_MONTH = 'six_month'
    YEARLY = 'yearly'

    GOAL_TYPE_CHOICES = [
        (DAILY, '24 Hours / Daily'),
        (WEEKLY, '7 Days'),
        (MONTHLY, '1 Month'),
        (SIX_MONTH, '6 Months'),
        (YEARLY, '1 Year'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='goals')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='goals')
    title = models.CharField(max_length=150)
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPE_CHOICES)
    description = models.TextField(blank=True)
    start_date = models.DateField(default=timezone.localdate)
    end_date = models.DateField(blank=True, null=True)
    target_minutes_per_day = models.PositiveIntegerField(default=15, help_text='Keep it small so daily work feels easy.')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.end_date:
            days = {
                self.DAILY: 1,
                self.WEEKLY: 7,
                self.MONTHLY: 30,
                self.SIX_MONTH: 180,
                self.YEARLY: 365,
            }.get(self.goal_type, 30)
            self.end_date = self.start_date + timedelta(days=days - 1)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('goal_list')


class DailyEntry(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='daily_entries')
    date = models.DateField(default=timezone.localdate)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'date')
        ordering = ['-date']

    def __str__(self):
        return f'{self.user} - {self.date}'

    @property
    def prayer_score(self):
        completed = self.prayers.exclude(status=PrayerLog.MISSED).count()
        return round((completed / 5) * 100)

    @property
    def productivity_score(self):
        prayer_total = 5
        prayer_done = self.prayers.exclude(status=PrayerLog.MISSED).count()

        goal_total = self.goal_progress.count()
        goal_done = self.goal_progress.filter(done=True).count()

        total = prayer_total + goal_total
        done = prayer_done + goal_done
        if total == 0:
            return 0
        return round((done / total) * 100)


class PrayerLog(models.Model):
    FAJR = 'fajr'
    DHUHR = 'dhuhr'
    ASR = 'asr'
    MAGHRIB = 'maghrib'
    ISHA = 'isha'

    PRAYER_CHOICES = [
        (FAJR, 'Fajr'),
        (DHUHR, 'Dhuhr'),
        (ASR, 'Asr'),
        (MAGHRIB, 'Maghrib'),
        (ISHA, 'Isha'),
    ]

    JAMAAT = 'jamaat'
    SINGLE = 'single'
    MISSED = 'missed'

    STATUS_CHOICES = [
        (JAMAAT, 'Jamaat'),
        (SINGLE, 'Single'),
        (MISSED, 'Missed'),
    ]

    daily_entry = models.ForeignKey(DailyEntry, on_delete=models.CASCADE, related_name='prayers')
    prayer = models.CharField(max_length=20, choices=PRAYER_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=MISSED)
    sunnah_done = models.BooleanField(default=False)

    class Meta:
        unique_together = ('daily_entry', 'prayer')
        ordering = ['id']

    def __str__(self):
        return f'{self.get_prayer_display()} - {self.get_status_display()}'


class GoalProgress(models.Model):
    """Daily submit data for each dynamic goal."""

    daily_entry = models.ForeignKey(DailyEntry, on_delete=models.CASCADE, related_name='goal_progress')
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='progress_logs')
    done = models.BooleanField(default=False)
    minutes = models.PositiveIntegerField(default=0)
    note = models.TextField(blank=True)

    class Meta:
        unique_together = ('daily_entry', 'goal')
        ordering = ['goal__category__name', 'goal__title']

    def __str__(self):
        return f'{self.goal.title} - {self.daily_entry.date}'
