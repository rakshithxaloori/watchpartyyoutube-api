# Generated by Django 4.2.4 on 2023-09-07 06:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('streamlist', '0006_streamvideo_status_alter_video_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='medialivechannel',
            name='stop_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
