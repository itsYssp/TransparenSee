from django.db import migrations, models
import django.db.models.deletion


def delete_null_report_logs(apps, schema_editor):
    AccomplishmentReportLog = apps.get_model('app', 'AccomplishmentReportLog')
    AccomplishmentReportLog.objects.filter(report__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_accomplishmentreportlog_organization_and_more'),
    ]

    operations = [
        migrations.RunPython(delete_null_report_logs, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='accomplishmentreportlog',
            name='organization',
        ),
        migrations.RemoveField(
            model_name='accomplishmentreportlog',
            name='report_title',
        ),
        migrations.AlterField(
            model_name='accomplishmentreportlog',
            name='action',
            field=models.CharField(choices=[('submitted', 'Submitted')], max_length=20),
        ),
        migrations.AlterField(
            model_name='accomplishmentreportlog',
            name='report',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ar_log', to='app.accomplishmentreport'),
        ),
    ]
