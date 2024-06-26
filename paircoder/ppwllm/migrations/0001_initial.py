# Generated by Django 5.0.4 on 2024-04-26 06:11

import datetime
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Objective',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('challenge', models.TextField(unique=True)),
                ('language', models.CharField(choices=[('python', 'Python'), ('javascript', 'JavaScript'), ('go', 'Go'), ('rust', 'Rust')], max_length=15)),
                ('apptype', models.CharField(choices=[('sc', 'script'), ('web', 'webapp'), ('gui', 'graphical'), ('cli', 'commandline')], max_length=15)),
                ('experience', models.CharField(choices=[('non-coder', 'non-coder'), ('amatuer', 'amatueur'), ('junior', 'junior'), ('midlevel', 'midlevel'), ('senior', 'senior')], max_length=15)),
            ],
        ),
        migrations.CreateModel(
            name='Rawcontent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(blank=True, default=None)),
            ],
        ),
        migrations.CreateModel(
            name='Promptintent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_intent', models.TextField()),
                ('user_question', models.TextField()),
                ('user_feedback', models.TextField()),
                ('user_satisfied', models.BooleanField(default=False)),
                ('input_prompt', models.TextField()),
                ('llm_question', models.TextField()),
                ('objective', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ppwllm.objective')),
            ],
        ),
        migrations.CreateModel(
            name='Codesnippet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code_intent', models.TextField(blank=True)),
                ('user_input', models.TextField(blank=True)),
                ('explanation', models.TextField(blank=True)),
                ('snippet', models.TextField(blank=True)),
                ('input_type', models.CharField(blank=True, choices=[('question', 'Asking for answers'), ('write code', 'Request to code'), ('explain', 'Asking for Explanation'), ('modify', 'Request to modify code'), ('Add', 'Add a feature or requirement'), ('Remove', 'Remove a feature')], max_length=25)),
                ('objective', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ppwllm.objective')),
                ('intent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ppwllm.promptintent')),
            ],
        ),
        migrations.CreateModel(
            name='Messagestore',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('msgdate', models.DateTimeField(default=datetime.datetime(2024, 4, 26, 11, 41, 29, 149167))),
                ('phonenumber', models.CharField(max_length=15)),
                ('rawcontent', models.TextField(blank=True, default=None)),
                ('parsedmsg', models.TextField(blank=True, default=None)),
                ('sourcemsg', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ppwllm.rawcontent')),
            ],
        ),
    ]
