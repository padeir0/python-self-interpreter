import lexkind
import nodekind
from lexer import Lexer
from core import Result, Node, Error

def parse(modname, string, track):
    parser = _Parser(Lexer(modname, string))
    if track:
        parser.start_tracking()
    parser.track("parser.parse")
    res = _block(parser)
    if res.failed():
        return res

    if not parser.word_is(lexkind.EOF):
        err = parser.error("unexpected token or symbol")
        return Result(None, err)

    return res

class _Parser:
    def __init__(self, lexer):
        self.lexer = lexer
        self.indent = 0 # numero de espaços
        self.is_tracking = False
        lexer.next() # precisamos popular lexer.word

    def error(self, str):
        return Error(self.lexer.modname, str, self.lexer.word.range.copy())

    def consume(self):
        if self.word_is(lexkind.INVALID):
            err = self.error("invalid character")
            return Result(None, err)
        out = self.lexer.word
        self.lexer.next()
        n = Node(out, nodekind.TERMINAL)
        return Result(n, None)

    def expect(self, kind, str):
        if self.word_is(kind):
            return self.consume()
        err = self.error("expected " + str)
        return Result(None, err)

    def expect_many(self, kinds, text):
        if self.word_is_one_of(kinds):
                return self.consume()
        err = self.error("expected " + text)
        return Result(None, err)

    def expect_prod(self, production, text):
        res = production(self)
        if res.failed():
            return res
        if res.value == None:
            err = self.error("expected " + text)
            return Result(None, err)
        return res
        
    # implements:
    #     Production {operators Production}
    #     where 'operators' are recognized by the predicate
    def repeat_binary(self, production, predicate):
        res = production(self)
        if res.failed() or res.value == None:
            return res

        last = res.value
        while predicate(self):
            res = self.consume()
            if res.failed():
                return res
            parent = res.value
            parent.kind = nodekind.BIN_OPERATOR
            parent.add_leaf(last)

            res = production(self)
            if res.failed():
                return res
            parent.add_leaf(res.value)
            last = parent
        return Result(last, None)

    # implements:
    #     {Production}
    def repeat(self, production):
        list = []
        res = production(self)
        if res.failed() or res.value == None:
            return res

        last = res.value
        while last != None:
            list += [last]

            res = production(self)
            if res.failed():
                return res
            last = res.value
        return Result(list, None)

    # implements:
    #    Production {',' Production} [','].
    def repeat_comma_list(self, production):
        res = production(self)
        if res.failed() or res.value == None:
            return res
        list = [res.value]
        while self.word_is(lexkind.COMMA):
            self.lexer.next()
            res = production(self)
            if res.failed():
                return res
            if res.value == None:
                return Result(list, None)
            list += [res.value]
        return Result(list, None)

    # implements:
    #    Production {[CommaNL] Production} [CommaNL].
    def repeat_multiline_comma_list(self, production):
        res = production(self)
        if res.failed() or res.value == None:
            return res
        list = [res.value]
        while self.word_is(lexkind.COMMA):
            _comma_nl(self)
            res = production(self)
            if res.failed():
                return res
            if res.value == None:
                return Result(list, None)
            list += [res.value]
        return Result(list, None)

    def start_tracking(self):
        self.is_tracking = True

    def track(self, str):
        if self.is_tracking:
            print(str)

    def word_is_one_of(self, kinds):
        return self.lexer.word.kind in kinds

    def word_is(self, kind):
        return self.lexer.word.kind == kind

    def curr_indent(self):
        return self.lexer.word.start_column()

    def same_indent(self, base_indent):
        return self.curr_indent() == base_indent and not self.word_is(lexkind.EOF)

    def indent_prod(self, base_indent, production):
        prev_indent = self.indent
        self.indent = base_indent + 1

        if not self.curr_indent() > self.indent:
            err = self.error("invalid indentation")
            return Result(None, err)

        res = production(self)
        if res.failed():
            return res
        out = res.value
        self.indent = prev_indent
        return Result(out, None)

# Block = { [Statement] NL }.
# Statement = While  | If    | Atrib_Expr
#           | Return | Class | Func
#           | Import | FromImport | Pass.
def _block(parser):
    parser.track("_block")
    statements = []

    base_indent = parser.curr_indent()
    while parser.same_indent(base_indent):
        res = None
        if parser.word_is(lexkind.WHILE):
            res = _while(parser)
        elif parser.word_is(lexkind.IF):
            res = _if(parser)
        elif parser.word_is(lexkind.RETURN):
            res = _return(parser)
        elif parser.word_is(lexkind.FROM):
            res = _from(parser)
        elif parser.word_is(lexkind.IMPORT):
            res = _import(parser)
        elif parser.word_is(lexkind.CLASS):
            res = _class(parser)
        elif parser.word_is(lexkind.PASS):
            res = _pass(parser)
        elif parser.word_is(lexkind.DEF):
            res = _func(parser)
        else:
            res = _atrib_expr(parser)
        if res.failed():
            return res
        sttm = res.value

        if parser.word_is(lexkind.NL):
            res = _NL(parser)
            if res.failed():
                return res

        if sttm != None:
            statements += [sttm]

    block = Node(None, nodekind.BLOCK)
    block.leaves = statements
    return Result(block, None)

# Atrib_Expr = Expr [Assign_Op Expr].
def _atrib_expr(parser):
    parser.track("_atrib_expr")
    res = _expr(parser)
    if res.failed() or res.value == None:
        return res
    lhs = res.value
    if parser.word_is(lexkind.ASSIGN):
        res = parser.consume()
        if res.failed():
            return res
        op = res.value
        res = parser.expect_prod(_expr, "expression on right hand side")
        if res.failed():
            return res
        rhs = res.value
        op.kind = nodekind.ASSIGN
        op.leaves = [lhs, rhs]
        return Result(op, None)
    elif parser.word_is_one_of([lexkind.ASSIGN_PLUS,
                                lexkind.ASSIGN_MINUS,
                                lexkind.ASSIGN_MULT,
                                lexkind.ASSIGN_DIV,
                                lexkind.ASSIGN_REM]):
        res = parser.consume()
        if res.failed():
            return res
        op = res.value
        res = parser.expect_prod(_expr, "expression on right hand side")
        if res.failed():
            return res
        rhs = res.value
        op.kind = nodekind.AUGMENTED_ASSIGN
        op.leaves = [lhs, rhs]
        return Result(op, None)
    return Result(lhs, None)

# While = 'while' Expr ':' NL >Block.
def _while(parser):
    parser.track("_while")
    res = parser.expect(lexkind.WHILE, "'while' keyword")
    if res.failed():
        return res
    kw = res.value

    res = parser.expect_prod(_expr, "expression")
    if res.failed():
        return res
    exp = res.value

    res = parser.expect(lexkind.COLON, "a colon ':'")
    if res.failed():
        return res
    res = _NL(parser)
    if res.failed():
        return res

    res = parser.indent_prod(kw.value.start_column(), _block)
    if res.failed():
        return res
    block = res.value

    n = Node(None, nodekind.WHILE)
    n.leaves = [exp, block]
    return Result(n, None)

# If = 'if' Expr ':' NL >Block {Elif} [Else].
def _if(parser):
    parser.track("_if")

    res = parser.expect(lexkind.IF, "'if' keyword")
    if res.failed():
        return res
    kw = res.value

    res = parser.expect_prod(_expr, "expression")
    if res.failed():
        return res
    exp = res.value

    res = parser.expect(lexkind.COLON, "a colon ':'")
    if res.failed():
        return res
    res = _NL(parser)
    if res.failed():
        return res

    res = parser.indent_prod(kw.value.start_column(), _block)
    if res.failed():
        return res
    block = res.value

    res = _elifs(parser, kw.value.start_column())
    if res.failed():
        return res
    _the_elifs = res.value

    elifs = None
    if _the_elifs != None:
        elifs = Node(None, nodekind.ELIF_LIST)
        elifs.leaves = _the_elifs

    res = _else(parser, kw.value.start_column())
    if res.failed():
        return res
    _the_else = res.value

    n = Node(None, nodekind.IF)
    n.leaves = [exp, block, elifs, _the_else]
    return Result(n, None)

def _elifs(parser, base_indent):
    parser.track("_elifs")
    if not parser.same_indent(base_indent):
        return Result(None, None)

    res = _elif(parser)
    if res.failed() or res.value == None:
        return res
    e = res.value

    elifs = [e]
    while e != None and parser.same_indent(base_indent):
        elifs += [e]

        res = _elif(parser)
        if res.failed():
            return res
        e = res.value

    return Result(elifs, None)

# Elif = 'elif' Expr ':' NL >Block.
def _elif(parser):
    parser.track("_elif")
    if not parser.word_is(lexkind.ELIF):
        return Result(None, None)

    res = parser.expect(lexkind.ELIF, "'elif' keyword")
    if res.failed():
        return res
    kw = res.value

    res = parser.expect_prod(_expr, "expression")
    if res.failed():
        return res
    exp = res.value

    res = parser.expect(lexkind.COLON, "a colon ':'")
    if res.failed():
        return res
    res = _NL(parser)
    if res.failed():
        return res

    res = parser.indent_prod(kw.value.start_column(), _block)
    if res.failed():
        return res
    block = res.value

    n = Node(None, nodekind.ELIF)
    n.leaves = [exp, block]
    return Result(n, None)

# Else = 'else' ':' NL >Block.
def _else(parser, base_indent):
    parser.track("_else")
    if not parser.word_is(lexkind.ELSE):
        return Result(None, None)
    if not parser.same_indent(base_indent):
        return Result(None, None)

    res = parser.expect(lexkind.ELSE, "'else' keyword")
    if res.failed():
        return res
    kw = res.value

    res = parser.expect(lexkind.COLON, "a colon ':'")
    if res.failed():
        return res

    res = _NL(parser)
    if res.failed():
        return res

    res = parser.indent_prod(kw.value.start_column(), _block)
    if res.failed():
        return res
    block = res.value

    n = Node(None, nodekind.ELSE)
    n.leaves = [block]
    return Result(n, None)

# MultiLine_ExprList = Expr {CommaNL Expr} [CommaNL].
def _multiline_expr_list(parser):
    parser.track("_multiline_expr_list")
    res = parser.repeat_multiline_comma_list(_expr)
    if res.failed() or res.value == None:
        return res
    n = Node(None, nodekind.EXPR_LIST)
    n.leaves = res.value
    return Result(n, None)

# ExprList = Expr {',' Expr} [','].
def _expr_list(parser):
    parser.track("_expr_list")
    res = parser.repeat_comma_list(_expr)
    if res.failed() or res.value == None:
        return res
    n = Node(None, nodekind.EXPR_LIST)
    n.leaves = res.value
    return Result(n, None)

# Return = 'return' Expr.
def _return(parser):
    parser.track("_return")
    res = parser.expect(lexkind.RETURN, "'return' keyword")
    if res.failed():
        return res

    res = parser.expect_prod(_expr, "expression")
    if res.failed():
        return res
    expr = res.value

    n = Node(None, nodekind.RETURN)
    n.leaves = [expr]
    return Result(n, None)

def _id(parser):
    if parser.word_is(lexkind.ID):
        return parser.consume()
    return Result(None, None)

# IdList = id {',' id} [','].
def _id_list(parser):
    parser.track("_idlist")
    res = parser.repeat_comma_list(_id)
    if res.failed() or res.value == None:
        return res
    n = Node(None, nodekind.ID_LIST)
    n.leaves = res.value
    return Result(n, None)

# FromImport = 'from' id 'import' IdList.
def _from(parser):
    parser.track("_from")
    res = parser.expect(lexkind.FROM, "'from' keyword")
    if res.failed():
        return res

    res = parser.expect(lexkind.ID, "identifier")
    if res.failed():
        return res
    id = res.value

    res = parser.expect(lexkind.IMPORT, "'import' keyword")
    if res.failed():
        return res

    res = parser.expect_prod(_id_list, "identifier list")
    if res.failed():
        return res
    idlist = res.value

    n = Node(None, nodekind.FROM_IMPORT)
    n.leaves = [id, idlist]
    return Result(n, None)

# Import = 'import' IdList.
def _import(parser):
    parser.track("_import")
    res = parser.expect(lexkind.IMPORT, "'import' keyword")
    if res.failed():
        return res

    res = parser.expect_prod(_id_list, "identifier list")
    if res.failed():
        return res
    idlist = res.value

    n = Node(None, nodekind.IMPORT)
    n.leaves = [idlist]
    return Result(n, None)

# Class = 'class' id ':' NL >Methods.
def _class(parser):
    parser.track("_class")
    res = parser.expect(lexkind.CLASS, "'class' keyword")
    if res.failed():
        return res
    kw = res.value

    res = parser.expect(lexkind.ID, "identifier")
    if res.failed():
        return res
    id = res.value

    res = parser.expect(lexkind.COLON, "a colon ':'")
    if res.failed():
        return res
    res = _NL(parser)
    if res.failed():
        return res

    res = parser.indent_prod(kw.value.start_column(), _methods)
    if res.failed():
        return res
    methods = res.value

    n = Node(None, nodekind.CLASS)
    n.leaves = [id, methods]
    return Result(n, None)

# Methods = {Func}.
def _methods(parser):
    parser.track("_methods")
    methods = []

    base_indent = parser.curr_indent()
    while parser.same_indent(base_indent):
        if not parser.word_is(lexkind.DEF):
            err = parser.error("expected method")
            return Result(None, err)
        res = _func(parser)
        if res.failed():
            return res
        f = res.value

        if parser.word_is(lexkind.NL):
            res = _NL(parser)
            if res.failed():
                return res
        methods += [f]

    n = Node(None, nodekind.METHODS)
    n.leaves = methods
    return Result(n, None)

# Pass = 'pass'.
def _pass(parser):
    parser.track("_pass")
    if parser.word_is(lexkind.PASS):
        res = parser.consume()
        if res.failed():
            return res
        node = res.value
        node.kind = nodekind.PASS
        return Result(node, None)
    return Result(None, None)

# Func = 'def' id Arguments ':' NL >Block.
def _func(parser):
    parser.track("_func")
    res = parser.expect(lexkind.DEF, "'def' keyword")
    if res.failed():
        return res
    kw = res.value

    res = parser.expect(lexkind.ID, "identifier")
    if res.failed():
        return res
    id = res.value

    res = _arguments(parser)
    if res.failed():
        return res
    args = res.value
    
    res = parser.expect(lexkind.COLON, "a colon ':'")
    if res.failed():
        return res
    res = _NL(parser)
    if res.failed():
        return res

    res = parser.indent_prod(kw.value.start_column(), _block)
    if res.failed():
        return res
    block = res.value

    n = Node(None, nodekind.FUNC)
    n.leaves = [id, args, block]
    return Result(n, None)

# Arguments = '(' [NL] [ArgList] ')'.
def _arguments(parser):
    parser.track("_arguments")
    res  = parser.expect(lexkind.LEFT_PAREN, "left parenthesis '('")
    if res.failed():
        return res
    if parser.word_is(lexkind.NL):
        res = _NL(parser)
        if res.failed():
            return res
    res = _arg_list(parser)
    if res.failed():
        return res
    args = res.value

    res = parser.expect(lexkind.RIGHT_PAREN, "right parenthesis ')'")
    if res.failed():
        return res
    return Result(args, None)

# ArgList = Arg {CommaNL Arg} [CommaNL].
def _arg_list(parser):
    parser.track("_arg_list")
    res = parser.repeat_multiline_comma_list(_arg)
    if res.failed() or res.value == None:
        return res
    n = Node(None, nodekind.ARG_LIST)
    n.leaves = res.value
    return Result(n, None)

# Arg = 'self' | id.
def _arg(parser):
    if parser.word_is(lexkind.SELF):
        return parser.consume()
    elif parser.word_is(lexkind.ID):
        return parser.consume()
    else:
        return Result(None, None)

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

    res = parser.repeat(_prefix)
    if res.failed():
        return res
    list = res.value

    # prefixos precisam formar uma arvore de acordo com a precedencia
    if list != None:
        i = 0
        while i < len(list):
            if i+1 < len(list):
                list[i].add_leaf(list[i+1])
            i+=1

    res = _unary_suffix(parser)
    if res.failed():
        return res
    other = res.value

    if list != None and other == None:
        err = parser.error("invalid use of operator without term")
        return Result(None, err)

    if list != None and len(list) > 0:
        first = list[0]
        last = list[len(list)-1]
        last.add_leaf(other)
        return Result(first, None)
    return Result(other, None)

# prefix = 'not' | '-'.
def _prefix(parser):
    parser.track("_prefix")
    if parser.word_is_one_of([lexkind.NOT, lexkind.MINUS]):
        res = parser.consume()
        if res.failed():
            return res
        n = res.value
        n.kind = nodekind.UNA_OPERATOR
        return Result(n, None)
    else:
        return Result(None, None)

# UnarySuffix = Term {Suffix}.
def _unary_suffix(parser):
    parser.track("_unary_suffix")

    res = _term(parser)
    if res.failed() or res.value == None:
        return res
    term = res.value

    res = parser.repeat(_suffix)
    if res.failed():
        return res
    list = res.value

    if list != None:
        # sufixos precisam formar uma arvore de acordo com a precedencia
        i = len(list)-1
        while 0 < i:
            if 0 <= i-1:
                list[i].add_leaf(list[i-1])
            i-=1
        if len(list) > 0:
            first = list[0]
            last = list[len(list)-1]
            first.add_leaf(term)
            return Result(last, None)
    return Result(term, None)

# Suffix = Call
#        | DotAccess
#        | Index.
def _suffix(parser):
    parser.track("_suffix")
    if parser.word_is(lexkind.LEFT_PAREN):
        return _call(parser)
    elif parser.word_is(lexkind.LEFT_BRACKET):
        return _index(parser)
    elif parser.word_is(lexkind.DOT):
        return _dot_access(parser)
    else:
        return Result(None, None)

# Call = '(' [NL] [MultiLine_ExprList] ')'.
def _call(parser):
    parser.track("_call")
    res = parser.expect(lexkind.LEFT_PAREN, "left parenthesis '('")
    if res.failed():
        return res
    if parser.word_is(lexkind.NL):
        res = _NL(parser)
        if res.failed():
            return res
    res = _multiline_expr_list(parser)
    if res.failed():
        return res
    args = res.value

    res = parser.expect(lexkind.RIGHT_PAREN, "right parenthesis ')'")
    if res.failed():
        return res
    n = Node(None, nodekind.CALL)
    n.leaves = [args]
    return Result(n, None)

# Index = '[' [NL] Expr [':' Expr] ']'.
def _index(parser):
    parser.track("_index")
    res = parser.expect(lexkind.LEFT_BRACKET, "lleft bracket '['")
    if res.failed():
        return res
    if parser.word_is(lexkind.NL):
        res = _NL(parser)
        if res.failed():
            return res
    res = parser.expect_prod(_expr, "expression")
    if res.failed():
        return res
    expr_1 = res.value

    expr_2 = None
    if parser.word_is(lexkind.COLON):
        res = parser.consume()
        if res.failed():
            return res
        res = parser.expect_prod(_expr, "expression")
        if res.failed():
            return res
        expr_2 = res.value

    res = parser.expect(lexkind.RIGHT_BRACKET, "right bracket ']'")
    if res.failed():
        return res

    n = None
    if expr_2 != None:
        n = Node(None, nodekind.SLICE)
        n.leaves = [expr_1, expr_2]
    else:
        n = Node(None, nodekind.INDEX)
        n.leaves = [expr_1]
    return Result(n, None)

# DotAccess = '.' id.
def _dot_access(parser):
    parser.track("_dot_access")
    if not parser.word_is(lexkind.DOT):
        return Result(None, None)

    res = parser.consume()
    if res.failed():
        return res
    res = parser.expect(lexkind.ID, "identifier")
    if res.failed():
        return res
    id = res.value

    n = Node(None, nodekind.FIELD_ACCESS)
    n.leaves = [id]
    return Result(n, None)


# Term = 'self' | 'None' | bool | num
#        | str  | id     | NestedExpr_Tuple
#        | Dict | List.
def _term(parser):
    parser.track("_term")
    ok = parser.word_is_one_of([lexkind.SELF,
                        lexkind.NONE,
                        lexkind.TRUE,
                        lexkind.FALSE,
                        lexkind.ID,
                        lexkind.STR,
                        lexkind.NUM])
    if ok:
        return parser.consume()
    elif parser.word_is(lexkind.LEFT_BRACKET):
        return _list(parser)
    elif parser.word_is(lexkind.LEFT_BRACE):
        return _dict(parser)
    elif parser.word_is(lexkind.LEFT_PAREN):
        return _nested_expr(parser)
    else:
        return Result(None, None)

# Dict = '{' [NL] KeyValue_List '}'.
def _dict(parser):
    res = parser.expect(lexkind.LEFT_BRACE, "left brace '{'")
    if res.failed():
        return res
    if parser.word_is(lexkind.NL):
        res = _NL(parser)
        if res.failed():
            return res
    res = _key_value_list(parser)
    if res.failed():
        return res
    kvlist = res.value

    res = parser.expect(lexkind.RIGHT_BRACE, "right brace '}'")
    if res.failed():
        return res

    n = Node(None, nodekind.DICT)
    n.leaves = [kvlist]
    return Result(n, None)

# KeyValue_List = KeyValue_Expr {CommaNL KeyValue_Expr} [CommaNL].
def _key_value_list(parser):
    res = parser.repeat_multiline_comma_list(_key_value_expr)
    if res.failed() or res.value == None:
        return res
    n = Node(None, nodekind.KEY_VALUE_LIST)
    n.leaves = res.value
    return Result(n, None)

# KeyValue_Expr = Expr [':' Expr].
def _key_value_expr(parser):
    res = _expr(parser)
    if res.failed() or res.value == None:
        return res
    key = res.value

    if parser.word_is(lexkind.COLON):
        res = parser.consume()
        if res.failed():
            return res

        res = parser.expect_prod(_expr, "expression")
        if res.failed():
            return res
        value = res.value

        n = Node(None, nodekind.KEY_VALUE_PAIR)
        n.leaves = [key, value]
        return Result(n, None)
    return Result(key, None)

# List = '[' [NL] MultiLine_ExprList ']'.
def _list(parser):
    res = parser.expect(lexkind.LEFT_BRACKET, "left bracket '['")
    if res.failed():
        return res
    if parser.word_is(lexkind.NL):
        res = _NL(parser)
        if res.failed():
            return res
    res = _multiline_expr_list(parser)
    if res.failed():
        return res
    expr_list = res.value
    res = parser.expect(lexkind.RIGHT_BRACKET, "right bracket ']'")
    if res.failed():
        return res
    n = Node(None, nodekind.LIST)
    n.leaves = [expr_list]
    return Result(n, None)

# NestedExpr = '(' Expr ')'.
def _nested_expr(parser):
    res = parser.expect(lexkind.LEFT_PAREN, "left parenthesis '('")
    if res.failed():
        return res

    res = parser.expect_prod(_expr, "expression")
    if res.failed():
        return res
    expr = res.value

    res = parser.expect(lexkind.RIGHT_PAREN, "right parenthesis ')'")
    if res.failed():
        return res

    return Result(expr, None)

# compOp = '==' | '!=' | '>' | '>=' | '<' | '<=' | 'in'.
def _comp_op(parser):
    kinds = [
        lexkind.IN,
        lexkind.EQUALS,
        lexkind.DIFF,
        lexkind.GREATER,
        lexkind.GREATER_OR_EQUALS,
        lexkind.LESS,
        lexkind.LESS_OR_EQUALS,
    ]
    return parser.word_is_one_of(kinds)

def _and_op(parser):
    return parser.word_is_one_of([lexkind.AND])

def _or_op(parser):
    return parser.word_is_one_of([lexkind.OR])

# sumOp = '+' | '-'.
def _sum_op(parser):
    return parser.word_is_one_of([lexkind.PLUS, lexkind.MINUS])

# multOp = '*' | '/' | '%'.
def _mult_op(parser):
    return parser.word_is_one_of([lexkind.MULT, lexkind.DIV, lexkind.REM])

# NL = nl {nl}.
def _NL(parser):
    res = parser.expect(lexkind.NL, "line break")
    if res.failed():
        return res
    _discard_nl(parser)
    return Result(None, None)

def _discard_nl(parser):
    while parser.word_is(lexkind.NL):
        parser.consume()

# CommaNL = ',' [NL].
def _comma_nl(parser):
    if parser.word_is(lexkind.COMMA):
        parser.consume()
        _discard_nl(parser)
