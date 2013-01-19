from django.db import models


class Parameter(models.Model):
    class Meta:
        app_label = 'rodan'

    result = models.ForeignKey('rodan.Result')
    key = models.CharField(max_length=50)
    value = models.CharField(max_length=50)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return '%s: %s. %s' % (self.key, self.value, self.result)
