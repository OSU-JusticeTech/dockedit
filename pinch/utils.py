import networkx as nx

import dockedit
from tree.models import EntryText
from tree.utils import get_cases


def get_tree():
    if (
        isinstance(dockedit.settings.TREE, dict)
        and "pinch" not in dockedit.settings.TREE
    ):
        cases = get_cases()
        print("reload pinch tree")
        TREE = nx.DiGraph()

        def case_node(name, case, days=0):
            if name not in TREE.nodes:
                TREE.add_node(name, cases=[])
            if "cases" not in TREE.nodes[name]:
                TREE.nodes[name]["cases"] = []
            if "rdays" not in TREE.nodes[name]:
                TREE.nodes[name]["rdays"] = []
            TREE.nodes[name]["cases"].append(case)
            TREE.nodes[name]["rdays"].append(days)

        all_texts = set()
        for case in cases:
            for d in case.docket:
                all_texts.add(d.text)

        mapping = {}
        for t in all_texts:
            mapping[t] = EntryText.objects.get_or_create(text=t)[0]

        for case in cases:
            # fwd_docket = list(map(lambda x: x.text, reversed(case.docket)))
            fwd_docket = list(reversed(case.docket))
            hist = []
            case_node("-" + fwd_docket[0].text, case)
            for fro, too in zip(fwd_docket, fwd_docket[1:]):
                fr = fro.text
                to = too.text
                frnode = f"{','.join(hist)}-" + fr
                hist.append(str(mapping[fr].pk))
                tonode = f"{','.join(hist)}-" + to
                # print(frnode, tonode)
                TREE.add_edge(frnode, tonode)
                TREE.nodes[frnode]["label"] = fr
                TREE.nodes[frnode]["obj"] = mapping[fr]
                TREE.nodes[tonode]["label"] = to
                TREE.nodes[tonode]["obj"] = mapping[to]
                case_node(tonode, case, (too.date - fro.date).days)

        dockedit.settings.TREE["pinch"] = TREE
        print("pinch tree loaded")
    else:
        TREE = dockedit.settings.TREE["pinch"]
    return TREE
