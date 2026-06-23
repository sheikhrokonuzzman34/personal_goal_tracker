from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView, UpdateView

from .forms import CategoryForm, GoalForm, PrayerSubmitForm, RegisterForm
from .models import Category, DailyEntry, Goal, GoalProgress, PrayerLog


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


def overlap_days(goal, start_date, end_date):
    start = max(goal.start_date, start_date)
    end = min(goal.end_date, end_date)
    if start > end:
        return 0
    return (end - start).days + 1


def active_goals_for_date(user, date):
    return Goal.objects.filter(
        user=user,
        is_active=True,
        start_date__lte=date,
        end_date__gte=date,
        category__is_active=True,
    ).select_related('category').order_by('category__name', 'title')


def build_report(user, start_date, end_date):
    entries = DailyEntry.objects.filter(user=user, date__range=[start_date, end_date]).prefetch_related(
        'prayers', 'goal_progress__goal__category'
    )
    total_days = (end_date - start_date).days + 1

    prayer_qs = PrayerLog.objects.filter(daily_entry__user=user, daily_entry__date__range=[start_date, end_date])
    completed_prayers = prayer_qs.exclude(status=PrayerLog.MISSED).count()
    jamaat_count = prayer_qs.filter(status=PrayerLog.JAMAAT).count()
    single_count = prayer_qs.filter(status=PrayerLog.SINGLE).count()
    missed_count = prayer_qs.filter(status=PrayerLog.MISSED).count()
    sunnah_count = prayer_qs.filter(sunnah_done=True).count()

    expected_prayers = total_days * 5
    prayer_percent = round((completed_prayers / expected_prayers) * 100) if expected_prayers else 0

    goals = Goal.objects.filter(
        user=user,
        start_date__lte=end_date,
        end_date__gte=start_date,
        category__is_active=True,
    ).select_related('category')

    expected_goal_tasks = sum(overlap_days(goal, start_date, end_date) for goal in goals)
    progress_qs = GoalProgress.objects.filter(
        daily_entry__user=user,
        daily_entry__date__range=[start_date, end_date],
        goal__in=goals,
    ).select_related('goal__category')
    completed_goal_tasks = progress_qs.filter(done=True).count()
    goal_minutes = progress_qs.aggregate(total=Sum('minutes'))['total'] or 0
    goal_percent = round((completed_goal_tasks / expected_goal_tasks) * 100) if expected_goal_tasks else 0

    category_reports = []
    categories = Category.objects.filter(user=user, is_active=True).order_by('name')
    for category in categories:
        cat_goals = [goal for goal in goals if goal.category_id == category.id]
        cat_expected = sum(overlap_days(goal, start_date, end_date) for goal in cat_goals)
        if not cat_expected:
            continue
        cat_progress = progress_qs.filter(goal__category=category)
        cat_done = cat_progress.filter(done=True).count()
        cat_minutes = cat_progress.aggregate(total=Sum('minutes'))['total'] or 0
        category_reports.append({
            'category': category,
            'expected': cat_expected,
            'done': cat_done,
            'minutes': cat_minutes,
            'percent': round((cat_done / cat_expected) * 100) if cat_expected else 0,
        })

    if expected_goal_tasks:
        overall_percent = round((prayer_percent + goal_percent) / 2)
    else:
        overall_percent = prayer_percent

    return {
        'total_days': total_days,
        'entry_count': entries.count(),
        'completed_prayers': completed_prayers,
        'expected_prayers': expected_prayers,
        'jamaat_count': jamaat_count,
        'single_count': single_count,
        'missed_count': missed_count,
        'sunnah_count': sunnah_count,
        'prayer_percent': prayer_percent,
        'expected_goal_tasks': expected_goal_tasks,
        'completed_goal_tasks': completed_goal_tasks,
        'goal_minutes': goal_minutes,
        'goal_percent': goal_percent,
        'category_reports': category_reports,
        'overall_percent': overall_percent,
        'entries': entries[:10],
    }


@login_required
def dashboard(request):
    today = timezone.localdate()
    today_entry = DailyEntry.objects.filter(user=request.user, date=today).prefetch_related(
        'prayers', 'goal_progress__goal__category'
    ).first()
    week_start, week_end = date_range_for_period('weekly')
    weekly_report = build_report(request.user, week_start, week_end)
    active_goals = active_goals_for_date(request.user, today)[:6]

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
    active_goals = list(active_goals_for_date(request.user, today))

    initial = {'notes': entry.notes if entry else ''}
    if entry:
        prayers = {p.prayer: p for p in entry.prayers.all()}
        for prefix, prayer_key in PRAYER_FIELDS:
            prayer_log = prayers.get(prayer_key)
            initial[f'{prefix}_status'] = prayer_log.status if prayer_log else PrayerLog.MISSED
            initial[f'{prefix}_sunnah'] = prayer_log.sunnah_done if prayer_log else False
    else:
        for prefix, prayer_key in PRAYER_FIELDS:
            initial[f'{prefix}_status'] = PrayerLog.MISSED

    if request.method == 'POST':
        form = PrayerSubmitForm(request.POST)
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

            for goal in active_goals:
                done = request.POST.get(f'goal_{goal.id}_done') == 'on'
                minutes_raw = request.POST.get(f'goal_{goal.id}_minutes') or 0
                try:
                    minutes = max(0, int(minutes_raw))
                except ValueError:
                    minutes = 0
                note = request.POST.get(f'goal_{goal.id}_note', '').strip()

                GoalProgress.objects.update_or_create(
                    daily_entry=entry,
                    goal=goal,
                    defaults={'done': done, 'minutes': minutes, 'note': note}
                )

            messages.success(request, 'Today\'s task submitted successfully.')
            return redirect('dashboard')
    else:
        form = PrayerSubmitForm(initial=initial)

    progress_map = {}
    if entry:
        progress_map = {p.goal_id: p for p in entry.goal_progress.all()}

    goal_rows = []
    for goal in active_goals:
        progress = progress_map.get(goal.id)
        goal_rows.append({
            'goal': goal,
            'done': progress.done if progress else False,
            'minutes': progress.minutes if progress else goal.target_minutes_per_day,
            'note': progress.note if progress else '',
        })

    return render(request, 'tracker/daily_submit.html', {
        'form': form,
        'today': today,
        'goal_rows': goal_rows,
    })


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


class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'tracker/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'tracker/category_form.html'
    success_url = reverse_lazy('category_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Category created successfully.')
        return super().form_valid(form)


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'tracker/category_form.html'
    success_url = reverse_lazy('category_list')

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Category updated successfully.')
        return super().form_valid(form)


class GoalListView(LoginRequiredMixin, ListView):
    model = Goal
    template_name = 'tracker/goal_list.html'
    context_object_name = 'goals'

    def get_queryset(self):
        return Goal.objects.filter(user=self.request.user).select_related('category')


class GoalCreateView(LoginRequiredMixin, CreateView):
    model = Goal
    form_class = GoalForm
    template_name = 'tracker/goal_form.html'
    success_url = reverse_lazy('goal_list')

    def dispatch(self, request, *args, **kwargs):
        if not Category.objects.filter(user=request.user, is_active=True).exists():
            messages.info(request, 'Please create a category first, then add your goals under that category.')
            return redirect('category_create')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

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
        return Goal.objects.filter(user=self.request.user).select_related('category')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Goal updated successfully.')
        return super().form_valid(form)
