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

        for case in cases:
            fwd_docket = list(map(lambda x: x.text, reversed(case.docket)))
            hist = []
            case_node("-" + fwd_docket[0], case)
            for fr, to in zip(fwd_docket, fwd_docket[1:]):
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
