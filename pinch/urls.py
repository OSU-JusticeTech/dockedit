from django.urls import path

from pinch.views import roots, NodeView

app_name = "pinch"
urlpatterns = [
    path("", roots, name="root"),
    path("node/<path:path>/", NodeView.as_view(), name="node"),
]
