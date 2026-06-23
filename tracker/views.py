from datetime import timedelta
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView, UpdateView

from .forms import DailySubmitForm, GoalForm, RegisterForm
from .models import DailyEntry, Goal, OtherTask, PrayerLog, SkillLog, StudyLog


PRAYER_FIELDS = [
    ('fajr', PrayerLog.FAJR),
    ('dhuhr', PrayerLog.DHUHR),
    ('asr', PrayerLog.ASR),
    ('maghrib', PrayerLog.MAGHRIB),
    ('isha', PrayerLog.ISHA),
]


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully.')
            return redirect('dashboard')
    else:
        form = RegisterForm()

    return render(request, 'registration/register.html', {'form': form})


def date_range_for_period(period):
    today = timezone.localdate()
    if period == 'daily':
        return today, today
    if period == 'weekly':
        return today - timedelta(days=6), today
    if period == 'monthly':
        return today - timedelta(days=29), today
    if period == 'six_month':
        return today - timedelta(days=179), today
    if period == 'yearly':
        return today - timedelta(days=364), today
    return today - timedelta(days=6), today


def build_report(user, start_date, end_date):
    entries = DailyEntry.objects.filter(user=user, date__range=[start_date, end_date]).prefetch_related('prayers', 'other_tasks')
    total_days = (end_date - start_date).days + 1
    entry_count = entries.count()

    prayer_qs = PrayerLog.objects.filter(daily_entry__user=user, daily_entry__date__range=[start_date, end_date])
    total_prayers = prayer_qs.count()
    completed_prayers = prayer_qs.exclude(status=PrayerLog.MISSED).count()
    jamaat_count = prayer_qs.filter(status=PrayerLog.JAMAAT).count()
    single_count = prayer_qs.filter(status=PrayerLog.SINGLE).count()
    missed_count = prayer_qs.filter(status=PrayerLog.MISSED).count()
    sunnah_count = prayer_qs.filter(sunnah_done=True).count()

    study_qs = StudyLog.objects.filter(daily_entry__user=user, daily_entry__date__range=[start_date, end_date])
    skill_qs = SkillLog.objects.filter(daily_entry__user=user, daily_entry__date__range=[start_date, end_date])

    study_days = study_qs.filter(done=True).count()
    skill_days = skill_qs.filter(done=True).count()
    study_minutes = study_qs.aggregate(total=Sum('minutes'))['total'] or 0
    skill_minutes = skill_qs.aggregate(total=Sum('minutes'))['total'] or 0

    other_qs = OtherTask.objects.filter(daily_entry__user=user, daily_entry__date__range=[start_date, end_date])
    other_total = other_qs.count()
    other_done = other_qs.filter(done=True).count()

    expected_prayers = total_days * 5
    prayer_percent = round((completed_prayers / expected_prayers) * 100) if expected_prayers else 0
    study_percent = round((study_days / total_days) * 100) if total_days else 0
    skill_percent = round((skill_days / total_days) * 100) if total_days else 0
    other_percent = round((other_done / other_total) * 100) if other_total else 0

    overall_parts = [prayer_percent, study_percent, skill_percent]
    if other_total:
        overall_parts.append(other_percent)
    overall_percent = round(sum(overall_parts) / len(overall_parts)) if overall_parts else 0

    return {
        'total_days': total_days,
        'entry_count': entry_count,
        'completed_prayers': completed_prayers,
        'expected_prayers': expected_prayers,
        'jamaat_count': jamaat_count,
        'single_count': single_count,
        'missed_count': missed_count,
        'sunnah_count': sunnah_count,
        'study_days': study_days,
        'skill_days': skill_days,
        'study_minutes': study_minutes,
        'skill_minutes': skill_minutes,
        'other_total': other_total,
        'other_done': other_done,
        'prayer_percent': prayer_percent,
        'study_percent': study_percent,
        'skill_percent': skill_percent,
        'other_percent': other_percent,
        'overall_percent': overall_percent,
        'entries': entries[:10],
    }


@login_required
def dashboard(request):
    today = timezone.localdate()
    today_entry = DailyEntry.objects.filter(user=request.user, date=today).prefetch_related('prayers').first()
    week_start, week_end = date_range_for_period('weekly')
    weekly_report = build_report(request.user, week_start, week_end)
    active_goals = Goal.objects.filter(user=request.user, is_active=True)[:5]

    return render(request, 'tracker/dashboard.html', {
        'today': today,
        'today_entry': today_entry,
        'weekly_report': weekly_report,
        'active_goals': active_goals,
    })


@login_required
def daily_submit(request):
    today = timezone.localdate()
    entry = DailyEntry.objects.filter(user=request.user, date=today).first()

    initial = {
        'notes': entry.notes if entry else '',
    }

    if entry:
        prayers = {p.prayer: p for p in entry.prayers.all()}
        for prefix, prayer_key in PRAYER_FIELDS:
            prayer_log = prayers.get(prayer_key)
            initial[f'{prefix}_status'] = prayer_log.status if prayer_log else PrayerLog.MISSED
            initial[f'{prefix}_sunnah'] = prayer_log.sunnah_done if prayer_log else False

        if hasattr(entry, 'study_log'):
            initial.update({
                'study_done': entry.study_log.done,
                'study_subject': entry.study_log.subject,
                'study_minutes': entry.study_log.minutes,
                'study_note': entry.study_log.note,
            })
        if hasattr(entry, 'skill_log'):
            initial.update({
                'skill_done': entry.skill_log.done,
                'skill_name': entry.skill_log.skill_name,
                'skill_minutes': entry.skill_log.minutes,
                'skill_note': entry.skill_log.note,
            })
        other_task = entry.other_tasks.first()
        if other_task:
            initial.update({
                'other_task_title': other_task.title,
                'other_task_done': other_task.done,
                'other_task_minutes': other_task.minutes,
            })
    else:
        for prefix, prayer_key in PRAYER_FIELDS:
            initial[f'{prefix}_status'] = PrayerLog.MISSED

    if request.method == 'POST':
        form = DailySubmitForm(request.POST)
        if form.is_valid():
            entry, _ = DailyEntry.objects.update_or_create(
                user=request.user,
                date=today,
                defaults={'notes': form.cleaned_data.get('notes', '')}
            )

            for prefix, prayer_key in PRAYER_FIELDS:
                PrayerLog.objects.update_or_create(
                    daily_entry=entry,
                    prayer=prayer_key,
                    defaults={
                        'status': form.cleaned_data[f'{prefix}_status'],
                        'sunnah_done': form.cleaned_data.get(f'{prefix}_sunnah', False),
                    }
                )

            StudyLog.objects.update_or_create(
                daily_entry=entry,
                defaults={
                    'done': form.cleaned_data.get('study_done', False),
                    'subject': form.cleaned_data.get('study_subject', ''),
                    'minutes': form.cleaned_data.get('study_minutes') or 0,
                    'note': form.cleaned_data.get('study_note', ''),
                }
            )

            SkillLog.objects.update_or_create(
                daily_entry=entry,
                defaults={
                    'done': form.cleaned_data.get('skill_done', False),
                    'skill_name': form.cleaned_data.get('skill_name', ''),
                    'minutes': form.cleaned_data.get('skill_minutes') or 0,
                    'note': form.cleaned_data.get('skill_note', ''),
                }
            )

            other_title = form.cleaned_data.get('other_task_title', '').strip()
            entry.other_tasks.all().delete()
            if other_title:
                OtherTask.objects.create(
                    daily_entry=entry,
                    title=other_title,
                    done=form.cleaned_data.get('other_task_done', False),
                    minutes=form.cleaned_data.get('other_task_minutes') or 0,
                )

            messages.success(request, 'Today\'s task submitted successfully.')
            return redirect('dashboard')
    else:
        form = DailySubmitForm(initial=initial)

    return render(request, 'tracker/daily_submit.html', {'form': form, 'today': today})


@login_required
def reports(request):
    period = request.GET.get('period', 'weekly')
    start_date, end_date = date_range_for_period(period)
    report = build_report(request.user, start_date, end_date)

    return render(request, 'tracker/reports.html', {
        'period': period,
        'start_date': start_date,
        'end_date': end_date,
        'report': report,
    })


class GoalListView(LoginRequiredMixin, ListView):
    model = Goal
    template_name = 'tracker/goal_list.html'
    context_object_name = 'goals'

    def get_queryset(self):
        return Goal.objects.filter(user=self.request.user)


class GoalCreateView(LoginRequiredMixin, CreateView):
    model = Goal
    form_class = GoalForm
    template_name = 'tracker/goal_form.html'
    success_url = reverse_lazy('goal_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Goal created successfully.')
        return super().form_valid(form)


class GoalUpdateView(LoginRequiredMixin, UpdateView):
    model = Goal
    form_class = GoalForm
    template_name = 'tracker/goal_form.html'
    success_url = reverse_lazy('goal_list')

    def get_queryset(self):
        return Goal.objects.filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Goal updated successfully.')
        return super().form_valid(form)
