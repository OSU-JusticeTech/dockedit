#from django.test import TestCase
from unittest import TestCase

import networkx as nx


# Create your tests here.

class Tree(TestCase):

    def test_tree(self):
        G = nx.DiGraph()

        G.add_edge("-PETITION IN FE&D FILED", "1-")
        self.assertEqual(lion.speak(), 'The lion says "roar"')
        self.assertEqual(cat.speak(), 'The cat says "meow"')