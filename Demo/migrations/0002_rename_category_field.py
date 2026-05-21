from django.db import migrations


class Migration(migrations.Migration):
    """
    Renames the badly-cased 'Category' FK field on Video to 'category'
    so it follows Django conventions and template lookups (v.category.id) work.
    """

    dependencies = [
        ('Demo', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='video',
            old_name='Category',
            new_name='category',
        ),
    ]
