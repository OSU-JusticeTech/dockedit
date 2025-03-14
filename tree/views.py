from django import views
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator

from tree.models import EntryText, EntrySkip, EntryMerge
from tree.forms import NodeForm
from tree.utils import get_tree, get_cases


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


@method_decorator(staff_member_required, name="dispatch")
class NodeView(views.View):
    def parse_path(self, path):
        prog = []

        G = get_tree(current_pos=list(map(int, path.split("/"))))
        hist = []
        node = None
        intp = []
        for p in path.split("/"):
            intp.append(int(p))
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
        return G, prog, intp, node

    def get(self, request, path):
        G, prog, intp, node = self.parse_path(path)

        form = NodeForm(G, node)

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
                    "field": form.__getitem__("succ_%d" % G.nodes[to]["pk"]),
                }
            )
            total += G.nodes[to]["count"]
        ended = G.nodes[node]["count"] - total

        return render(
            request,
            "tree/node.html",
            {
                "prog": prog,
                "path": path,
                "nodes": nodes,
                "ended": ended,
                "total": total,
                "form": form,
                "skips": EntrySkip.objects.filter(path=intp),
                "merges": EntryMerge.objects.filter(path=intp),
            },
        )

    def post(self, request, path):
        G, prog, intp, node = self.parse_path(path)

        form = NodeForm(G, node, request.POST)
        if form.is_valid():
            if "skip" in request.POST:
                selected_items = form.cleaned_data
                print("sel", selected_items)
                for fr, to in sorted(G.out_edges(node)):
                    pk = G.nodes[to]["pk"]
                    if selected_items.get("succ_%d" % pk, False):
                        EntrySkip.objects.create(path=intp, item_id=pk)
            else:
                selected_items = form.cleaned_data
                for fr, to in sorted(G.out_edges(node)):
                    pk = G.nodes[to]["pk"]
                    if "merge_%d" % pk in request.POST:
                        m = EntryMerge.objects.create(path=intp, item_id=pk)
                        for fr, to in sorted(G.out_edges(node)):
                            pk = G.nodes[to]["pk"]
                            if selected_items.get("succ_%d" % pk, False):
                                m.equals.add(EntryText.objects.get(pk=pk))
                        break
            return redirect("viewnode", path=path)


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

    # print(G.nodes[node]["cases"])
    rel = list(filter(lambda x: x.case_number in G.nodes[node]["cases"], get_cases()))
    only_ended = request.GET.get("ended", False)
    if only_ended:
        cont = set()
        for succ in G.successors(node):
            cont.update(G.nodes[succ]["cases"])

        rel = list(filter(lambda x: x.case_number not in cont, rel))

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
