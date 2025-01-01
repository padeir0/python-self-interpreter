import lexkind
import nodekind

# esse arquivo contém as principais estruturas de dados
# e suas funções utilitárias

class Result:
    def __init__(self, value, error):
        # GOD what wouldn't i do for static types :)
        #if type(value) is Result:
        #    raise
        self.value = value
        self.error = error

    def ok(self):
        return self.error == None

    def failed(self):
        return self.error != None

# representa uma posição no código fonte
class Position:
    def __init__(self, line, column):
        self.line = line
        self.column = column
    def copy(self):
        return Position(self.line, self.column)
    def __str__(self):
        return str(self.line) + ":" + str(self.column)
    def correct_editor_view(self):
        # no lexer a gente começa na linha 0, coluna 0,
        # mas no editor, nós vémos tudo começando da linha 1,
        # coluna 1
        self.line += 1
        self.column += 1
    def less(self, other):
        if self.line < other.line:
            return True
        if self.line > other.line:
            return False
        # aqui as linhas são iguais
        if self.column < other.column:
            return True
        return False
    def more(self, other):
        if self.line > other.line:
            return True
        if self.line < other.line:
            return False
        # aqui as linhas são iguais
        if self.column > other.column:
            return True
        return False

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
    def correct_editor_view(self):
        self.start.correct_editor_view()
        self.end.correct_editor_view()

class Error:
    def __init__(self, string, range):
        self.message = string
        self.range = range
    def __str__(self):
        if self.range != None:
            return "error " + self.range.__str__() + ": "+ self.message
        else:
            return "error: " + self.message
    def copy(self):
        if self.range != None:
            return Error(self.message, self.range.copy())
        else:
            return Error(self.message, None)
    def correct_editor_view(self):
        if self.range != None:
            self.range.correct_editor_view()

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

    def has_lexkind(self, kind):
        return self.value.kind == kind

    def has_lexkinds(self, kinds):
        i = 0
        while i < len(kinds):
            kind = kinds[i]
            if self.value.kind == kind:
                return True
            i += 1
        return False

    def compute_range(self):
        if self.kind == nodekind.TERMINAL:
            self.range = self.value.range.copy()
            return;
        self.range = Range(Position(0, 0), Position(0, 0))
        i = 0
        while i < len(self.leaves):
            leaf = self.leaves[i]

            if leaf != None:
                leaf.compute_range()
                if leaf.range.start.less(self.range.start):
                    self.range.start = leaf.range.start.copy()
                if leaf.range.end.more(self.range.end):
                    self.range.end = leaf.range.end.copy()
            i += 1

    def __str__(self):
        return _print_tree(self, 0)

    def copy(self):
        leaves = []
        i = 0
        while i < len(self.leaves):
            leaf = self.leaves[i]

            leaves += [leaf.copy()]
            i += 1
        n = Node(self.value.copy())
        n.leaves = leaves
        return n

def _print_tree(node, depth):
    if node == None:
        return _indent(depth) + "nil\n"

    out = _indent(depth) + nodekind.to_str(node.kind)
    if node.kind in [nodekind.TERMINAL, nodekind.BIN_OPERATOR, nodekind.UNA_OPERATOR]:
        out += " " + node.value.__str__()
    out += "\n"

    i = 0
    while i < len(node.leaves):
        n = node.leaves[i]

        out += _print_tree(n, depth+1)
        i += 1
    return out

def _indent(n):
    i = 0
    out = ""
    while i < n:
        out += "  "
        i += 1
    return out
