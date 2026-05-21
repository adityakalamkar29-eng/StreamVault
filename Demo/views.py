import hmac
import hashlib
import json
import razorpay
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import Category, Video, Subscription, Plan, PaymentOrder


# ── helpers ───────────────────────────────────────────────────────────────────

def _get_sub(user):
    sub, _ = Subscription.objects.get_or_create(user=user, defaults={'plan': 'free'})
    return sub

def _razorpay_client():
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def _ensure_plans():
    defaults = [
        {'name': 'free',     'monthly_price': 0,   'annual_price': 0,    'max_screens': 1, 'max_downloads': 0,   'video_quality': '480p',  'ad_free': False},
        {'name': 'standard', 'monthly_price': 499,  'annual_price': 3990, 'max_screens': 2, 'max_downloads': 25,  'video_quality': '1080p', 'ad_free': True},
        {'name': 'premium',  'monthly_price': 799,  'annual_price': 6390, 'max_screens': 4, 'max_downloads': 100, 'video_quality': '4K',    'ad_free': True},
    ]
    for d in defaults:
        Plan.objects.get_or_create(name=d['name'], defaults=d)


# ── USER PANEL ────────────────────────────────────────────────────────────────

@login_required(login_url='login')
def home(request):
    videos     = Video.objects.all().order_by('-created_at')
    categories = Category.objects.all()
    sub        = _get_sub(request.user)
    return render(request, 'user/home.html', {
        'videos': videos, 'categories': categories, 'sub': sub,
    })


def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username         = request.POST.get('username', '').strip()
        email            = request.POST.get('email', '').strip().lower()
        password         = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        errors = {}

        if not username:
            errors['username'] = 'Username is required.'
        elif len(username) < 3:
            errors['username'] = 'Username must be at least 3 characters.'
        elif not username.replace('_','').replace('-','').isalnum():
            errors['username'] = 'Username can only contain letters, numbers, _ and -.'
        elif User.objects.filter(username__iexact=username).exists():
            errors['username'] = 'That username is already taken.'

        if not email:
            errors['email'] = 'Email is required.'
        elif '@' not in email or '.' not in email.split('@')[-1]:
            errors['email'] = 'Enter a valid email address.'
        elif User.objects.filter(email__iexact=email).exists():
            errors['email'] = 'An account with this email already exists.'

        if not password:
            errors['password'] = 'Password is required.'
        elif len(password) < 6:
            errors['password'] = 'Password must be at least 6 characters.'
        if password and confirm_password != password:
            errors['confirm_password'] = 'Passwords do not match.'

        if errors:
            return render(request, 'user/register.html', {
                'errors': errors, 'old_username': username, 'old_email': email,
            })
        user = User.objects.create_user(username=username, email=email, password=password)
        Subscription.objects.create(user=user, plan='free')
        messages.success(request, '🎉 Account created! Please sign in.')
        return redirect('login')
    return render(request, 'user/register.html')


def check_field(request):
    field = request.GET.get('field')
    value = request.GET.get('value', '').strip()
    if field == 'username':
        if not value:
            return JsonResponse({'status': 'error', 'message': 'Username is required.'})
        if len(value) < 3:
            return JsonResponse({'status': 'error', 'message': 'At least 3 characters required.'})
        if User.objects.filter(username__iexact=value).exists():
            return JsonResponse({'status': 'taken', 'message': 'Username already taken.'})
        return JsonResponse({'status': 'ok', 'message': 'Username is available ✅'})
    elif field == 'email':
        if not value:
            return JsonResponse({'status': 'error', 'message': 'Email is required.'})
        if '@' not in value or '.' not in value.split('@')[-1]:
            return JsonResponse({'status': 'error', 'message': 'Enter a valid email address.'})
        if User.objects.filter(email__iexact=value).exists():
            return JsonResponse({'status': 'taken', 'message': 'An account with this email already exists.'})
        return JsonResponse({'status': 'ok', 'message': 'Email is available ✅'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request.'})


def user_login(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        user = authenticate(request,
                            username=request.POST.get('username'),
                            password=request.POST.get('password'))
        if user:
            login(request, user)
            return redirect(request.GET.get('next', 'home'))
        messages.error(request, 'Invalid username or password.')
    return render(request, 'user/login.html')


def user_logout(request):
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def category(request, id):
    cat        = get_object_or_404(Category, id=id)
    videos     = cat.videos.all().order_by('-created_at')
    categories = Category.objects.all()
    sub        = _get_sub(request.user)
    return render(request, 'user/category.html', {
        'cat': cat, 'videos': videos, 'categories': categories, 'sub': sub,
    })


@login_required(login_url='login')
def delete_own_account(request):
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, 'Your account has been permanently deleted.')
        return redirect('login')
    return redirect('home')


# ── SUBSCRIPTION & RAZORPAY ───────────────────────────────────────────────────

@login_required(login_url='login')
def pricing(request):
    _ensure_plans()
    sub   = _get_sub(request.user)
    plans = {p.name: p for p in Plan.objects.all()}
    return render(request, 'user/pricing.html', {
        'sub':      sub,
        'free':     plans.get('free'),
        'standard': plans.get('standard'),
        'premium':  plans.get('premium'),
    })


@login_required(login_url='login')
def subscribe(request, plan):
    """Free plan — no payment needed. Paid plans redirect to payment page."""
    if plan not in ('free', 'standard', 'premium'):
        messages.error(request, 'Invalid plan.')
        return redirect('pricing')
    if plan == 'free':
        sub = _get_sub(request.user)
        sub.plan = 'free'
        sub.save()
        messages.success(request, 'Switched to Free plan.')
        return redirect('pricing')
    return redirect('payment_gateway', plan=plan)


@login_required(login_url='login')
def payment_gateway(request, plan):
    """
    Renders the checkout page with a Razorpay order already created server-side.
    The Razorpay JS popup is opened automatically on page load.
    """
    if plan not in ('standard', 'premium'):
        messages.error(request, 'Invalid plan.')
        return redirect('pricing')

    _ensure_plans()
    plan_obj = Plan.objects.filter(name=plan).first()
    billing  = request.GET.get('billing', 'monthly')
    amount   = float(plan_obj.annual_price if billing == 'annual' else plan_obj.monthly_price)

    # Create a Razorpay order server-side
    client = _razorpay_client()
    rz_order = client.order.create({
        'amount':          int((amount + amount*0.18) * 100),   # paise
        'currency':        'INR',
        'payment_capture': 1,
        'notes': {
            'username': request.user.username,
            'plan':     plan,
            'billing':  billing,
        },
    })

    # Save a pending PaymentOrder so we can track it
    PaymentOrder.objects.create(
        user              = request.user,
        razorpay_order_id = rz_order['id'],
        plan              = plan,
        billing           = billing,
        amount            = amount,
        status            = PaymentOrder.STATUS_PENDING,
    )

    sub = _get_sub(request.user)
    return render(request, 'user/payment.html', {
        'plan':             plan,
        'billing':          billing,
        'amount':           amount,
        'plan_obj':         plan_obj,
        'sub':              sub,
        # Razorpay JS needs these
        'razorpay_key_id':    settings.RAZORPAY_KEY_ID,
        'razorpay_order_id':  rz_order['id'],
        'user_email':         request.user.email or '',
        'user_name':          request.user.get_full_name() or request.user.username,
        'amount_paise':       int((amount + amount*0.18) * 100),
    })


@login_required(login_url='login')
def create_razorpay_order(request):
    """
    AJAX endpoint — creates a fresh Razorpay order and returns its ID.
    Called by the billing-toggle JS when the user switches monthly/annual.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    data    = json.loads(request.body)
    plan    = data.get('plan')
    billing = data.get('billing', 'monthly')

    if plan not in ('standard', 'premium'):
        return JsonResponse({'error': 'Invalid plan'}, status=400)

    _ensure_plans()
    plan_obj = Plan.objects.filter(name=plan).first()
    amount   = float(plan_obj.annual_price if billing == 'annual' else plan_obj.monthly_price)

    client   = _razorpay_client()
    rz_order = client.order.create({
        'amount':          int((amount + amount*0.18)*100),
        'currency':        'INR',
        'payment_capture': 1,
    })

    # Replace the old pending order
    PaymentOrder.objects.filter(
        user=request.user, status=PaymentOrder.STATUS_PENDING, plan=plan
    ).delete()
    PaymentOrder.objects.create(
        user=request.user,
        razorpay_order_id=rz_order['id'],
        plan=plan, billing=billing, amount=amount,
        status=PaymentOrder.STATUS_PENDING,
    )

    return JsonResponse({
        'order_id':    rz_order['id'],
        'amount':      amount,
        'amount_paise': int(amount * 100),
    })


@login_required(login_url='login')
def payment_success(request):
    """
    Razorpay redirects here after successful payment (via handler in JS).
    Verifies signature, upgrades subscription, marks order as success.
    """
    if request.method != 'POST':
        return redirect('pricing')

    rz_payment_id = request.POST.get('razorpay_payment_id', '')
    rz_order_id   = request.POST.get('razorpay_order_id', '')
    rz_signature  = request.POST.get('razorpay_signature', '')

    # ── Signature verification ──────────────────────────────────────────────
    client = _razorpay_client()
    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id':   rz_order_id,
            'razorpay_payment_id': rz_payment_id,
            'razorpay_signature':  rz_signature,
        })
    except razorpay.errors.SignatureVerificationError:
        # Mark order failed
        PaymentOrder.objects.filter(razorpay_order_id=rz_order_id).update(
            status=PaymentOrder.STATUS_FAILED
        )
        messages.error(request, 'Payment verification failed. Please contact support.')
        return redirect('payment_failed')

    # ── Update order ────────────────────────────────────────────────────────
    order = get_object_or_404(PaymentOrder, razorpay_order_id=rz_order_id, user=request.user)
    order.razorpay_payment_id = rz_payment_id
    order.status              = PaymentOrder.STATUS_SUCCESS
    order.completed_at        = timezone.now()
    order.save()

    # ── Upgrade subscription ─────────────────────────────────────────────────
    sub      = _get_sub(request.user)
    sub.plan = order.plan
    sub.save()

    return render(request, 'user/payment_success.html', {
        'order': order,
        'sub':   sub,
    })


@login_required(login_url='login')
def payment_failed(request):
    return render(request, 'user/payment_failed.html')


@login_required(login_url='login')
def payment_history(request):
    orders = PaymentOrder.objects.filter(user=request.user)
    sub    = _get_sub(request.user)
    return render(request, 'user/payment_history.html', {'orders': orders, 'sub': sub})


@csrf_exempt
def razorpay_webhook(request):
    """
    Razorpay webhook — handles server-to-server payment events.
    Configure URL in Razorpay Dashboard → Settings → Webhooks.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    webhook_secret = settings.RAZORPAY_KEY_SECRET.encode()
    payload        = request.body
    signature      = request.headers.get('X-Razorpay-Signature', '')

    # Verify webhook signature
    expected_sig = hmac.new(webhook_secret, payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_sig, signature):
        return JsonResponse({'error': 'Invalid signature'}, status=400)

    data  = json.loads(payload)
    event = data.get('event', '')

    if event == 'payment.captured':
        payment   = data['payload']['payment']['entity']
        order_id  = payment.get('order_id')
        payment_id = payment.get('id')
        try:
            order = PaymentOrder.objects.get(razorpay_order_id=order_id)
            if order.status != PaymentOrder.STATUS_SUCCESS:
                order.razorpay_payment_id = payment_id
                order.status              = PaymentOrder.STATUS_SUCCESS
                order.completed_at        = timezone.now()
                order.save()
                sub      = _get_sub(order.user)
                sub.plan = order.plan
                sub.save()
        except PaymentOrder.DoesNotExist:
            pass

    elif event == 'payment.failed':
        payment  = data['payload']['payment']['entity']
        order_id = payment.get('order_id')
        PaymentOrder.objects.filter(razorpay_order_id=order_id).update(
            status=PaymentOrder.STATUS_FAILED
        )

    return JsonResponse({'status': 'ok'})


# ── ADMIN PANEL ───────────────────────────────────────────────────────────────

def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_dashboard')
    if request.method == 'POST':
        user = authenticate(request,
                            username=request.POST.get('username'),
                            password=request.POST.get('password'))
        if user and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')
        messages.error(request, 'Invalid credentials or insufficient permissions.')
    return render(request, 'admin_panel/login.html')


@login_required(login_url='admin_login')
def admin_dashboard(request):
    if not request.user.is_staff:
        return redirect('login')
    total_revenue = sum(
        o.amount for o in PaymentOrder.objects.filter(status='success')
    )
    return render(request, 'admin_panel/dashboard.html', {
        'users':         User.objects.count(),
        'videos':        Video.objects.count(),
        'categories':    Category.objects.count(),
        'recent_videos': Video.objects.order_by('-created_at')[:5],
        'total_revenue': total_revenue,
        'total_orders':  PaymentOrder.objects.filter(status='success').count(),
    })


@login_required(login_url='admin_login')
def admin_category(request):
    if not request.user.is_staff:
        return redirect('login')
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            Category.objects.create(name=name)
            messages.success(request, f'Category "{name}" created.')
        else:
            messages.error(request, 'Category name cannot be empty.')
        return redirect('admin_category')
    return render(request, 'admin_panel/category.html', {
        'categories': Category.objects.all().order_by('name')
    })


@login_required(login_url='admin_login')
def delete_category(request, id):
    if not request.user.is_staff:
        return redirect('login')
    get_object_or_404(Category, id=id).delete()
    messages.success(request, 'Category deleted.')
    return redirect('admin_category')


@login_required(login_url='admin_login')
def add_category(request):
    if not request.user.is_staff:
        return redirect('login')
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            Category.objects.create(name=name)
            messages.success(request, 'Category added.')
            return redirect('admin_category')
        messages.error(request, 'Name is required.')
    return render(request, 'admin_panel/add_category.html')


@login_required(login_url='admin_login')
def add_video(request):
    if not request.user.is_staff:
        return redirect('login')
    if request.method == 'POST':
        title        = request.POST.get('title', '').strip()
        description  = request.POST.get('description', '').strip()
        category_id  = request.POST.get('category')
        video_upload = request.FILES.get('videos')
        thumb_upload = request.FILES.get('thumbnail')
        if not all([title, description, category_id, video_upload, thumb_upload]):
            messages.error(request, 'All fields are required.')
        else:
            Video.objects.create(
                title=title, description=description,
                category_id=category_id,
                video_file=video_upload, thumbnail=thumb_upload,
            )
            messages.success(request, f'"{title}" uploaded successfully.')
            return redirect('admin_dashboard')
    return render(request, 'admin_panel/add_video.html', {'categories': Category.objects.all()})


@login_required(login_url='admin_login')
def delete_video(request, id):
    if not request.user.is_staff:
        return redirect('login')
    get_object_or_404(Video, id=id).delete()
    messages.success(request, 'Video deleted.')
    return redirect('admin_dashboard')


@login_required(login_url='admin_login')
def manage_videos(request):
    if not request.user.is_staff:
        return redirect('login')
    return render(request, 'admin_panel/manage_videos.html', {
        'videos':     Video.objects.all().order_by('-created_at').select_related('category'),
        'categories': Category.objects.all(),
    })


@login_required(login_url='admin_login')
def update_video_plan(request, id):
    if not request.user.is_staff:
        return redirect('login')
    if request.method == 'POST':
        video    = get_object_or_404(Video, id=id)
        new_plan = request.POST.get('required_plan')
        if new_plan in ('free', 'standard', 'premium'):
            video.required_plan = new_plan
            video.save()
            messages.success(request, f'"{video.title}" updated to {new_plan.capitalize()}.')
        else:
            messages.error(request, 'Invalid plan selected.')
    return redirect('manage_videos')


@login_required(login_url='admin_login')
def admin_plans(request):
    if not request.user.is_staff:
        return redirect('login')
    _ensure_plans()
    return render(request, 'admin_panel/plans.html', {
        'plans': Plan.objects.filter(name__in=['free','standard','premium']).order_by('monthly_price')
    })


@login_required(login_url='admin_login')
def update_plan(request, id):
    if not request.user.is_staff:
        return redirect('login')
    if request.method == 'POST':
        plan               = get_object_or_404(Plan, id=id)
        plan.monthly_price = request.POST.get('monthly_price', plan.monthly_price)
        plan.annual_price  = request.POST.get('annual_price',  plan.annual_price)
        plan.max_screens   = request.POST.get('max_screens',   plan.max_screens)
        plan.max_downloads = request.POST.get('max_downloads', plan.max_downloads)
        plan.video_quality = request.POST.get('video_quality', plan.video_quality)
        plan.ad_free       = request.POST.get('ad_free') == 'true'
        plan.save()
        messages.success(request, f'{plan.get_name_display()} plan updated.')
    return redirect('admin_plans')


@login_required(login_url='admin_login')
def manage_users(request):
    if not request.user.is_staff:
        return redirect('login')
    return render(request, 'admin_panel/manage_users.html', {
        'users': User.objects.all().order_by('-date_joined').select_related('subscription')
    })


@login_required(login_url='admin_login')
def update_user(request, id):
    if not request.user.is_staff:
        return redirect('login')
    if request.method == 'POST':
        target = get_object_or_404(User, id=id)
        action = request.POST.get('action')
        if action == 'toggle_staff':
            if target == request.user:
                messages.error(request, "You can't change your own admin status.")
            else:
                target.is_staff = not target.is_staff
                target.save()
                messages.success(request, f'{"Granted" if target.is_staff else "Removed"} admin for {target.username}.')
        elif action == 'toggle_active':
            if target == request.user:
                messages.error(request, "You can't deactivate yourself.")
            else:
                target.is_active = not target.is_active
                target.save()
                messages.success(request, f'User {target.username} {"activated" if target.is_active else "deactivated"}.')
        elif action == 'change_plan':
            new_plan = request.POST.get('plan')
            if new_plan in ('free', 'standard', 'premium'):
                sub, _ = Subscription.objects.get_or_create(user=target, defaults={'plan': 'free'})
                sub.plan = new_plan
                sub.save()
                messages.success(request, f'{target.username} plan → {new_plan.capitalize()}.')
        elif action == 'delete_user':
            if target == request.user:
                messages.error(request, "You can't delete yourself.")
            else:
                name = target.username
                target.delete()
                messages.success(request, f'User "{name}" deleted.')
                return redirect('manage_users')
    return redirect('manage_users')


@login_required(login_url='admin_login')
def admin_payments(request):
    if not request.user.is_staff:
        return redirect('login')
    orders        = PaymentOrder.objects.select_related('user').order_by('-created_at')
    total_revenue = sum(o.amount for o in orders.filter(status='success'))
    return render(request, 'admin_panel/payments.html', {
        'orders': orders, 'total_revenue': total_revenue,
    })
