# StreamVault — Enhanced Django Netflix Clone

## Bugs Fixed

### Critical (app-breaking)
1. **Login redirect crash** (`views.py` `user_login`): `redirect('user/home.html')` used a
   template path instead of a URL name. Django's redirect() needs a named URL like `'home'`.
2. **Category view re-authenticates on every request** (`views.py` `category`): The view
   called `authenticate()` inside a POST check, meaning the page was always inaccessible
   via GET. Fixed to use `@login_required` and simply fetch the category by ID.
3. **Admin login failure redirected to wrong template path** (`views.py` `admin_login`):
   On bad credentials, it called `redirect('admin_login.html')` — a template filename,
   not a URL. This caused a `NoReverseMatch` exception on every failed login.
4. **Login button had `<a>` tag inside `<button>`** (`login.html`): The submit button wrapped
   an anchor tag (`<a href="/category/">`), which hijacked the click event, bypassed form
   submission entirely, and navigated to a broken URL.
5. **Video cards never showed on home page** (`home.html`): The template compared
   `v.category.id == c.id`, but the model FK field was named `Category` (capital C). Django
   lowercases all attribute access, so `v.category` returned `AttributeError` silently in
   templates, meaning no card ever matched. Fixed by renaming the field to `category` in
   the model and adding migration `0002_rename_category_field.py`.

### Settings bugs
6. **`STATIC_DIRS` is not a valid Django setting** (`settings.py`): The correct name is
   `STATICFILES_DIRS`. With the wrong key, Django ignores the app's static files entirely.
7. **`MEDIA_ROOT` was a bare string `'media'`** (`settings.py`): Relative string paths can
   break depending on the working directory. Fixed to `BASE_DIR / 'media'` (an absolute Path).

### Missing features added
- `@login_required` protection on `home` and `category` views (unauthenticated users were
  previously able to access the home page without logging in)
- Flash messages using Django's `messages` framework on login, register, and all admin actions
- Delete video and delete category endpoints (`/admin-delete-video/<id>/` and
  `/admin-delete-category/<id>/`) — the admin template had delete buttons pointing to URLs
  that didn't exist
- `Video` and `Category` registered in Django admin via `admin.py`
- Category page now has a sidebar listing all categories for easy navigation
- Hero fallback gradient when no thumbnail exists (prevents broken `<img>` tags)
- Empty state UI when no videos or categories exist yet

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
