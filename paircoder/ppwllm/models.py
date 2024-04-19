from django.db import models


lang_choices = [
    ('python', 'Python'),
    ('javascript', 'JavaScript'),
    ('go', 'Go'),
    ('rust', 'Rust')
]
app_type = [
    ('sc', "script"),
    ('web', "webapp"),
    ('gui', "graphical"),
    ('cli', "commandline"),
]
experience = [
    ('non-coder', "non-coder"),
    ('amatuer', "amatueur"),
    ('junior', "junior"),
    ('midlevel', 'midlevel'),
    ('senior', 'senior')
]


class Objective(models.Model):
    challenge = models.TextField(unique=True)
    language = models.CharField(max_length=15, choices=lang_choices)
    apptype = models.CharField(max_length=15, choices=app_type)
    experience = models.CharField(max_length=15, choices=experience)
    # need to add datefield for better control

    def __str__(self):
        return self.challenge


class Promptintent(models.Model):
    objective = models.ForeignKey(Objective, on_delete=models.CASCADE)
    user_intent = models.TextField()
    user_question = models.TextField()
    user_feedback = models.TextField()
    user_satisfied = models.BooleanField(default=False)
    llm_question = models.TextField()