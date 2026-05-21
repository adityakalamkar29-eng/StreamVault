from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Demo', '0003_subscription_video_required_plan'),
    ]

    operations = [
        migrations.CreateModel(
            name='Plan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(choices=[('free','Free'),('standard','Standard'),('premium','Premium')], max_length=20, unique=True)),
                ('monthly_price', models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                ('annual_price',  models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                ('max_screens',   models.PositiveIntegerField(default=1)),
                ('max_downloads', models.PositiveIntegerField(default=0)),
                ('video_quality', models.CharField(default='480p', max_length=20)),
                ('ad_free',       models.BooleanField(default=False)),
                ('updated_at',    models.DateTimeField(auto_now=True)),
            ],
        ),
    ]