# Generated by Django 4.2.4 on 2023-08-30 16:17

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='StreamList',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('title', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=1000)),
                ('stream_key', models.CharField(blank=True, max_length=100, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'StreamList',
            },
        ),
        migrations.CreateModel(
            name='Video',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('ordering', models.PositiveSmallIntegerField()),
                ('title', models.CharField(max_length=100)),
                ('size', models.IntegerField()),
                ('path', models.URLField()),
                ('status', models.CharField(choices=[('U', 'Uploading'), ('D', 'Uploaded'), ('E', 'Error')], default='U', max_length=1)),
                ('stream_list', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='streamlist.streamlist')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['stream_list', 'ordering'],
            },
        ),
        migrations.CreateModel(
            name='StreamVideo',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('path', models.URLField()),
                ('duration_in_ms', models.PositiveIntegerField()),
                ('stream_list', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='stream_video', to='streamlist.streamlist')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'StreamVideo',
            },
        ),
        migrations.CreateModel(
            name='StreamListStatus',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('Q', 'Queued'), ('P', 'Processing'), ('R', 'Ready'), ('S', 'Streaming'), ('F', 'Finished'), ('C', 'Cancelled'), ('E', 'Error')], default='Q', max_length=1)),
                ('stream_list', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stream_list_status', to='streamlist.streamlist')),
            ],
            options={
                'verbose_name': 'StreamListStatus',
            },
        ),
        migrations.CreateModel(
            name='MediaLiveChannel',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('channel_id', models.CharField(blank=True, max_length=100, null=True)),
                ('input_id', models.CharField(max_length=100)),
                ('stream_key', models.CharField(max_length=100)),
                ('audio_description_name', models.CharField(max_length=100)),
                ('video_description_name', models.CharField(max_length=100)),
                ('state', models.CharField(choices=[('C', 'Created'), ('R', 'Running')], default='C', max_length=1)),
                ('stream_list', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='media_live_channel', to='streamlist.streamlist')),
            ],
            options={
                'verbose_name': 'MediaLiveChannel',
            },
        ),
        migrations.CreateModel(
            name='MediaConvertJob',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('job_id', models.CharField(max_length=100)),
                ('status', models.CharField(choices=[('Q', 'Queued'), ('P', 'Progressing'), ('I', 'Input Information'), ('C', 'Completed'), ('E', 'Error')], default='Q', max_length=1)),
                ('error_message', models.CharField(blank=True, max_length=1000, null=True)),
                ('stream_list', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='media_convert_job', to='streamlist.streamlist')),
            ],
            options={
                'verbose_name': 'MediaConvertJob',
            },
        ),
    ]
