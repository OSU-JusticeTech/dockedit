import time
from collections import defaultdict

import dockedit.settings

import json
from tree.pyschema import Case
import networkx as nx
from pydantic import TypeAdapter
from tree.models import EntryText, EntrySkip, EntryMerge

# from copy import deepcopy, copy
import copy


def transform(T, current_pos=None):
    t_start = time.perf_counter()
    print("start transform")
    G = nx.DiGraph()
    # G = T.copy() # deepcopy(T)
    print("copy", time.perf_counter() - t_start)

    def cleanup_duplicates(n):
        # merge equal children
        children = defaultdict(list)
        for succ in G.successors(n):
            children[G.nodes[succ]["pk"]].append(
                {"node_name": succ, "count": G.nodes[succ]["count"]}
            )
        for ch in children.values():
            if len(ch) > 1:
                # print("ch", ch)
                li = sorted(ch, key=lambda x: x["count"], reverse=True)
                for no in li[1:]:
                    node_name = no["node_name"]
                    one_down = list(G.successors(node_name))
                    G.nodes[li[0]["node_name"]]["count"] += G.nodes[node_name]["count"]
                    old_list = copy.copy(G.nodes[li[0]["node_name"]]["cases"])
                    G.nodes[li[0]["node_name"]]["cases"] = (
                        old_list + G.nodes[node_name]["cases"]
                    )
                    G.remove_node(node_name)
                    for to in one_down:
                        G.add_edge(li[0]["node_name"], to)

    merges = EntryMerge.objects.all()
    skips = EntrySkip.objects.all()

    def copy_part(n):
        if n not in G.nodes:
            G.add_node(n)
            G.nodes[n]["count"] = T.nodes[n]["count"]
            G.nodes[n]["label"] = T.nodes[n]["label"]
            if "cases" in G.nodes[n]:
                G.nodes[n]["cases"] = copy.copy(T.nodes[n]["cases"])
            G.nodes[n]["pk"] = T.nodes[n]["pk"]
        for fr, to in T.out_edges(n):
            if not G.has_edge(fr, to):
                G.add_edge(fr, to)
                G.nodes[to]["count"] = T.nodes[to]["count"]
                G.nodes[to]["label"] = T.nodes[to]["label"]
                G.nodes[to]["cases"] = copy.copy(T.nodes[to]["cases"])
                G.nodes[to]["pk"] = T.nodes[to]["pk"]

    def apply_transform(n, path):
        # print("applying transform", n, path)
        if current_pos is not None and len(path) > len(current_pos) + 2:
            # pass
            return

        copy_part(n)
        done_skip = False
        while not done_skip:
            done_skip = True
            for succ in list(G.successors(n)):
                succpk = G.nodes[succ]["pk"]
                skipthis = False
                for sk in skips:
                    if path == sk.path and succpk == sk.item.pk:
                        print("this successor should be skipped")
                        skipthis = True
                if skipthis:
                    copy_part(succ)
                    one_down = list(G.successors(succ))
                    G.remove_node(succ)
                    for to in one_down:
                        G.add_edge(n, to)
                    done_skip = False

        cleanup_duplicates(n)
        # merge speced nodes:
        for me in merges:
            if path == me.path:
                children = {}
                for succ in G.successors(n):
                    children[G.nodes[succ]["pk"]] = succ
                if me.item.pk in children:
                    print("merge ", children)
                    for eq in me.equals.values_list("pk", flat=True):
                        print("try ", eq, children[eq], list(G.successors(n)))
                        if children[eq] in list(G.successors(n)):
                            print("is in list", eq, children[eq])
                            copy_part(children[eq])

                            one_down = list(G.successors(children[eq]))
                            print(
                                "update count",
                                G.nodes[children[me.item.pk]]["count"],
                                "with ",
                                G.nodes[children[eq]]["count"],
                            )
                            G.nodes[children[me.item.pk]]["count"] += G.nodes[
                                children[eq]
                            ]["count"]
                            old_list = copy.copy(G.nodes[children[me.item.pk]]["cases"])
                            G.nodes[children[me.item.pk]]["cases"] = (
                                old_list + G.nodes[children[eq]]["cases"]
                            )
                            G.remove_node(children[eq])
                            for to in one_down:
                                G.add_edge(children[me.item.pk], to)

        cleanup_duplicates(n)

        # recurse:
        for succ in G.successors(n):
            succpk = G.nodes[succ]["pk"]
            apply_transform(succ, path + [succpk])

    nodes_no_incoming = [node for node, degree in T.in_degree() if degree == 0]
    for node in nodes_no_incoming:
        # each tree
        apply_transform(node, [T.nodes[node]["pk"]])
    print("full trans", time.perf_counter() - t_start)
    return G


def get_cases():
    if "cases" not in dockedit.settings.TREE:
        print("reload all cases")
        CaseList = TypeAdapter(list[Case])

        # with open("data/sample.json") as f:
        with open("data/cases.json") as f:
            raw = json.load(f)
            cases = CaseList.validate_python(raw)
        dockedit.settings.TREE["cases"] = cases
        print("cases loaded")
        return cases
    else:
        return dockedit.settings.TREE["cases"]


def get_tree(current_pos=None):
    if (
        isinstance(dockedit.settings.TREE, dict)
        and "data" not in dockedit.settings.TREE
    ):
        cases = get_cases()
        print("reload tree")
        TREE = nx.DiGraph()

        def inc_node(name):
            if name not in TREE.nodes:
                TREE.add_node(name, count=0)
            if "count" not in TREE.nodes[name]:
                TREE.nodes[name]["count"] = 0
            TREE.nodes[name]["count"] += 1

        def case_node(name, cno):
            if name not in TREE.nodes:
                TREE.add_node(name, cases=[])
            if "cases" not in TREE.nodes[name]:
                TREE.nodes[name]["cases"] = []
            TREE.nodes[name]["cases"].append(cno)

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
                frnode = f"{','.join(hist)}-" + fr
                hist.append(str(mapping[fr]))
                tonode = f"{','.join(hist)}-" + to
                # print(frnode, tonode)
                TREE.add_edge(frnode, tonode)
                TREE.nodes[frnode]["label"] = fr
                TREE.nodes[frnode]["pk"] = mapping[fr]
                TREE.nodes[tonode]["label"] = to
                TREE.nodes[tonode]["pk"] = mapping[to]
                inc_node(tonode)
                case_node(tonode, case.case_number)

        dockedit.settings.TREE["data"] = TREE
        print("tree loaded")
    else:
        TREE = dockedit.settings.TREE["data"]
    # return TREE
    return transform(TREE, current_pos)
