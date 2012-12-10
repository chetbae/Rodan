from django.db import models


class Page(models.Model):
    project = models.ForeignKey('rodan.Project')
    filename = models.FileField(upload_to="images")
    page_order = models.IntegerField(null=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'rodan'

    def __unicode__(self):
        return unicode(self.filename)
