# Personal Goal Tracker

A simple Django + Bootstrap web app for personal goals and daily task tracking.

## Features

- Register / Login / Logout
- Create goals for:
  - 24 hours / daily
  - 7 days
  - 1 month
  - 6 months
  - 1 year
- Daily task submit page
- 5 waqt namaz tracking:
  - Jamaat
  - Single
  - Missed
  - Sunnah done/not done
- University study tracking
- New skill practice tracking
- Other task tracking
- Daily, weekly, monthly, 6-month and yearly reports

## Tech Stack

- Django
- SQLite
- HTML
- CSS
- Bootstrap

## How to Run

```bash
cd personal_goal_tracker
python -m venv venv
```

### Windows

```bash
venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### macOS / Linux

```bash
source venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

## Main Pages

- `/register/` - Create user account
- `/accounts/login/` - Login
- `/` - Dashboard
- `/daily-submit/` - Submit today's tasks
- `/goals/` - Goal list
- `/goals/create/` - Create goal
- `/reports/` - Reports

## Notes

This is an MVP. Later you can add:

- Charts
- Calendar view
- Reminder system
- Streak count
- API version
- Mobile app
