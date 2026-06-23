from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Category, Goal, PrayerLog


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class CategoryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            else:
                field.widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = Category
        fields = ['name', 'description', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class GoalForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user:
            self.fields['category'].queryset = Category.objects.filter(user=self.user, is_active=True)

        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            else:
                field.widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = Goal
        fields = ['category', 'title', 'goal_type', 'description', 'start_date', 'end_date', 'target_minutes_per_day', 'is_active']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class PrayerSubmitForm(forms.Form):
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

    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, forms.RadioSelect) and not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-control'})
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
