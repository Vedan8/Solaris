# Generated by Django 5.1.4 on 2024-12-10 08:45

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ProcessedModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('obj_file', models.FileField(blank=True, null=True, upload_to='processed_models/')),
                ('mtl_file', models.FileField(blank=True, null=True, upload_to='processed_models/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]