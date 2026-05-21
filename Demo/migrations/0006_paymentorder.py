import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Demo', '0005_merge_20260508_1745'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('razorpay_order_id',   models.CharField(max_length=100, unique=True)),
                ('razorpay_payment_id', models.CharField(blank=True, max_length=100)),
                ('plan',       models.CharField(max_length=20)),
                ('billing',    models.CharField(choices=[('monthly','Monthly'),('annual','Annual')], default='monthly', max_length=10)),
                ('amount',     models.DecimalField(decimal_places=2, max_digits=10)),
                ('status',     models.CharField(choices=[('pending','Pending'),('success','Success'),('failed','Failed')], default='pending', max_length=20)),
                ('created_at',   models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
