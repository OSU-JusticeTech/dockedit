from django.contrib import admin

# Register your models here.

from .models import EntryText, EntrySkip, EntryMerge

admin.site.register(EntryText)
admin.site.register(EntrySkip)
admin.site.register(EntryMerge)
