import lexkind
import nodekind

# esse arquivo contém as principais estruturas de dados
# e suas funções utilitárias

# representa uma posição no código fonte
class Position:
    def __init__(self, line, column):
        self.line = line
        self.column = column
    def copy(self):
        return Position(self.line, self.column)
    def __str__(self):
        return str(self.line) + ":" + str(self.column)

# representa uma seção continua do código fonte
# start e end tem que ser da classe Position
class Range:
    def __init__(self, pos_start, pos_end):
        self.start = pos_start
        self.end = pos_end
    def copy(self):
        return Range(self.start.copy(), self.end.copy())
    def __str__(self):
        return self.start.__str__() + " to " + self.end.__str__()

class Error:
    def __init__(self, string, range):
        self.message = string
        self.range = range
    def __str__(self):
        return "error " + self.range.__str__() + ": "+ self.message
    def copy(self):
        return Error(self.string, self.range.copy())

class Lexeme:
    def __init__(self, string, kind, range):
        self.text = string
        self.kind = kind
        self.range = range
    def __str__(self):
        return "('" + self.text + "', " + lexkind.to_string(self.kind) + ")"
    def start_column(self):
        return self.range.start.column
    def copy(self):
        return Lexeme(self.string, self.kind, self.range.copy())

# value precisa ser um Lexeme
class Node:
    def __init__(self, value, kind):
        self.value = value
        self.kind = kind
        self.leaves = []
        self.range = None

    def add_leaf(self, leaf):
        self.leaves += [leaf];

    def left(self):
        return self.leaves[0]
    def right(self):
        return self.leaves[1]

    def compute_range(self):
        if self.kind == nodekind.TERMINAL:
            self.range = self.value.range.copy()
            return;
        self.range = Range(Position(0, 0), Position(0, 0))
        for leaf in self.leaves:
            leaf.compute_range()
            if leaf.range.start.less(self.range.start):
                self.range.start = leaf.range.start.copy()
            if leaf.range.end.more(self.range.end):
                self.range.end = leaf.range.end.copy()

    def __str__(self):
        return _print_tree(self, 0)

    def copy(self):
        leaves = []
        for leaf in self.leaves:
            leaves += [leaf.copy()]
        n = Node(self.value.copy())
        n.leaves = leaves
        return n

def _print_tree(node, depth):
    if node == None:
        return _indent(depth) + "nil\n"

    out = _indent(depth) + nodekind.to_str(node.kind)
    if node.kind in [nodekind.TERMINAL, nodekind.OPERATOR]:
        out += " " + node.value.__str__()
    out += "\n"

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
