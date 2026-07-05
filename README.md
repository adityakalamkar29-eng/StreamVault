# StreamVault — Enhanced Django Netflix Clone



## Setup

```bash
cd TestApp_enhanced
pip install -r requirements.txt
python manage.py migrate        # runs both 0001_initial and 0002_rename_category_field
python manage.py createsuperuser
python manage.py runserver
```

Then visit:
- http://127.0.0.1:8000/          — user home (requires login)
- http://127.0.0.1:8000/register/ — create account
- http://127.0.0.1:8000/login/    — sign in
- http://127.0.0.1:8000/admin-login/ — admin panel (staff users only)
