from django.urls import path

from pinch.views import roots, NodeView, pinch, cases

app_name = "pinch"
urlpatterns = [
    path("", roots, name="root"),
    path("pinch", pinch, name="pinch"),
    path("node/<path:path>/", NodeView.as_view(), name="node"),
    path("cases/", cases, name="cases"),
]
