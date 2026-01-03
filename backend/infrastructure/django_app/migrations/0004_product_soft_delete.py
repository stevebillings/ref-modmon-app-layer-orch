from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("django_app", "0003_add_auth_and_user_ids"),
    ]

    operations = [
        migrations.AddField(
            model_name="productmodel",
            name="deleted_at",
            field=models.DateTimeField(null=True, blank=True, db_index=True),
        ),
    ]
