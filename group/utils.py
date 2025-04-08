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

        def case_node(name, case, rdays=0, fdays=0):
            if name not in TREE.nodes:
                TREE.add_node(name, cases=[])
            if "cases" not in TREE.nodes[name]:
                TREE.nodes[name]["cases"] = []
            if "rdays" not in TREE.nodes[name]:
                TREE.nodes[name]["rdays"] = []
            if "fdays" not in TREE.nodes[name]:
                TREE.nodes[name]["fdays"] = []
            TREE.nodes[name]["cases"].append(case)
            TREE.nodes[name]["rdays"].append(rdays)
            TREE.nodes[name]["fdays"].append(fdays)

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
                (grouping[entry.text], entry)
                for entry in reversed(case.docket)
                if entry.text in grouping
            ]
            hist = []
            rootname = fwd_docket[0][0]
            if rootname.startswith("🌱"):
                rootname = rootname[1:]
            case_node("-" + rootname, case)
            file_date = fwd_docket[0][1].date
            for fr, to in zip(fwd_docket, fwd_docket[1:]):
                todate = to[1].date
                frdate = fr[1].date
                fr = fr[0]
                to = to[0]
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
                case_node(
                    tonode, case, (todate - frdate).days, (todate - file_date).days
                )

        dockedit.settings.TREE["group"] = TREE
        print("group tree loaded")
    else:
        TREE = dockedit.settings.TREE["group"]
    return TREE
