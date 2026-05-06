from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='note',
            field=models.CharField(blank=True, default='', max_length=500),
        ),
    ]
