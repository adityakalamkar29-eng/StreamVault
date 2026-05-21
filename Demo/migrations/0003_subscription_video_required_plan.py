from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Demo', '0002_rename_category_field'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='video',
            name='required_plan',
            field=models.CharField(
                choices=[('free', 'Free'), ('standard', 'Standard'), ('premium', 'Premium')],
                default='free',
                max_length=20,
            ),
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('plan', models.CharField(
                    choices=[('free', 'Free'), ('standard', 'Standard'), ('premium', 'Premium')],
                    default='free',
                    max_length=20,
                )),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('active', models.BooleanField(default=True)),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='subscription',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
        ),
    ]
