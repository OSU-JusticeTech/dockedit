from django.db import models

# Create your models here.


class EntryText(models.Model):
    text = models.CharField(max_length=400)

    def __str__(self):
        return self.text


class EntrySkip(models.Model):
    path = models.JSONField()
    item = models.ForeignKey("EntryText", on_delete=models.CASCADE)

    def __str__(self):
        return "/".join(map(str, self.path)) + " skip: " + self.item.text


class EntryMerge(models.Model):
    path = models.JSONField()
    item = models.ForeignKey("EntryText", on_delete=models.CASCADE)
    equals = models.ManyToManyField(EntryText, related_name="equals")

    def __str__(self):
        return (
            "/".join(map(str, self.path))
            + " use: "
            + self.item.text
            + " for: "
            + ", ".join(self.equals.values_list("text", flat=True))
        )
