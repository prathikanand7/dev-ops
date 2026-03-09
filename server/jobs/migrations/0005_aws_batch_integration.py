# Generated migration for AWS Batch integration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0004_alter_notebook_environment_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='status',
            field=models.CharField(
                choices=[
                    ('PENDING', 'Pending'),
                    ('PROVISIONING', 'Provisioning Resources'),
                    ('RUNNING', 'Running'),
                    ('SUCCESS', 'Success'),
                    ('FAILED', 'Failed'),
                    ('SUBMITTED', 'Submitted'),
                    ('RUNNABLE', 'Runnable'),
                    ('STARTING', 'Starting'),
                    ('SUCCEEDED', 'Succeeded'),
                ],
                default='PENDING',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='job',
            name='aws_batch_job_id',
            field=models.CharField(
                blank=True,
                help_text='AWS Batch Job ID',
                max_length=255,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='job',
            name='aws_batch_job_queue',
            field=models.CharField(
                blank=True,
                help_text='AWS Batch Job Queue',
                max_length=255,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='job',
            name='aws_batch_job_definition',
            field=models.CharField(
                blank=True,
                help_text='AWS Batch Job Definition',
                max_length=255,
                null=True
            ),
        ),
    ]
