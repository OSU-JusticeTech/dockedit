from collections import defaultdict

from django import views
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils.decorators import method_decorator

from pinch.utils import get_tree
from tree.models import EntryText
from tree.utils import get_cases, transpose_respect_longest

import plotly.offline
import plotly.graph_objects as go

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
            fig = go.Figure(data=[go.Histogram(x=G.nodes[to]["rdays"])])
            fig.update_layout(
                width=300,  # Width in pixels
                height=100,  # Height in pixels
                margin=dict(
                    l=0,  # Left margin
                    r=0,  # Right margin
                    b=0,  # Bottom margin
                    t=0,  # Top margin
                ),
            )
            graph_div = plotly.offline.plot(
                fig,
                auto_open=False,
                output_type="div",
            )
            nodes.append(
                {
                    "count": len(G.nodes[to]["cases"]),
                    "graph": to,
                    "obj": G.nodes[to]["obj"],
                    "rhist": graph_div,
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


def split_by_elements(A, B):
    # Initialize variables to keep track of the current split start and the result
    result = []
    start = 0

    # Iterate through elements of A to find their positions in B
    for element in A:
        # Find the next occurrence of the element in B after 'start' index
        try:
            index = B.index(element, start)
        except ValueError:
            return None  # In case one of the elements in A is not found in B

        # Append the segment of B from 'start' to this index (exclusive)
        result.append(B[start:index])

        # Update the start index for the next segment to be after the found element
        start = index + 1

    # After the loop, add the remaining elements of B after the last element of A
    result.append(B[start:])

    return result


@staff_member_required
def pinch(request):
    print("get req", request.GET)
    points = []
    for r, val in request.GET.items():
        print(r, val)
        if val == "on":
            try:
                x = tuple(map(int, r.split("_")))
                points.append({"pos": x[0], "obj": EntryText.objects.get(pk=x[1])})
            except Exception as e:
                print(e.__repr__())
                pass
    points = sorted(points, key=lambda p: p["pos"])
    cases = get_cases()

    contains = [p["obj"].text for p in points]

    c = {i: defaultdict(int) for i, _ in enumerate(contains)}
    c[-1] = defaultdict(int)
    sel_case = {i: defaultdict(list) for i, _ in enumerate(contains)}
    sel_case[-1] = defaultdict(list)

    for case in cases:
        it = [entry.text for entry in reversed(case.docket)]
        # print([item in it for item in seqences[variant]["docket"]])
        # contains = [item in it for item in seqences[variant]["docket"]]
        # vals = [o or n for o,n in zip(vals,contains)]
        # continue
        res = split_by_elements(contains, it)
        if res is not None:
            # print(contains)
            # print(res)
            for i, el in enumerate(res):
                # if len(el) > 0:
                c[i - 1][tuple(el)] += 1
                sel_case[i - 1][tuple(el)].append(case)
            # break

    mapping = {}
    for e in EntryText.objects.all():
        mapping[e.text] = e

    hist = 0
    full = [
        [
            (
                [(mapping[entry], hist + hist_add) for hist_add, entry in enumerate(p)],
                c,
                [case.case_number for case in sel],
            )
            for (p, c), (_, sel) in zip(c[-1].items(), sel_case[-1].items())
        ]
    ]
    hist += 100
    for i, p in enumerate(points):
        full.append([p])
        # full.append()
        hist += 200
        sorted_inbetween = sorted(
            list(zip(c[i].items(), sel_case[i].items())),
            key=lambda p: p[0][1],
            reverse=True,
        )
        full.append(
            [
                (
                    [
                        (mapping[entry], hist + hist_add)
                        for hist_add, entry in enumerate(p)
                    ],
                    c,
                    [case.case_number for case in sel],
                )
                for (p, c), (_, sel) in sorted_inbetween
            ]
        )

    # print(full)

    tr = transpose_respect_longest(full)

    return render(request, "pinch/pinch.html", {"table": tr})


@staff_member_required
def cases(request):
    rel = list(filter(lambda x: x.case_number in request.GET.keys(), get_cases()))

    tr = transpose_respect_longest([list(reversed(c.docket)) for c in rel])
    return render(
        request,
        "pinch/cases.html",
        {
            "dockets": tr,
            "cases": [c.case_number for c in rel],
        },
    )
