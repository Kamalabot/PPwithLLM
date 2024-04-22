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
queries = [
    ('question', 'Asking for answers'),
    ('write code', 'Request to code'),
    ('explain', 'Asking for Explanation'),
    ('modify', 'Request to modify code'),
    ('Add', 'Add a feature or requirement'),
    ('Remove', 'Remove a feature')
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
    input_prompt = models.TextField()
    llm_question = models.TextField()


class Codesnippet(models.Model):
    objective = models.ForeignKey(Objective, on_delete=models.CASCADE)
    code_intent = models.TextField(blank=True)
    user_input = models.TextField(blank=True)
    explanation = models.TextField(blank=True)
    snippet = models.TextField(blank=True)
    input_type = models.CharField(max_length=25, choices=queries,
                                  blank=True)