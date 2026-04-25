from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0027_student_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='financialreportentry',
            name='income_source',
            field=models.CharField(blank=True, choices=[('society', 'Society Fee'), ('product', 'Product Sale'), ('other', 'Other Income')], max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='financialreportentry',
            name='receipt_image',
            field=models.ImageField(blank=True, null=True, upload_to='financial_reports/receipts/'),
        ),
    ]
