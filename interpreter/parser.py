import lexkind
from lexer import Lexer
from core import Node, Error

class _Parser:
    def __init__(self, lexer):
        self.lexer = lexer
        self.indent = 0
        self.is_tracking = False
        lexer.next() # precisamos popular lexer.word

    def error(self, str):
        return Error(str, self.lexer.word.range.copy())

    def consume(self):
        if self.lexer.word.kind == lexkind.INVALID:
            return None, self.error("invalid character")
        out = self.lexer.word
        self.lexer.next()
        return Node(out), None;
        
    # implements:
    #     <prod> {<op> <prod>}
    #     where <op> is recognized by the predicate
    def repeatBinary(self, production, predicate):
        last, err = production(self)
        if err != None:
            return None, err
        if last == None:
            return None, None
        while predicate(self):
            parent, err = self.consume()
            if err != None:
                return None, err
            parent.addLeaf(last)

            newLeaf, err = production(self)
            if err != None:
                return None, err
            parent.addLeaf(newLeaf)
            last = parent
        return last, None

    def start_tracking(self):
        self.is_tracking = true

    def track(self, str):
        if self.is_tracking:
            print(str)

    def is_kinds(self, kinds):
        for kind in kinds:
            if self.lexer.word.kind == kind:
                return True
        return False

    def is_kind(self, kind):
        return self.lexer.word.kind == kind

def _sumOp(parser):
    return parser.is_kinds([lexkind.PLUS, lexkind.MINUS])

def _multOp(parser):
    return parser.is_kinds([lexkind.MULT, lexkind.DIV])

def _expr(parser):
    parser.track("_expr")
    return parser.repeatBinary(_mult, _sumOp)

def _mult(parser):
    parser.track("_mult")
    return parser.repeatBinary(_unary, _multOp)

def _unary(parser):
    parser.track("_unary")
    parent = None
    if parser.is_kind(lexkind.MINUS):
        parent, err = parser.consume()
        if err != None:
            return None, err

    n, err = _term(parser)
    if err != None:
        return None, err

    if parent != None:
        parent.addLeaf(n)
        return parent, None
    return n, None

def _term(parser):
    parser.track("_term")
    if parser.is_kind(lexkind.NUM):
        return parser.consume()
    elif parser.is_kind(lexkind.LEFT_PAREN):
        return _nestedExpr(parser)
    else:
        return None, parser.error("unexpected token in term")

def _nestedExpr(parser):
    parser.track("_nestedExpr")
    _discard, err = parser.consume()
    if err != None:
        return None, err
    if _discard.value.kind != lexkind.LEFT_PAREN:
        return None, parser.error("bad use of _nestedExpr")

    exp, err = _expr(parser)
    if err != None:
        return None, err

    _discard, err = parser.consume()
    if err != None:
        return None, err
    if _discard.value.kind != lexkind.RIGHT_PAREN:
        return None, parser.error("expected closing parenthesis in expression")

    return exp, None

def parse(string, track):
    parser = _Parser(Lexer(string))
    if track:
        parser.start_tracking()
    parser.track("Parse")
    return _expr(parser)
