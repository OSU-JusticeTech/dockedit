import dockedit.settings

import json
from tree.pyschema import Case
import networkx as nx
from pydantic import TypeAdapter


def get_tree():
    if isinstance(dockedit.settings.TREE, dict) and len(dockedit.settings.TREE) == 0:

        CaseList = TypeAdapter(list[Case])

        with open("data/sample.json") as f:
            raw = json.load(f)
            cases = CaseList.validate_python(raw)

        TREE = nx.DiGraph()

        def inc_node(name):
            if name not in TREE.nodes:
                TREE.add_node(name, count=0)
            if "count" not in TREE.nodes[name]:
                TREE.nodes[name]["count"] = 0
            TREE.nodes[name]["count"] += 1

        from tree.models import EntryText

        for case in cases:
            fwd_docket = list(map(lambda x: x.text, reversed(case.docket)))
            hist = []
            inc_node("-" + fwd_docket[0])
            for fr, to in zip(fwd_docket, fwd_docket[1:]):
                frnode = f"{",".join(hist)}-" + fr
                hist.append(str(EntryText.objects.get_or_create(text=fr)[0].pk))
                tonode = f"{",".join(hist)}-" + to
                # print(frnode, tonode)
                TREE.add_edge(frnode, tonode)
                TREE.nodes[frnode]["label"] = fr
                TREE.nodes[tonode]["label"] = to
                inc_node(tonode)

        dockedit.settings.TREE["data"] = TREE
    else:
        TREE = dockedit.settings.TREE["data"]

    return TREE