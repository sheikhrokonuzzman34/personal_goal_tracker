from datetime import timedelta
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


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

    CATEGORY_CHOICES = [
        ('prayer', 'Prayer'),
        ('study', 'University Study'),
        ('skill', 'New Skill'),
        ('health', 'Health'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='goals')
    title = models.CharField(max_length=150)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
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
        prayers = self.prayers.all()
        if not prayers:
            return 0
        completed = prayers.exclude(status=PrayerLog.MISSED).count()
        return round((completed / 5) * 100)

    @property
    def productivity_score(self):
        points = 0
        total = 0

        total += 5
        points += self.prayers.exclude(status=PrayerLog.MISSED).count()

        total += 1
        if hasattr(self, 'study_log') and self.study_log.done:
            points += 1

        total += 1
        if hasattr(self, 'skill_log') and self.skill_log.done:
            points += 1

        other_total = self.other_tasks.count()
        if other_total:
            total += other_total
            points += self.other_tasks.filter(done=True).count()

        if total == 0:
            return 0
        return round((points / total) * 100)


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


class StudyLog(models.Model):
    daily_entry = models.OneToOneField(DailyEntry, on_delete=models.CASCADE, related_name='study_log')
    done = models.BooleanField(default=False)
    subject = models.CharField(max_length=150, blank=True)
    minutes = models.PositiveIntegerField(default=0)
    note = models.TextField(blank=True)

    def __str__(self):
        return f'Study - {self.daily_entry.date}'


class SkillLog(models.Model):
    daily_entry = models.OneToOneField(DailyEntry, on_delete=models.CASCADE, related_name='skill_log')
    done = models.BooleanField(default=False)
    skill_name = models.CharField(max_length=150, blank=True)
    minutes = models.PositiveIntegerField(default=0)
    note = models.TextField(blank=True)

    def __str__(self):
        return f'Skill - {self.daily_entry.date}'


class OtherTask(models.Model):
    daily_entry = models.ForeignKey(DailyEntry, on_delete=models.CASCADE, related_name='other_tasks')
    title = models.CharField(max_length=150)
    done = models.BooleanField(default=False)
    minutes = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title
