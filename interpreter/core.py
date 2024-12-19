# esse arquivo contém as principais estruturas de dados
# e suas funções utilitárias

class Error:
    def __init__(self, string):
        self.message = string
    def __str__(self):
        return "error:" + self.message

class Lexeme:
    def __init__(self, string, kind):
        self.text = string
        self.kind = kind
    def __str__(self):
        return "(" + self.text + ", " + self.kind.__str__() + ")"

class Node:
    def __init__(self, value):
        self.value = value
        self.leaves = []

    def addLeaf(self, leaf):
        self.leaves += [leaf];

    def left(self):
        return self.leaves[0]
    def right(self):
        return self.leaves[1]

    def __str__(self):
        return _print_tree(self, 0)

def _print_tree(node, depth):
    out = _indent(depth) + node.value.__str__()
    for n in node.leaves:
        out += _print_tree(n, depth+1)
    return out

def _indent(n):
    i = 0
    out = ""
    while i < n:
        out += "  "
        i += 1
    return out
