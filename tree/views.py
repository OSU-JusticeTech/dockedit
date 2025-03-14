from django.shortcuts import render

from tree.models import EntryText
from tree.utils import get_tree

import networkx as nx


def roots(request):
    G = get_tree()

    nodes_no_incoming = [node for node, degree in G.in_degree() if degree == 0]
    print("Nodes with no incoming edges:", nodes_no_incoming)
    nodes = []
    total = 0
    for node in nodes_no_incoming:
        nodes.append(
            {
                "count": G.nodes[node]["count"],
                "db": EntryText.objects.get(text=G.nodes[node]["label"]),
            }
        )
        total += G.nodes[node]["count"]

    return render(request, "tree/roots.html", {"nodes": nodes, "total": total})


def count_branch_nodes(G, root):
    # Extract the subtree (all reachable nodes from the root)
    subtree = nx.descendants(G, root) | {root}

    # Count nodes with more than 1 successor
    branch_count = 0
    for node in subtree:
        if len(list(G.successors(node))) > 1:
            branch_count += 1

    return branch_count


def viewnode(request, path):
    prog = []

    G = get_tree()
    hist = []
    for p in path.split("/"):
        e = EntryText.objects.get(pk=int(p))
        node = f"{','.join(hist)}-" + e.text
        prog.append(
            {"text": e, "path": "/".join(hist), "count": G.nodes[node]["count"]}
        )
        hist.append(str(e.pk))

    node = f"{','.join(hist[:-1])}-" + e.text
    total = 0
    nodes = []
    for fr, to in sorted(
        G.out_edges(node), key=lambda x: G.nodes[x[1]]["count"], reverse=True
    ):
        # print("to", to)
        nodes.append(
            {
                "count": G.nodes[to]["count"],
                "graph": to,
                "db": EntryText.objects.get(text=G.nodes[to]["label"]),
            }
        )
        total += G.nodes[to]["count"]
    ended = G.nodes[node]["count"] - total

    tree_size = count_branch_nodes(G, node)

    return render(
        request,
        "tree/node.html",
        {
            "prog": prog,
            "path": path,
            "nodes": nodes,
            "ended": ended,
            "total": total,
            "tree_size": tree_size,
        },
    )
