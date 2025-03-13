from django.conf import settings
from django.shortcuts import render

from tree.models import EntryText
from tree.utils import get_tree


def roots(request):

    G = get_tree()

    nodes_no_incoming = [node for node, degree in G.in_degree() if degree == 0]
    print("Nodes with no incoming edges:", nodes_no_incoming)
    nodes = []
    total = 0
    for node in nodes_no_incoming:
        nodes.append({"count": G.nodes[node]["count"], "db": EntryText.objects.get(text=G.nodes[node]["label"])})
        total += G.nodes[node]["count"]

    return render(request, "tree/roots.html", {"nodes": nodes, "total": total})
