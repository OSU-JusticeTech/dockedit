import json

import networkx as nx

import dockedit
from tree.models import EntryText
from tree.utils import get_cases


def get_tree():
    if (
        isinstance(dockedit.settings.TREE, dict)
        and "group" not in dockedit.settings.TREE
    ):
        cases = get_cases()
        print("reload group tree")
        TREE = nx.DiGraph()

        def case_node(name, case):
            if name not in TREE.nodes:
                TREE.add_node(name, cases=[])
            if "cases" not in TREE.nodes[name]:
                TREE.nodes[name]["cases"] = []
            TREE.nodes[name]["cases"].append(case)

        all_texts = set()
        for case in cases:
            for d in case.docket:
                all_texts.add(d.text)

        mapping = {}
        for t in all_texts:
            mapping[t] = EntryText.objects.get_or_create(text=t)[0]

        for e in EntryText.objects.all():
            mapping[e.text] = e

        with open("data/groups.json") as f:
            grouping = json.load(f)

        for case in cases:
            # fwd_docket = list(filter(lambda x: x in grouping, map(lambda x: x.text, reversed(case.docket))))
            fwd_docket = [
                grouping[entry.text]
                for entry in reversed(case.docket)
                if entry.text in grouping
            ]
            hist = []
            rootname = fwd_docket[0]
            if rootname.startswith("🌱"):
                rootname = rootname[1:]
            case_node("-" + rootname, case)
            for fr, to in zip(fwd_docket, fwd_docket[1:]):
                if fr.startswith("🌱"):
                    fr = fr[1:]
                if to.startswith("🌱"):
                    to = to[1:]
                frnode = f"{','.join(hist)}-" + fr
                hist.append(str(mapping[fr].pk))
                tonode = f"{','.join(hist)}-" + to
                # print(frnode, tonode)
                TREE.add_edge(frnode, tonode)
                TREE.nodes[frnode]["label"] = fr
                TREE.nodes[frnode]["obj"] = mapping[fr]
                TREE.nodes[tonode]["label"] = to
                TREE.nodes[tonode]["obj"] = mapping[to]
                case_node(tonode, case)

        dockedit.settings.TREE["group"] = TREE
        print("group tree loaded")
    else:
        TREE = dockedit.settings.TREE["group"]
    return TREE
