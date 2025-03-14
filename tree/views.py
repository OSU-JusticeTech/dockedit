from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from tree.models import EntryText
from tree.utils import get_tree, get_cases

import networkx as nx


@staff_member_required
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


@staff_member_required
def viewnode(request, path):
    prog = []

    G = get_tree()
    hist = []
    node = None
    for p in path.split("/"):
        e = EntryText.objects.get(pk=int(p))
        if node is None:
            roots = [
                no
                for no, degree in G.in_degree()
                if degree == 0 and G.nodes[no]["pk"] == int(p)
            ]
            assert len(roots) == 1
            node = roots[0]
        else:
            for succ in G.successors(node):
                if G.nodes[succ]["pk"] == int(p):
                    node = succ
        prog.append(
            {
                "text": e,
                "path": "/".join(hist + [str(G.nodes[node]["pk"])]),
                "count": G.nodes[node]["count"],
            }
        )
        hist.append(str(e.pk))

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


@staff_member_required
def cases(request, path):
    prog = []
    G = get_tree()
    hist = []
    node = None
    for p in path.split("/"):
        e = EntryText.objects.get(pk=int(p))
        if node is None:
            roots = [
                no
                for no, degree in G.in_degree()
                if degree == 0 and G.nodes[no]["pk"] == int(p)
            ]
            assert len(roots) == 1
            node = roots[0]
        else:
            for succ in G.successors(node):
                if G.nodes[succ]["pk"] == int(p):
                    node = succ
        prog.append(
            {"text": e, "path": "/".join(hist), "count": G.nodes[node]["count"]}
        )
        hist.append(str(e.pk))

    print(G.nodes[node]["cases"])
    rel = list(filter(lambda x: x.case_number in G.nodes[node]["cases"], get_cases()))
    # print(rel)

    def transpose_respect_longest(lst):
        # Find the maximum length of the lists
        max_len = max(len(sublist) for sublist in lst)

        # Transpose while filling missing values with None
        transposed = [
            [lst[i][j] if j < len(lst[i]) else None for i in range(len(lst))]
            for j in range(max_len)
        ]

        return transposed

    tr = transpose_respect_longest([list(reversed(c.docket)) for c in rel])
    return render(
        request,
        "tree/cases.html",
        {
            "prog": prog,
            "path": path,
            "dockets": tr,
            "cases": [c.case_number for c in rel],
        },
    )
