from django import forms


class NodeForm(forms.Form):
    def __init__(self, G, node, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for fr, to in sorted(
            G.out_edges(node), key=lambda x: G.nodes[x[1]]["count"], reverse=True
        ):
            self.fields["succ_%d" % G.nodes[to]["pk"]] = forms.BooleanField(
                label=G.nodes[to]["label"],
                required=False,
            )
