from collections import defaultdict

import dockedit.settings

import json
from tree.pyschema import Case
import networkx as nx
from pydantic import TypeAdapter
from tree.models import EntryText

from copy import deepcopy

def transform(T):

    G = deepcopy(T)

    skip = [{"path": [1,2], "item": 3}] #IMAGE OF NOTICE OF COURT APPEARANCE
    merge = [{"path":[1,2,3,4,5,6,5,7,5,8], "items":[17,27], "name": "MERGED PRECIPE FOR RESTITUTION AND SETOUT"}]

    def apply_transform(n, path):
        #print("applying transform", n, path)
        if len(path) > 4:
            pass
            #return

        for succ in list(G.successors(n)):
            succpk = G.nodes[succ]["pk"]
            skipthis = False
            for sk in skip:
                if path == sk["path"] and succpk == sk["item"]:
                    print("this successor should be skipped")
                    skipthis = True
            if skipthis:
                one_down = list(G.successors(succ))
                G.remove_node(succ)
                for to in one_down:
                    G.add_edge(n, to)

        # merge equal nodes
        children = defaultdict(list)
        for succ in G.successors(n):
            children[G.nodes[succ]["pk"]].append({"node_name": succ,"count": G.nodes[succ]["count"]})
        for ch in children.values():
            if len(ch) > 1:
                print("ch", ch)
                li = sorted(ch, key=lambda x:x["count"], reverse=True)
                for no in li[1:]:
                    node_name = no["node_name"]
                    one_down = list(G.successors(node_name))
                    G.nodes[li[0]["node_name"]]["count"] += G.nodes[node_name]["count"]
                    G.remove_node(node_name)
                    for to in one_down:
                        G.add_edge(li[0]["node_name"], to)

        for succ in G.successors(n):
            succpk = G.nodes[succ]["pk"]
            apply_transform(succ, path + [succpk])

    nodes_no_incoming = [node for node, degree in G.in_degree() if degree == 0]
    for node in nodes_no_incoming:
        # each tree
        apply_transform(node, [G.nodes[node]["pk"]])
    return G


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

        all_texts = set()
        for case in cases:
            for d in case.docket:
                all_texts.add(d.text)

        mapping = {}
        for t in all_texts:
            mapping[t] = EntryText.objects.get_or_create(text=t)[0].pk

        for case in cases:
            fwd_docket = list(map(lambda x: x.text, reversed(case.docket)))
            hist = []
            inc_node("-" + fwd_docket[0])
            for fr, to in zip(fwd_docket, fwd_docket[1:]):
                frnode = f"{",".join(hist)}-" + fr
                hist.append(str(mapping[fr]))
                tonode = f"{",".join(hist)}-" + to
                # print(frnode, tonode)
                TREE.add_edge(frnode, tonode)
                TREE.nodes[frnode]["label"] = fr
                TREE.nodes[frnode]["pk"] = mapping[fr]
                TREE.nodes[tonode]["label"] = to
                TREE.nodes[tonode]["pk"] = mapping[to]
                inc_node(tonode)

        dockedit.settings.TREE["data"] = TREE
    else:
        TREE = dockedit.settings.TREE["data"]
    #return TREE
    return transform(TREE)