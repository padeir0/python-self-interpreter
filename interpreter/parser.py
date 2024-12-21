import lexkind
import nodekind
from lexer import Lexer
from core import Node, Error

def parse(string, track):
    parser = _Parser(Lexer(string))
    if track:
        parser.start_tracking()
    parser.track("Parse")
    return _expr(parser)

class _Parser:
    def __init__(self, lexer):
        self.lexer = lexer
        self.indent = 0 # numero de espaços
        self.is_tracking = False
        lexer.next() # precisamos popular lexer.word

    def error(self, str):
        return Error(str, self.lexer.word.range.copy())

    def consume(self):
        if self.is_kind(lexkind.INVALID):
            return None, self.error("invalid character")
        out = self.lexer.word
        self.lexer.next()
        return Node(out, nodekind.TERMINAL), None;

    def expect(self, kind, str):
        if self.is_kind(kind):
            return self.consume()
        return None, self.error("expected " + str)

    def expect_many(self, kinds, text):
        for kind in kinds:
            if self.is_kind(kind):
                return self.consume()
        return None, self.error("expected " + text)

    def expect_prod(self, production, text):
        n, err = production(self)
        if err != None:
            return None, err
        if n == None:
            return None, self.error("expected " + text)
        return n, None
        
    # implements:
    #     Production {operators Production}
    #     where 'operators' are recognized by the predicate
    def repeat_binary(self, production, predicate):
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

    # implements:
    #     {Production}
    def repeat(self, production):
        list = []
        last, err = production(self)
        if err != None:
            return None, err
        if last == None:
            return None, None
        while last != None:
            list += [last]

            last, err = production(self)
            if err != None:
                return None, err
        return list, None

    # implements:
    #    Production {',' Production} [','].
    def repeat_comma_list(self, production):
        first, err = production(self)
        if err != None:
            return None, err
        if first == None:
            return None, None
        list = [first]
        while self.is_kind(lexkind.COMMA):
            self.lexer.next()
            n, err = production(self)
            if err != None:
                return None, err
            if n == None:
                return list, None
            list += [n]
        return list, None

    # implements:
    #    Production {[CommaNL] Production} [CommaNL].
    def repeat_multiline_comma_list(self, production):
        first, err = production(self)
        if err != None:
            return None, err
        if first == None:
            return None, None
        list = [first]
        while self.is_kind(lexkind.COMMA):
            _comma_nl(self)
            n, err = production(self)
            if err != None:
                return None, err
            if n == None:
                return list, None
            list += [n]
        return list, None

    def start_tracking(self):
        self.is_tracking = True

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

    def same_indent(self):
        column = self.lexer.word.start_column()
        return column == self.indent

    def strict_indent(self):
        column = self.lexer.word.start_column()
        return column > self.indent

# Block = { Statement NL }.
# Statement = While  | If    | For | Atrib_Expr
#           | Return | Class | Func
#           | Import | FromImport | Pass.
def _block(parser):
    parser.track("_block")
    statements = []
    while parser.same_indent():
        n = None
        err = None
        if parser.is_kind(lexkind.WHILE):
            n, err = _while(parser)
        elif parser.is_kind(lexkind.IF):
            n, err = _if(parser)
        elif parser.is_kind(lexkind.FOR):
            n, err = _for(parser)
        elif parser.is_kind(lexkind.RETURN):
            n, err = _return(parser)
        elif parser.is_kind(lexkind.FROM):
            n, err = _from(parser)
        elif parser.is_kind(lexkind.IMPORT):
            n, err = _import(parser)
        elif parser.is_kind(lexkind.CLASS):
            n, err = _class(parser)
        elif parser.is_kind(lexkind.PASS):
            n, err = _pass(parser)
        elif parser.is_kind(lexkind.DEF):
            n, err = _func(parser)
        else:
            n, err = _expr(parser)
            if n == None:
                return None, parser.Error("expected a statement")
        if err != None:
            return None, err
        statements += [n]
    block = Node(None, nodekind.BLOCK)
    block.leaves = statements
    return block, None

# While = 'while' Expr ':' NL >Block.
def _while(parser):
    parser.track("_while")
    kw, err = parser.expect(lexkind.WHILE, "'while' keyword")
    if err != None:
        return None, err
    exp, err = parser.expect_prod(_expr, "expression")
    if err != None:
        return None, err
    _, err = parser.expect(lexkind.COLON, "a colon ':'")
    if err != None:
        return None, err
    _, err = _NL(parser)
    if err != None:
        return None, err

    prev_indent = parser.indent
    parser.indent = kw.value.start_column() + 1
    block, err = _block(parser)
    if err != None:
        return None, err
    parser.indent = prev_indent

    n = Node(None, nodekind.WHILE)
    n.leaves = [exp, block]
    return n, None

# If = 'if' Expr ':' NL >Block {Elif} [Else].
def _if(parser):
    parser.track("_if")
    kw, err = parser.expect(lexkind.IF, "'if' keyword")
    if err != None:
        return None, err
    exp, err = parser.expect_prod(_expr, "expression")
    if err != None:
        return None, err
    _, err = parser.expect(lexkind.COLON, "a colon ':'")
    if err != None:
        return None, err
    _, err = _NL(parser)
    if err != None:
        return None, err

    prev_indent = parser.indent
    parser.indent = kw.value.start_column() + 1
    block, err = _block(parser)
    if err != None:
        return None, err
    parser.indent = prev_indent

    _the_elifs, err = parser.repeat(_elif)
    if err != None:
        return None, err

    _the_else, err = _else(parser)
    if err != None:
        return None, err

    n = Node(None, nodekind.IF)
    n.leaves = [exp, block, _the_elifs, _the_else]
    return n, None

# Elif = 'elif' Expr ':' NL >Block.
def _elif(parser):
    parser.track("_elif")
    if not parser.is_kind(lexkind.ELIF):
        return None, None

    kw, err = parser.expect(lexkind.ELIF, "'elif' keyword")
    if err != None:
        return None, err
    exp, err = parser.expect_prod(_expr, "expression")
    if err != None:
        return None, err
    _, err = parser.expect(lexkind.COLON, "a colon ':'")
    if err != None:
        return None, err
    _, err = _NL(parser)
    if err != None:
        return None, err

    prev_indent = parser.indent
    parser.indent = kw.value.start_column() + 1
    block, err = _block(parser)
    if err != None:
        return None, err
    parser.indent = prev_indent

    n = Node(None, nodekind.ELIF)
    n.leaves = [exp, block]
    return n, None

# Else = 'else' ':' NL >Block.
def _else(parser):
    parser.track("_else")
    if not parser.is_kind(lexkind.ELSE):
        return None, None
    kw, err = parser.expect(lexkind.ELSE, "'else' keyword")
    if err != None:
        return None, err
    _, err = parser.expect(lexkind.COLON, "a colon ':'")
    if err != None:
        return None, err

    prev_indent = parser.indent
    parser.indent = kw.value.start_column() + 1
    block, err = _block(parser)
    if err != None:
        return None, err
    parser.indent = prev_indent

    n = Node(None, nodekind.ELSE)
    n.leaves = [block]
    return n, None

# For = 'for' id 'in' Expr ':' NL >Block.
# Atrib_Expr = Expr [Assign_Op Expr].
def _for(parser):
    parser.track("_for")
    kw, err = parser.expect(lexkind.FOR, "'for' keyword")
    if err != None:
        return None, err

    id, err = parser.expect(lexkind.ID, "identifier")
    if err != None:
        return None, err

    _, err = parser.expect(lexkind.IN, "'in' keyword")
    if err != None:
        return None, err

    exp, err = parser.expect_prod(_expr, "expression")
    if err != None:
        return None, err

    _, err = parser.expect(lexkind.COLON, "a colon ':'")
    if err != None:
        return None, err
    _, err = _NL(parser)
    if err != None:
        return None, err

    prev_indent = parser.indent
    parser.indent = kw.value.start_column() + 1
    block, err = _block(parser)
    if err != None:
        return None, err
    parser.indent = prev_indent

    n = Node(None, nodekind.FOR)
    n.leaves = [id, exp, block]
    return n, None

# MultiLine_ExprList = Expr {CommaNL Expr} [CommaNL].
def _multiline_expr_list(parser):
    parser.track("_multiline_expr_list")
    list, err = parser.repeat_multiline_comma_list(_expr)
    if err != None:
        return None, err
    if list == None:
        return None, None
    n = Node(None, nodekind.EXPR_LIST)
    n.leaves = list
    return n, None

# ExprList = Expr {',' Expr} [','].
def _expr_list(parser):
    parser.track("_expr_list")
    list, err = parser.repeat_comma_list(_expr)
    if err != None:
        return None, err
    if list == None:
        return None, None
    n = Node(None, nodekind.EXPR_LIST)
    n.leaves = list
    return n, None

# Return = 'return' ExprList.
def _return(parser):
    parser.track("_return")
    _, err = parser.expect(lexkind.RETURN, "'return' keyword")
    if err != None:
        return None, err

    exprlist, err = parser.expect_prod(_expr_list, "expression list")
    if err != None:
        return None, err

    n = Node(None, nodekind.EXPR_LIST)
    n.leaves = [exprlist]
    return n, None

def _id(parser):
    if parser.is_kind(lexkind.ID):
        return parser.consume()
    return None, None

# IdList = id {',' id} [','].
def _id_list(parser):
    parser.track("_idlist")
    list, err = parser.repeat_comma_list(_id)
    if err != None:
        return None, err
    if list == None:
        return None, None
    n = Node(None, nodekind.ID_LIST)
    n.leaves = list
    return n, None

# FromImport = 'from' id 'import' IdList.
def _from(parser):
    parser.track("_from")
    _, err = parser.expect(lexkind.FROM, "'from' keyword")
    if err != None:
        return None, err

    id, err = parser.expect(lexkind.ID, "identifier")
    if err != None:
        return None, err

    _, err = parser.expect(lexkind.IMPORT, "'import' keyword")
    if err != None:
        return None, err

    idlist, err = parser.expect_prod(_id_list, "identifier list")
    if err != None:
        return None, err

    n = Node(None, nodelist.FROM_IMPORT)
    n.leaves = [id, idlist]
    return n

# Import = 'import' IdList.
def _import(parser):
    parser.track("_import")
    _, err = parser.expect(lexkind.IMPORT, "'import' keyword")
    if err != None:
        return None, err

    idlist, err = parser.expect_prod(_id_list, "identifier list")
    if err != None:
        return None, err

    n = Node(None, nodelist.IMPORT)
    n.leaves = [idlist]
    return n

# Class = 'class' id ':' NL >Methods.
def _class(parser):
    parser.track("_class")
    kw, err = parser.expect(lexkind.CLASS, "'class' keyword")
    if err != None:
        return None, err
    id, err = parser.expect(lexkind.ID, "identifier")
    if err != None:
        return None, err
    _, err = parser.expect(lexkind.COLON, "a colon ':'")
    if err != None:
        return None, err
    _, err = _NL(parser)
    if err != None:
        return None, err

    prev_indent = parser.indent
    parser.indent = kw.value.start_column() + 1
    methods, err = _methods(parser)
    if err != None:
        return None, err
    parser.indent = prev_indent

    n = Node(None, nodekind.CLASS)
    n.leaves = [id, methods]
    return n, None

# Methods = {Func}.
def _methods(parser):
    parser.track("_methods")
    methods = []
    while parser.same_indent():
        if not parser.is_kind(lexkind.DEF):
            return None, parser.error("expected method")
        f, err = _func(parser)
        if err != None:
            return None, err
        methods += [f]

    n = Node(None, nodekind.METHODS)
    n.leaves = methods
    return n, None

# Pass = 'pass'.
def _pass(parser):
    parser.track("_pass")
    if parser.is_kind(lexkind.PASS):
        return parser.consume()
    return None, None

# Func = 'def' id Arguments ':' NL >Block.
def _func(parser):
    parser.track("_func")
    kw, err = parser.expect(lexkind.def, "'def' keyword")
    if err != None:
        return None, err
    id, err = parser.expect(lexkind.ID, "identifier")
    if err != None:
        return None, err

    args, err = _arguments(parser)
    if err != None:
        return None, err
    
    _, err = parser.expect(lexkind.COLON, "a colon ':'")
    if err != None:
        return None, err
    _, err = _NL(parser)
    if err != None:
        return None, err

    prev_indent = parser.indent
    parser.indent = kw.value.start_column() + 1
    block, err = _block(parser)
    if err != None:
        return None, err
    parser.indent = prev_indent

    n = Node(None, nodekind.FUNC)
    n.leaves = [id, args, block]
    return n, None

# Arguments = '(' [NL] [ArgList] ')'.
def _arguments(parser):
    parser.track("_arguments")
    _, err = parser.expect(lexkind.LEFT_PAREN, "left parenthesis '('")
    if err != None:
        return None, err
    if parser.is_kind(lexkind.NEWLINE):
        _, err = _NL(parser)
        if err != None:
            return None, err
    args, err = _arglist(parser)
    if err != None:
        return None, err
    _, err = parser.expect(lexkind.RIGHT_PAREN, "right parenthesis ')'")
    if err != None:
        return None, err
    return args, None

# ArgList = Arg {CommaNL Arg} [CommaNL].
def _arg_list(parser):
    parser.track("_arg_list")
    list, err = parser.repeat_multiline_comma_list(_arg)
    if err != None:
        return None, err
    n = Node(None, nodekind.ARG_LIST)
    n.leaves = list
    return n, None

# Arg = 'self' | id.
def _arg(parser):
    if parser.is_kind(lexkind.SELF):
        return parser.consume()
    elif parser.is_kind(lexkind.ID):
        return parser.consume()
    else:
        return None, None

# Expr = And {'or' And}.
def _expr(parser):
    parser.track("_expr")
    return parser.repeat_binary(_and, _or_op)

# And = Comp {'and' Comp}.
def _and(parser):
    parser.track("_and")
    return parser.repeat_binary(_comp, _and_op)

# Comp = Sum {compOp Sum}.
def _comp(parser):
    parser.track("_comp")
    return parser.repeat_binary(_sum, _comp_op)

# Sum = Mult {sumOp Mult}.
def _sum(parser):
    parser.track("_sum")
    return parser.repeat_binary(_mult, _sum_op)

# Mult = UnaryPrefix {multOp UnaryPrefix}.
def _mult(parser):
    parser.track("_mult")
    return parser.repeat_binary(_unary_prefix, _mult_op)

# UnaryPrefix = {Prefix} UnarySuffix.
def _unary_prefix(parser):
    parser.track("_unary_prefix")
    list, err = parser.repeat(_prefix)
    if err != None:
        return None, err

    # prefixos precisam formar uma arvore de acordo com a precedencia
    if list != None:
        i = 0
        while i < len(list):
            if i+1 < len(list):
                list[i].add_leaf(list[i+1])
            i++

    other, err = _unary_suffix(parser)
    if err != None:
        return None, err

    if list != None and other == None:
        return None, parser.error("invalid use of operator without term")

    if list != None and len(list) > 0:
        first = list[0]
        last = list[len(list)-1]
        last.add_leaf(other)
        return first, None
    return other, None

# prefix = 'not' | '-'.
def _prefix(parser):
    parser.track("_prefix")
    if parser.is_kind(lexkind.NOT):
        return parser.consume()
    elif parser.is_kind(lexkind.MINUS):
        return parser.consume()
    else:
        return None, None

# UnarySuffix = Term {Suffix}.
def _unary_suffix(parser):
    parser.track("_unary_suffix")
    term, err = _term(parser)
    if err != None:
        return None, err
    if term == None:
        return None, None

    list, err = parser.repeat(_suffix)
    if err != None:
        return None, err

    if list != None:
        # sufixos precisam formar uma arvore de acordo com a precedencia
        i = len(list)-1
        while 0 < i:
            if 0 < i-1:
                list[i-1].add_leaf(list[i])
            i--
        if len(list) > 0:
            first = list[0]
            last = list[len(list)-1]
            first.add_leaf(term)
            return last, None
    return term, None


# Term = 'self' | 'None' | bool | num
#        | str  | id     | NestedExpr_Tuple
#        | Dict | List.
def _term(parser):
    parser.track("_term")
    if parser.is_kinds(lexkind.SELF,
                       lexkind.NONE,
                       lexkind.TRUE,
                       lexkind.FALSE,
                       lexkind.ID,
                       lexkind.STR,
                       lexkind.NUM):
        return parser.consume()
    elif parser.is_kind(lexkind.LEFT_BRACKET):
        return _nested_expr_tuple(parser)
    elif parser.is_kind(lexkind.LEFT_BRACE):
        return _dict(parser)
    elif parser.is_kind(lexkind.LEFT_PAREN):
        return _list(parser)
    else:
        return None, None

# Dict = '{' [NL] KeyValue_List '}'.
def _dict(parser):
    _, err = parser.expect(lexkind.LEFT_BRACE, "left braces '{'")
    if err != None:
        return None, err
    if parser.is_kind(lexkind.NEWLINE):
        _, err = _NL(parser)
        if err != None:
            return None, err
    kvlist, err = _keyvalue_list(parser)
    if err != None:
        return None, err
    _, err = parser.expect(lexkind.RIGHT_BRACE, "right braces '}'")
    if err != None:
        return None, err
    n = Node(None, nodekind.DICT)
    n.leaves = [kvlist]
    return n, None

# List = '[' [NL] MultiLine_ExprList ']'.
def _list(parser):
    _, err = parser.expect(lexkind.LEFT_BRACKET, "left bracket '['")
    if err != None:
        return None, err
    if parser.is_kind(lexkind.NEWLINE):
        _, err = _NL(parser)
        if err != None:
            return None, err
    expr_list, err = _multiline_expr_list(parser)
    if err != None:
        return None, err
    _, err = parser.expect(lexkind.RIGHT_BRACKET, "right bracket ']'")
    if err != None:
        return None, err
    n = Node(None, nodekind.LIST)
    n.leaves = [expr_list]
    return n, None

# NestedExpr_Tuple = '(' [NL] MultiLine_ExprList ')'.
def _nested_expr_tuple(parser):
    _, err = parser.expect(lexkind.LEFT_PAREN, "left parenthesis '('")
    if err != None:
        return None, err
    if parser.is_kind(lexkind.NEWLINE):
        _, err = _NL(parser)
        if err != None:
            return None, err
    expr_list, err = _multiline_expr_list(parser)
    if err != None:
        return None, err
    _, err = parser.expect(lexkind.RIGHT_BRACKET, "right parenthesis ')'")
    if err != None:
        return None, err

    if len(expr_list.leaves) == 1:
        n = expr_list.leaves[0]
        return n, None
    else:
        n = Node(None, nodekind.TUPLE)
        n.leaves = [expr_list]
        return n, None

# compOp = '==' | '!=' | '>' | '>=' | '<' | '<=' | 'in'.
def _comp_op(parser):
    kinds = [
        lexkind.EQUALS,
        lexkind.DIFF,
        lexkind.GREATER,
        lexkind.GREATER_OR_EQUALS,
        lexkind.LESS,
        lexkind.LESS_OR_EQUALS,
    ]
    return parser.is_kinds(kinds)

def _and_op(parser):
    return parser.is_kinds([lexkind.and])

def _or_op(parser):
    return parser.is_kinds([lexkind.OR])

# sumOp = '+' | '-'.
def _sum_op(parser):
    return parser.is_kinds([lexkind.PLUS, lexkind.MINUS])

# multOp = '*' | '/' | '%'.
def _mult_op(parser):
    return parser.is_kinds([lexkind.MULT, lexkind.DIV, lexkind.REM])

# NL = nl {nl}.
def _NL(parser):
    _, err = parser.expect(lexkind.NEWLINE, "line break")
    if err != None:
        return None, err
    _discard_nl(parser)
    return None, None

def _discard_nl(parser):
    while parser.is_kind(lexkind.NEWLINE):
        parser.consume()

# CommaNL = ',' [NL].
def _comma_nl(parser):
    if parser.is_kind(lexkind.COMMA):
        parser.consume()
        _discard_nl(parser)
