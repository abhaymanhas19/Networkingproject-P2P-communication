from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0020_waninfohistory'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupdevice',
            name='starlink_data_limit_gb',
            field=models.FloatField(
                blank=True,
                default=None,
                help_text='Monthly Starlink data limit in GB. Set this value via the admin page.',
                null=True,
                verbose_name='Starlink Data Limit (GB)'
            ),
        ),
    ]
