# Personal Goal Tracker — Dynamic Version

A Django + Bootstrap web app for personal goal and daily task tracking.

## Correct Requirement Covered

Only **5 Waqt Namaz** is default/fixed.

Everything else is dynamic:

- User can create categories dynamically.
  - Example: University Study, New Skill, Health, Business, Reading.
- User can create goals dynamically under categories.
  - Goal duration: 24 hours, 7 days, 1 month, 6 months, 1 year.
- Daily submit page automatically shows only active goals created by the user.
- Reports calculate prayer progress and dynamic goal progress.

## Features

- Register / Login / Logout
- Default 5 Waqt Namaz tracking:
  - Jamaat
  - Single
  - Missed
  - Sunnah done / not done
- Dynamic category create/edit
- Dynamic goal create/edit
- Daily submit with:
  - Namaz status
  - Active dynamic goals
  - Done checkbox
  - Minutes
  - Short note
- Reports for:
  - Daily
  - 7 days
  - 1 month
  - 6 months
  - 1 year
- Category-wise report
- Overall progress percentage

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

- `/register/` — Create user account
- `/accounts/login/` — Login
- `/` — Dashboard
- `/categories/` — Category list
- `/categories/create/` — Create category
- `/goals/` — Goal list
- `/goals/create/` — Create goal
- `/daily-submit/` — Submit today's prayer and dynamic goals
- `/reports/` — Reports

## Flow

1. Register or login.
2. Create a category.
   - Example: University Study.
3. Create a goal under that category.
   - Example: Study Django 15 minutes daily for 1 month.
4. Go to Daily Submit.
5. Fill namaz status and tick your dynamic goals.
6. Check Dashboard and Reports.
