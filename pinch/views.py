from django import views
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils.decorators import method_decorator

from pinch.utils import get_tree


# Create your views here.


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
                "count": len(G.nodes[node]["cases"]),
                "obj": G.nodes[node]["obj"],
            }
        )
        total += len(G.nodes[node]["cases"])

    return render(request, "pinch/roots.html", {"nodes": nodes, "total": total})


@method_decorator(staff_member_required, name="dispatch")
class NodeView(views.View):
    def parse_path(self, path):
        prog = []

        G = get_tree()
        hist = []
        node = None
        intp = []
        for p in path.split("/"):
            intp.append(int(p))

            if node is None:
                roots = [
                    no
                    for no, degree in G.in_degree()
                    if degree == 0 and G.nodes[no]["obj"].pk == int(p)
                ]
                assert len(roots) == 1
                node = roots[0]
            else:
                for succ in G.successors(node):
                    if G.nodes[succ]["obj"].pk == int(p):
                        node = succ
            prog.append(
                {
                    "obj": G.nodes[node]["obj"],
                    "path": "/".join(hist + [str(G.nodes[node]["obj"].pk)]),
                    "count": len(G.nodes[node]["cases"]),
                }
            )
            hist.append(str(G.nodes[node]["obj"].pk))
        return G, prog, intp, node

    def get(self, request, path):
        G, prog, intp, node = self.parse_path(path)

        total = 0
        nodes = []
        for fr, to in sorted(
            G.out_edges(node), key=lambda x: len(G.nodes[x[1]]["cases"]), reverse=True
        ):
            nodes.append(
                {
                    "count": len(G.nodes[to]["cases"]),
                    "graph": to,
                    "obj": G.nodes[to]["obj"],
                }
            )
            total += len(G.nodes[to]["cases"])
        ended = len(G.nodes[to]["cases"]) - total

        return render(
            request,
            "pinch/node.html",
            {
                "prog": prog,
                "path": path,
                "nodes": nodes,
                "ended": ended,
                "total": total,
            },
        )
