from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Goal, PrayerLog


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class GoalForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            else:
                field.widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = Goal
        fields = ['title', 'category', 'goal_type', 'description', 'start_date', 'end_date', 'target_minutes_per_day', 'is_active']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class DailySubmitForm(forms.Form):
    PRAYER_STATUS = PrayerLog.STATUS_CHOICES

    fajr_status = forms.ChoiceField(choices=PRAYER_STATUS, widget=forms.RadioSelect)
    fajr_sunnah = forms.BooleanField(required=False)

    dhuhr_status = forms.ChoiceField(choices=PRAYER_STATUS, widget=forms.RadioSelect)
    dhuhr_sunnah = forms.BooleanField(required=False)

    asr_status = forms.ChoiceField(choices=PRAYER_STATUS, widget=forms.RadioSelect)
    asr_sunnah = forms.BooleanField(required=False)

    maghrib_status = forms.ChoiceField(choices=PRAYER_STATUS, widget=forms.RadioSelect)
    maghrib_sunnah = forms.BooleanField(required=False)

    isha_status = forms.ChoiceField(choices=PRAYER_STATUS, widget=forms.RadioSelect)
    isha_sunnah = forms.BooleanField(required=False)

    study_done = forms.BooleanField(required=False, label='University study done')
    study_subject = forms.CharField(required=False, max_length=150)
    study_minutes = forms.IntegerField(required=False, min_value=0, initial=0)
    study_note = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}))

    skill_done = forms.BooleanField(required=False, label='New skill practice done')
    skill_name = forms.CharField(required=False, max_length=150)
    skill_minutes = forms.IntegerField(required=False, min_value=0, initial=0)
    skill_note = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}))

    other_task_title = forms.CharField(required=False, max_length=150, label='Other task')
    other_task_done = forms.BooleanField(required=False)
    other_task_minutes = forms.IntegerField(required=False, min_value=0, initial=0)

    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.RadioSelect) and not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-control'})
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
