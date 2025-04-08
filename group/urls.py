from django.urls import path

from group.views import roots, NodeView, pinch, cases

app_name = "group"
urlpatterns = [
    path("", roots, name="root"),
    path("pinch", pinch, name="pinch"),
    path("node/<path:path>/", NodeView.as_view(), name="node"),
    path("cases/", cases, name="cases"),
]
