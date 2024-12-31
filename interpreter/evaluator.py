from core import Result, Error, Node
from parser import parse
import lexkind
import nodekind
import objkind
import scopekind

# Considerations:
# - All built-in functions must be implemented using CPython's built-in functions.
# - `print` takes a single argument (no varags) and uses __str__ method if present

class _Builtin_Func:
    def __init__(self, num_args, wrapper):
        self.num_args = num_args
        self.wrapper = wrapper
    def call(self, args):
        if len(args) != self.num_args:
            return Error("invalid number of arguments", None)
        if self.num_args == 1:
            self.wrapper(args[0])
        elif self.num_args == 2:
            self.wrapper(args[0], args[1])
        elif self.num_args == 3:
            self.wrapper(args[0], args[1], args[2])
        else:
            return Error("too many arguments", None)
        return None

# implementamos métodos passando um escopo onde o "self"
# é uma variável respresentando a instancia do objeto
class _User_Function:
    def __init__(self, name, formal_args, block, parent_scope):
        self.name = name
        self.block = block
        # lista dos nomes dos argumentos
        self.formal_args = formal_args
        # toda função captura o ambiente que ela ta inserida,
        # ie, é uma closure
        self.parent_scope = parent_scope

    def call(self, ctx, args):
        if len(args) != len(self.formal_args):
            return Error("invalid number of arguments", None)

        s = _Scope(self.parent_scope, scopekind.FUNCTION)
        ctx.push_env(s)

        i = 0
        while i < len(args):
            name = self.formal_args[i]
            obj = args[i]
            s.add_symbol(name, obj)
            i += 1

        err = _eval_block(ctx, self.block)
        if err != None:
            return err

        ctx.pop_env()
        return None
    
class _User_Object_Template:
    def __init__(self, name, node, methods):
        self.name = name
        self.node = node
        self.methods = methods
    # preenche self.value usando a logica do __init__ criado pelo usuario
    # emite um erro se não existir __init__
    def eval_init(self, ctx, args):
        instance = _User_Object_Instance(self)
        if "__init__" in obj.methods:
            func = instance.get_method("__init__")
            news = _Scope(func.parent, scopekind.FUNC)
            news.add_symbol("self", instance)
            func.parent = news
            func.call(ctx, args)
            return Result(instance, None)
        else:
            err = Error("object has no __init__ procedure", None)
            return Result(None, err)

class _User_Object_Instance:
    def __init__(self, template):
        # dicionario de tipo str->_Py_Object que contém as propriedades
        # do objeto
        self.properties = None
        # dicionario de tipo str->_User_Function que contém os métodos
        # do objeto
        self.methods = template.methods
        self.class_name = template.name

    def get_method(self, name):
        if name in self.methods:
            return Result(self.methods[name], None)
        else:
            return Result(None, True)
    
    # retorna um atributo do objeto
    def get_attr(self, attr_name):
        if attr_name in self.properties:
            return Result(self.properties[attr_name], None)
        else:
            return Result(None, True)

    def create_attr(self, attr_name):
        self.properties[attr_name] = _Py_Object(objkind.NONE, None, False)
        return self.properties[attr_name]

class _Module:
    def __init__(self, name, mod_scope):
        self.name = name
        self.scope = mod_scope

    def get_global(self, name):
        if self.scope.contains(name):
            return self.scope.retrieve(name)
        err = Error("name '"+name+"' is not part of module"+self.name, None)
        return Result(None, err)

class _Py_Object:
    def __init__(self, kind, value, mutable):
        self.kind = kind
        self.value = value
        self.mutable = mutable
    def copy(self):
        value = self.value
        return _Py_Object(self.kind, value, self.mutable)
    def is_kind(self, kind):
        return self.kind == kind
    def is_kinds(self, kinds):
        i = 0
        while i < len(kinds):
            if self.kind == kinds[i]:
                return True
            i += 1
        return False
    def is_hashable(self):
        kinds = [
            objkind.BOOL, objkind.NUM, objkind.STR,
            objkind.USER_OBJECT, objkind.USER_FUNCTION,
            objkind.BUILTIN_FUNC, objkind.NONE,
            objkind.MODULE,
        ]
        return self.is_kinds(kinds)
    def set(self, kind, value):
        self.kind = kind
        self.value = value

class _Scope:
    def __init__(self, parent, kind):
        # é necessário diferenciar entre escopos de função
        # e escopos de módulo
        self.kind = kind
        self.parent = parent
        self.dict = {}
    def add_symbol(self, name, obj):
        self.dict[name] = obj
    def set_symbol(self, name, obj):
        if name in self.dict:
            self.dict[name] = obj
            return True
        else:
            return False
    def contains(self, name):
        return name in self.dict
    def retrieve(self, name):
        if name in self.dict:
            return Result(self.dict[name], None)
        elif self.parent != None:
            return self.parent.retrieve(name)
        else:
            err = Error("name '"+name+"' not found", None)
            return Result(None, err)

# _Call_Node define um nó numa pilha de chamada
class _Call_Node:
    def __init__(self, parent, scope):
        # toda função tem um escopo, podendo variar apenas localmente (no escopo de função)
        # ou globalmente (no escopo de módulo), por isso é necessário que esse campo esteja
        # presente e aponte para o escopo onde a função foi declarada
        self.curr_scope = scope
        # preenchido por qualquer função chamada dentro desse contexto
        self.return_obj = None
        # ao retornar de uma função, é necessário ter acesso ao contexto pai
        self.parent = parent

class _Context:
    def __init__(self, source_map, call_node, builtin_scope):
        self.builtin_scope = builtin_scope
        self.source_map = source_map
        self.curr_call_node = call_node
        self.evaluated_mods = {}

    def push_env(self, scope):
        next = _Call_Node(self.curr_call_node, scope)
        self.curr_call_node = next

    def pop_env(self):
        self.curr_call_node = self.curr_call_node.parent

    def curr_scope(self):
        return self.curr_call_node.curr_scope

    def contains_symbol(self, name):
        return self.curr_call_node.curr_scope.contains(name)

    def retrieve(self, name):
        return self.curr_call_node.curr_scope.retrieve(name)

    def add_symbol(self, name, obj):
        self.curr_call_node.curr_scope.add_symbol(name, obj)

    def set_symbol(self, name, obj):
        return self.curr_call_node.curr_scope.set_symbol(name, obj)

    def set_mod(self, mod_name, mod):
        self.evaluated_mods[mod_name] = mod

    def get_mod(self, mod_name):
        if mod_name in self.evaluated_mods:
            return self.evaluated_mods[mod_name]
        return None

    def get_return(self):
        return self.curr_call_node.return_obj

    def set_return(self, obj):
        if self.curr_call_node.parent == None:
            return Error("invalid return (outside function?)", None)
        self.curr_call_node.parent.return_obj = obj
        return None

def _check_unif_bin(node, left_obj, right_obj):
    if left_obj.kind != right_obj.kind:
        return Error("objects have different types", node.range.copy())
    return None

def _check_unif_bin_types(node, left_obj, right_obj, typelist):
    if left_obj.kind != right_obj.kind:
        return Error("objects have different types", node.range.copy())
    if not left_obj.is_kinds(typelist):
        msg = "invalid operation on object of type: " + objkind.to_str(left_obj.kind)
        return Error(msg, node.range.copy())
    return None

def _eval_arith(left_obj, right_obj, node):
    err = _check_unif_bin_types(node, left_obj, right_obj, [objkind.NUM])
    if err != None:
        return Result(None, err)

    out = None
    if node.has_lexkind(lexkind.MINUS):
        out = left_obj.value - right_obj.value
    elif node.has_lexkind(lexkind.MULT):
        out = left_obj.value * right_obj.value
    elif node.has_lexkind(lexkind.DIV):
        if right_obj.value == 0:
            err = Error("division by zero", node.range.copy())
            return Result(None, err)
        out = left_obj.value / right_obj.value
    elif node.has_lexkind(lexkind.REM):
        if right_obj.value == 0:
            err = Error("division by zero", node.range.copy())
            return Result(None, err)
        out = left_obj.value % right_obj.value
    obj = _Py_Object(objkind.NUM, out, False)
    return Result(obj, None)

def _eval_identity(left_obj, right_obj, node):
    err = _check_unif(node, left_obj, right_obj)
    if err != None:
        return Result(None, err)

    out = None
    if node.has_lexkind(lexkind.EQUALS):
        out = left_obj.value == right_obj.value
    elif node.has_lexkind(lexkind.DIFF):
        out = left_obj.value != right_obj.value
    obj = _Py_Object(objkind.BOOL, out, False)
    return Result(obj, None)

def _eval_order(left_obj, right_obj, node):
    err = _check_unif_bin_types(node, left_obj, right_obj, [objkind.NUM])
    if err != None:
        return Result(None, err)

    out = None
    if node.has_lexkind(lexkind.GREATER):
        out = left_obj.value > right_obj.value
    elif node.has_lexkind(lexkind.GREATER_OR_EQUALS):
        out = left_obj.value >= right_obj.value
    elif node.has_lexkind(lexkind.LESS):
        out = left_obj.value < right_obj.value
    elif node.has_lexkind(lexkind.LESS_OR_EQUALS):
        out = left_obj.value <= right_obj.value

    obj = _Py_Object(objkind.BOOL, out, False)
    return Result(obj, None)

def _eval_or(left_obj, right_obj, node):
    err = _check_unif_bin_types(node, left_obj, right_obj, [objkind.BOOL])
    if err != None:
        return Result(None, err)
    out = left_obj.value or right_obj.value
    obj = _Py_Object(objkind.BOOL, out, False)
    return Result(obj, None)

def _eval_and(left_obj, right_obj, node):
    err = _check_unif_bin_types(node, left_obj, right_obj, [objkind.BOOL])
    if err != None:
        return Result(None, err)
    out = left_obj.value and right_obj.value
    obj = _Py_Object(objkind.BOOL, out, False)
    return Result(obj, None)

def _eval_plus(left_obj, right_obj, node):
    kinds = [objkind.NUM, objkind.LIST, objkind.STR]
    err = _check_unif_bin_types(node, left_obj, right_obj, kinds)
    if err != None:
        return Result(None, err)

    out = left_obj.value + right_obj.value
    obj = _Py_Object(left_obj.kind, out, False)
    return Result(obj, None)

def _eval_in(left_obj, right_obj, node):
    if not left_obj.is_hashable():
        err = Error("object is not hashable", node.left().range.copy())
        return Result(None, err)

    if not right_obj.is_kind(objkind.DICT):
        err = Error("object is not a dictionary", node.right().range.copy())
        return Result(None, err)

    out = left_obj.value in right_obj.value
    obj = _Py_Object(objkind.BOOL, out, False)
    return Result(obj, None)

def _eval_bin_operator(ctx, node):
    left = node.leaves[0]
    right = node.leaves[1]

    res = _eval_expr(ctx, left)
    if res.failed():
        return res
    left_obj = res.value

    res = _eval_expr(ctx, right)
    if res.failed():
        return res
    right_obj = res.value

    arith = [lexkind.MINUS, lexkind.MULT, lexkind.DIV, lexkind.REM]
    identity = [lexkind.EQUALS, lexkind.DIFF]
    order = [lexkind.GREATER, lexkind.GREATER_OR_EQUALS, lexkind.LESS, lexkind.LESS_OR_EQUALS]
    
    if node.has_lexkind(lexkind.AND):
        return _eval_and(left_obj, right_obj, node)
    elif node.has_lexkind(lexkind.OR):
        return _eval_or(left_obj, right_obj, node)
    elif node.has_lexkind(lexkind.IN):
        return _eval_in(left_obj, right_obj, node)
    elif node.has_lexkind(lexkind.PLUS):
        return _eval_plus(left_obj, right_obj, node)
    elif node.has_lexkinds(arith):
        return _eval_arith(left_obj, right_obj, node)
    elif node.has_lexkinds(identity):
        return _eval_identity(left_obj, right_obj, node)
    elif node.has_lexkinds(order):
        return _eval_order(left_obj, right_obj, node)
    else:
        err = Error("invalid lexkind for binary operator", node.range.copy())
        return Result(None, err)

def _eval_una_operator(ctx, node):
    operand = node.leaves[0]
    res = _eval_expr(ctx, operand)
    if res.failed():
        return res
    obj = res.value
    if node.has_lexkind(lexkind.NOT):
        if obj.is_kind(objkind.BOOL):
            new_value = not obj.value
            obj = _Py_Object(objkind.BOOL, new_value, False)
            return Result(obj, None)
        else:
            err = Error("object is not a boolean", operand.range.copy())
            return Result(None, err)
    elif node.has_lexkind(lexkind.MINUS):
        if obj.is_kind(objkind.NUM):
            new_value = -obj.value
            obj = _Py_Object(objkind.NUM, new_value, False)
            return Result(obj, None)
        else:
            err = Error("object is not a number", operand.range.copy())
            return Result(None, err)
    else:
        err = Error("invalid lexkind for unary operator", node.range.copy())
        return Result(None, err)

def _eval_terminal(ctx, node):
    obj = None
    if node.has_lexkind(lexkind.TRUE):
        obj = _Py_Object(objkind.BOOL, True, False)
    elif node.has_lexkind(lexkind.FALSE):
        obj = _Py_Object(objkind.BOOL, False, False)
    elif node.has_lexkind(lexkind.NONE):
        obj = _Py_Object(objkind.NONE, None, False)
    elif node.has_lexkind(lexkind.ID) or node.has_lexkind(lexkind.SELF):
        name = node.value.text
        res = ctx.retrieve(name)
        if res.failed():
            err = res.error
            err.range = node.range.copy()
            return Result(None, err)
        obj = res.value
    elif node.has_lexkind(lexkind.STR):
        obj = _Py_Object(objkind.STR, node.value.text, False)
    elif node.has_lexkind(lexkind.NUM):
        obj = _Py_Object(objkind.NUM, int(node.value.text), False)
    else:
        err = Error("invalid lexkind for terminal", node.range.copy())
        return Result(None, err)
    return Result(obj, None)

def _eval_dict(ctx, node):
    kvlist = node.leaves[0]
    i = 0
    out = {}
    while i < len(kvlist.leaves):
        kvpair = kvlist.leaves[i]
        key_expr = kvpair.leaves[0]
        value_expr = kvpair.leaves[1]

        res = _eval_expr(ctx, key_expr)
        if res.failed():
            return res
        key = res.value

        res = _eval_expr(ctx, value_expr)
        if res.failed():
            return res
        value = res.value

        if not key.is_hashable():
            err = Error("object is not hashable", key_expr.range.copy())
            return Result(None, err)

        out[key] = value
        i += 1

    obj = _Py_Object(objkind.DICT, out, False)
    return Result(obj, None)

def _eval_list(ctx, node):
    exprlist = node.leaves[0]
    i = 0
    out = []
    while i < len(exprlist.leaves):
        expr = exprlist.leaves[i]
        res = _eval_expr(ctx, expr)
        if res.failed():
            return res
        item = res.value
        out += [item]
        i += 1
    obj = _Py_Object(objkind.LIST, out, False)
    return Result(obj, None)

def _eval_special_call_int(ctx, exprlist):
    if len(exprlist.leaves) != 1:
        err = Error("invalid number of arguments, expected 1", exprlist.range.copy())
        return Result(None, err)
    res = _eval_expr(ctx, exprlist.leaves[0])
    if res.failed():
        return res
    obj = res.value

    if obj.is_kind(objkind.STR):
        num = int(obj.value)
        new_obj = _Py_Object(objkind.NUM, num, False)
        return Result(new_obj, None)
    else:
        err = Error("invalid type for int() call", exprlist.range.copy())
        return Result(None, err)

def _eval_special_call_len(ctx, exprlist):
    if len(exprlist.leaves) != 1:
        err = Error("invalid number of arguments, expected 1", exprlist.range.copy())
        return Result(None, err)

    res = _eval_expr(ctx, exprlist.leaves[0])
    if res.failed():
        return res
    obj = res.value

    if obj.is_kinds([objkind.STR, objkind.LIST]):
        num = len(obj.value)
        new_obj = _Py_Object(objkind.NUM, num, False)
        return Result(new_obj, None)
    else:
        err = Error("invalid type for len() call", exprlist.range.copy())
        return Result(None, err)

# SPECIAL_CASES:
#     int(<str>)
#     len(<list>)
def _eval_call(ctx, node):
    exprlist = node.leaves[0]
    callee = node.leaves[1]

    if callee.kind == nodekind.TERMINAL and callee.has_lexkind(lexkind.ID):
        name = callee.value.text
        if name == "int":
            return _eval_special_call_int(ctx, exprlist)
        elif name == "len":
            return _eval_special_call_len(ctx, exprlist)

    res = _eval_expr(ctx, callee)
    if res.failed():
        return res
    thing = res.value

    args = []
    i = 0
    while i < len(exprlist.leaves):
        expr = exprlist.leaves[i]

        res = _eval_expr(ctx, expr)
        if res.failed():
            return res
        args += [res.value]
        i += 1

    if thing.is_kind(objkind.USER_FUNCTION):
        err = thing.value.call(ctx, args)
        if err != None:
            err.range = exprlist.range.copy()
            return Result(None, err)
        obj = ctx.get_return()
        return Result(obj, None)
    elif thing.is_kind(objkind.BUILTIN_FUNC):
        err = thing.value.call(args)
        obj = ctx.get_return()
        return Result(obj, err)
    elif thing.is_kind(objkind.USER_CLASS):
        res = thing.value.eval_init(args)
        if res.failed():
            res.error.range = callee.range.copy()
        obj = res.value
        return Result(obj, err)
    else:
        err = Error("object is not callable", callee.range.copy())
        return Result(None, err)

def _eval_field_access(ctx, node):
    field = node.leaves[0]
    operand = node.leaves[1]
    res = _eval_expr(ctx, operand)
    if res.failed():
        return res
    obj = res.value

    if obj.is_kinds([objkind.STR, objkind.DICT, objkind.NUM,
                     objkind.LIST, objkind.USER_FUNCTION,
                     objkind.BUILTIN_FUNC]):
        err = Error("object has no properties", operand.range.copy())
        return Result(None, err)

    name = field.value.text
    if obj.is_kinds([objkind.MODULE]):
        res = obj.value.get_global(name)
        if res.failed():
            res.error.range = field.range.copy()
            return res
        return Result(res.value, None)
    elif obj.is_kind([objkind.USER_OBJECT]):
        if name in obj.value.methods:
            func = obj.value.get_method(name)
            news = _Scope(func.parent, scopekind.FUNC)
            news.add_symbol("self", obj)
            func.parent = news
            obj = _Py_Object(objkind.FUNC, func, False)
        elif name in obj.value.properties:
            obj = obj.value.get_attr(name)
        else:
            err = Error("property not found", field.range.copy())
            return Result(err, None)
        return Result(obj, None)
    else:
        err = Error("object has invalid type", obj.range.copy())
        return Result(None, err)

def _eval_index(ctx, node):
    operand = node.leaves[1]
    expr = node.leaves[0]

    res = _eval_expr(ctx, operand)
    if res.failed():
        return res
    obj = res.value

    res = _eval_expr(ctx, expr)
    if res.failed():
        return res
    index = res.value

    if obj.is_kind(objkind.DICT):
        if index.is_hashable():
            if index.value in obj.value:
                obj = obj.value[index.value]
                return Result(obj, None)
            else:
                err = Error("key not found", expr.range.copy())
                return Result(None, err)
        else:
            err = Error("object not hashable", expr.range.copy())
            return Result(None, err)
    elif obj.is_kinds([objkind.LIST, objkind.STR]):
        if index.is_kind(objkind.NUM):
            obj = obj.value[index.value]
            return Result(obj, None)
        else:
            err = Error("index is not a number", expr.range.copy())
    else:
        msg = "unexpected type for indexing: " + objkind.to_str(obj.kind)
        err = Error(msg, operand.range.copy())
        return Result(None, err)

def _eval_slice(ctx, node):
    begin_expr = node.leaves[0]
    end_expr = node.leaves[1]
    operand_expr = node.leaves[2]

    res = _eval_expr(ctx, operand_expr)
    if res.failed():
        return res
    obj = res.value

    res = _eval_expr(ctx, begin_expr)
    if res.failed():
        return res
    begin = res.value

    res = _eval_expr(ctx, end_expr)
    if res.failed():
        return res
    end = res.value

    if not begin.is_kind(objkind.NUM):
        err = Error("expected an integer", begin_expr.range.copy())
        return Result(None, err)
    if not end.is_kind(objkind.NUM):
        err = Error("expected an integer", end_expr.range.copy())
        return Result(None, err)
    if not obj.is_kinds([objkind.LIST, objkind.STR]):
        err = Error("expected a list or string", operand_expr.range.copy())
        return Result(None, err)

    if begin.value < 0 or begin.value > len(obj.value):
        err = Error("out of bounds", begin_expr.range.copy())
        return Result(None, err)
    elif end.value < 0 or end.value > len(obj.value):
        err = Error("out of bounds", end_expr.range.copy())
        return Result(None, err)

    out = obj.value[begin.value:end.value]
    out_obj = _Py_Object(obj.kind, out, False)
    return Result(out_obj, None)
    
def _eval_expr(ctx, node):
    if node.kind == nodekind.BIN_OPERATOR:
        return _eval_bin_operator(ctx, node)
    elif node.kind == nodekind.UNA_OPERATOR:
        return _eval_una_operator(ctx, node)
    elif node.kind == nodekind.TERMINAL:
        return _eval_terminal(ctx, node)
    elif node.kind == nodekind.DICT:
        return _eval_dict(ctx, node)
    elif node.kind == nodekind.LIST:
        return _eval_list(ctx, node)
    elif node.kind == nodekind.CALL:
        return _eval_call(ctx, node)
    elif node.kind == nodekind.INDEX:
        return _eval_index(ctx, node)
    elif node.kind == nodekind.FIELD_ACCESS:
        return _eval_field_access(ctx, node)
    elif node.kind == nodekind.SLICE:
        return _eval_slice(ctx, node)
    else:
        err = Error("invalid expression", node.range.copy())
        return Result(None, err)

def _eval_import(ctx, node):
    i = 0
    while i < len(node.leaves):
        leaf = node.leaves[i]
        name = leaf.value.text

        mod = ctx.get_mod()
        if mod == None:
            res = _eval_module(ctx, name)
            if res.failed():
                if res.error.range == None:
                    res.error.range = node.range.copy()
                return res.error()
            mod = res.value
            obj = _Py_Object(mod, objkind.MODULE, False)
            ctx.add_symbol(name, obj)
            ctx.set_mod(name, mod)
        else:
            obj = _Py_Object(mod, objkind.MODULE, False)
            ctx.add_symbol(name, obj)
        i += 1
    return None

def _eval_from(ctx, node):
    id = node.leaves[0]
    idlist = node.leaves[1]

    name = id.value.text
    mod = ctx.get_mod(name)
    if mod == None:
        res = _eval_module(ctx, name)
        if res.failed():
            if res.error.range == None:
                res.error.range = node.range.copy()
            return res.error
        mod = res.value

    i = 0
    while i < len(idlist.leaves):
        leaf = node.leaves[i]
        name = leaf.value.text
        if mod.scope.contains(name):
            res = mod.scope.retrieve(name)
            cpy = res.value.copy()
            cpy.mutable = False
            ctx.add_symbol(name, cpy)
        else:
            return Error("symbol not found in module", leaf.range.copy())
        i += 1
    return None

def _extract_names(arg_list):
    i = 0
    out = []
    while i < len(arg_list):
        arg = arg_list[i]
        out += [arg.value.text]
        i += 1

    return out

def _eval_func(ctx, node):
    id = node.leaves[0]
    args = node.leaves[1]
    block = node.leaves[2]

    name = id.value.text
    arg_names = _extract_names(args.leaves)

    func = _User_Function(name, arg_names, block, ctx.curr_scope())
    obj = _Py_Object(objkind.USER_FUNCTION, func, False)
    ctx.add_symbol(name, obj)
    return None

def _eval_lhs_index(ctx, lhs):
    list = lhs.leaves[1]
    index_expr = lhs.leaves[0]

    res = _eval_expr(ctx, list)
    if res.failed():
        return res
    obj = res.value

    if not obj.mutable:
        err = Error("object is not mutable", list.range.copy())
        return Result(None, err)

    res = _eval_expr(ctx, index_expr)
    if res.failed():
        return res
    index_val = res.value

    out = None
    if obj.is_kind(objkind.MAP):
        out = obj.value[index_val.value]
    elif obj.is_kind(objkind.LIST) and index_val.is_kind(objkind.NUM):
        out = obj.value[index_val.value]
    else:
        err = Error("invalid indexing expression", lhs.range.copy())
        return Result(None, err)

    if not out.mutable:
        err = Error("object is not mutable", lhs.range.copy())
        return Result(None, err)

    return Result(out, None)

def _eval_lhs_field_access(ctx, lhs):
    op = lhs.leaves[1]
    field = lhs.leaves[0]

    if field.kind != nodekind.TERMINAL or field.value != lexkind.ID:
        err = Error("field must be an identifier", field.range.copy())
        return Result(None, err)

    res = _eval_expr(ctx, op)
    if res.failed():
        return res
    obj = res.value

    if obj.is_kinds([objkind.STR, objkind.DICT, objkind.NUM,
                     objkind.LIST, objkind.USER_FUNCTION,
                     objkind.BUILTIN_FUNC]):
        err = Error("object has no properties", obj.range.copy())
        return Result(None, err)

    if obj.is_kinds([objkind.MODULE]):
        err = Error("object is not mutable", lhs.range.copy())
        return Result(None, err)

    if obj.is_kind([objkind.USER_OBJECT]):
        name = field.value.text
        if name in obj.value.methods:
            err = Error("methods are not mutable", field.range.copy())
            return Result(None, err)
        elif name in obj.value.properties:
            obj = obj.value.get_attr(name)
        else:
            obj = obj.value.create_attr(name)
        return Result(obj, None)
    else:
        err = Error("object has invalid type", obj.range.copy())
        return Result(None, err)

# O lado esquerdo deve obedecer uma semantica mais estrita que o direito,
# por necessitar ter um objeto atribuivel.
# A função eval_lhs retorna um _Py_Object, esse, por ser passado por
# referência, pode ser atribuido futuramente.
def _eval_lhs(ctx, lhs):
    if lhs.kind == nodekind.TERMINAL and lhs.value.kind == lexkind.ID:
        name = lhs.value.text
        if not ctx.contains_symbol(name):
            newnone = _Py_Object(objkind.NONE, None, False)
            ctx.add_symbol(name, newnone)
        res = ctx.retrieve(name)
        if res.failed():
            return res
        obj = res.value
        return Result(obj, None)
    elif lhs.kind == nodekind.INDEX:
        return _eval_lhs_index(ctx, lhs)
    elif lhs.kind == nodekind.FIELD_ACCESS:
        return _eval_lhs_field_access(ctx, lhs)
    else:
        err = Error("expression is not assignable", lhs.range.copy())
        return Result(None, err)

def _eval_assign(ctx, node):
    lhs = node.leaves[0]
    rhs = node.leaves[1]

    res = _eval_lhs(ctx, lhs)
    if res.failed():
        return res.error
    obj = res.value

    res = _eval_expr(ctx, rhs)
    if res.failed():
        return res.error
    exp = res.value

    obj.set(exp.kind, exp.value)
    return None

def _extract_method_args(arg_list):
    i = 0
    out = []
    while i < len(arg_list):
        arg = arg_list[i]
        if not arg.has_lexkind(lexkind.SELF):
            out += [arg.value.text]
        i += 1

    return out

def _eval_method(ctx, node):
    id = node.leaves[0]
    args = node.leaves[1]
    block = node.leaves[2]

    name = id.value.text
    arg_names = _extract_method_args(args.leaves)

    return _User_Function(name, arg_names, block, ctx.curr_scope())

def _eval_declare_class(ctx, node):
    id = node.leaves[0]
    met_node = node.leaves[1]

    methods = {}
    i = 0
    while i < len(met_node.leaves):
        method = _eval_method(ctx, met_node.leaves[i])
        methods[method.name] = method
        i += 1

    name = id.value.text
    value = _User_Object_Template(name, node, methods)
    obj = _Py_Object(objkind.USER_CLASS, value, False)

    ctx.add_symbol(name, obj)
    return None

def _eval_return(ctx, node):
    expr = node.leaves[0]

    res = _eval_expr(ctx, expr)
    if res.failed():
        return res.error
    obj = res.value

    err = ctx.set_return(obj)
    if err != None:
        err.range = node.range.copy()
    return err

def _check_unif_aug_ass_types(node, left_obj, right_obj, typelist):
    if left_obj.kind != right_obj.kind:
        return Error("objects have different types", node.range.copy())
    if not left_obj.is_kinds(typelist):
        msg = "invalid operation on object of type: " + objkind.to_str(left_obj.kind)
        return Error(msg, node.range.copy())
    return None

def _eval_aug_assign(ctx, node):
    lhs_expr = node.leaves[0]
    rhs_expr = node.leaves[1]

    res = _eval_lhs(ctx, lhs_expr)
    if res.failed():
        return res.error
    lhs_obj = res.value

    res = _eval_expr(ctx, rhs_expr)
    if res.failed():
        return res.error
    rhs_obj = res.value

    if node.has_lexkind(lexkind.ASSIGN_PLUS): # list, num, str
        kinds = [objkind.LIST, objkind.NUM, objkind.STR]
        err = _check_unif_aug_ass_types(node, lhs_obj, rhs_obj, kinds)
        if err != None:
            return err
        lhs_obj.set(lhs_obj.kind, lhs_obj.value + rhs_obj.value)
    else:
        kinds = [objkind.NUM]
        err = _check_unif_aug_ass_types(node, lhs_obj, rhs_obj, kinds)
        if err != None:
            return err

        if node.has_lexkind(lexkind.ASSIGN_MINUS):
            lhs_obj.set(lhs_obj.kind, lhs_obj.value - rhs_obj.value)
        elif node.has_lexkind(lexkind.ASSIGN_MULT):
            lhs_obj.set(lhs_obj.kind, lhs_obj.value * rhs_obj.value)
        elif node.has_lexkind(lexkind.ASSIGN_DIV):
            if rhs_obj.value == 0:
                return Error("division by zero", rhs_expr.range.copy())
            lhs_obj.set(lhs_obj.kind, lhs_obj.value / rhs_obj.value)
        elif node.has_lexkind(lexkind.ASSIGN_REM):
            if rhs_obj.value == 0:
                return Error("division by zero", rhs_expr.range.copy())
            lhs_obj.set(lhs_obj.kind, lhs_obj.value % rhs_obj.value)
        else:
            return Error("invalid lexkind for augmented assign", node.range.copy())

def _eval_while(ctx, node):
    expr = node.leaves[0]
    block = node.leaves[1]

    res = _eval_expr(ctx, expr)
    if res.failed():
        return res.error
    cond = res.value

    if not cond.is_kind(objkind.BOOL):
        err = Error("expression is not a boolean", expr.range.copy())
        return err

    while cond.value:
        res = _eval_block(ctx, block)
        if res.failed():
            return res.error

        res = _eval_expr(ctx, expr)
        if res.failed():
            return res.error
        cond = res.value

    return None

def _eval_if(ctx, node):
    cond = node.leaves[0]
    block = node.leaves[1]
    elifs = node.leaves[2]
    _else = node.leaves[3]

    res = _eval_expr(ctx, cond)
    if res.failed():
        return res.error
    obj = res.value

    if not obj.is_kind(objkind.BOOL):
        return Error("condition expected to be boolean", expr.range.copy())

    if obj.value:
        return _eval_block(ctx, block)

    if elifs != None:
        i = 0
        while i < len(elifs):
            _elif = elifs.leaves[i]
            cond = _elif.leaves[0]
            block = _elif.leaves[1]

            res = _eval_expr(ctx, cond)
            if res.failed():
                return res.error
            obj = res.value

            if not obj.is_kind(objkind.BOOL):
                return Error("condition expected to be boolean", expr.range.copy())

            if obj.value:
                return _eval_block(ctx, block)
            i += 1

    if _else != None:
        return _eval_block(ctx, _else.leaves[0])
    
    return None

def _eval_sttm(ctx, node):
    if node.kind == nodekind.IMPORT:
        return _eval_import(ctx, node)
    elif node.kind == nodekind.FROM_IMPORT:
        return _eval_from(ctx, node)
    elif node.kind == nodekind.FUNC:
        return _eval_func(ctx, node)
    elif node.kind == nodekind.ASSIGN:
        return _eval_assign(ctx, node)
    elif node.kind == nodekind.AUGMENTED_ASSIGN:
        return _eval_aug_assign(ctx, node)
    elif node.kind == nodekind.WHILE:
        return _eval_while(ctx, node)
    elif node.kind == nodekind.IF:
        return _eval_if(ctx, node)
    elif node.kind == nodekind.RETURN:
        return _eval_return(ctx, node)
    elif node.kind == nodekind.CLASS:
        return _eval_declare_class(ctx, node)
    elif node.kind == nodekind.PASS:
        return None
    else:
        res = _eval_expr(ctx, node)
        return res.error

def _eval_block(ctx, node):
    i = 0
    while i < len(node.leaves):
        sttm = node.leaves[i]
        err = _eval_sttm(ctx, sttm)
        if err != None:
            return err
        i += 1
    return None

def _eval_module(ctx, name):
    if not name in ctx.source_map:
        err = Error("module '"+name+"' not found", None)
        return Result(None, err)
    source = ctx.source_map[name]

    res = parse(source, False)
    if res.failed():
        return Result(None, res.error)
    n = res.value
    if n.kind != nodekind.BLOCK:
        err = Error("expected root node to be a _block", None)
        return Result(None, err)
    n.compute_range()

    s = _Scope(ctx.builtin_scope, scopekind.MODULE)
    ctx.push_env(s)
    module = _Module(name, s)

    err = _eval_block(ctx, n)
    if err != None:
        return Result(None, err)

    ctx.pop_env()
    return Result(module, None)

# TODO: figure out how to self-interpret this function without making a mess
def _str_dict(dict):
    keys = list(dict.value.keys())
    out = "{"
    i = 0
    while i < len(keys):
        key = keys[i]
        value = dict.value[key]
        out += str(key) + ":" + _str_obj(value)
        if i + 1 < len(keys):
            out += ", "
        i += 1

def _str_list(list):
    i = 0
    out = "["
    while i < len(list.value):
        obj = list.value[i]
        out += _str_obj(obj)
        if i + 1 < len(list.value):
            out += ", "
        i += 1
    out += "]"
    return out

def _str_obj(obj):
    if obj.is_kind(objkind.LIST):
        return _str_list(obj)
    elif obj.is_kind(objkind.STR):
        return "\"" + obj.value + "\""
    elif obj.is_kind(objkind.BOOL):
        if obj.value:
            return "True"
        else:
            return "False"
    elif obj.is_kind(objkind.NUM):
        return str(obj.value)
    elif obj.is_kind(objkind.DICT):
        return _str_dict(obj)
    elif obj.is_kind(objkind.MODULE):
        return "module<" + obj.value.name + ">"
    elif obj.is_kind(objkind.USER_OBJECT):
        return "object<" + obj.value.class_name + ">"
    elif obj.is_kind(objkind.USER_FUNCTION):
        return "function<" + obj.value.name + ">"
    elif obj.is_kind(objkind.NONE):
        return "None"
    elif obj.is_kind(objkind.USER_CLASS):
        return "class<" + obj.value.name + ">"
    else:
        return "<unknown>"

def _print_wrapper(arg):
    print(_str_obj(arg))

def _create_builtin_scope():
    s = _Scope(None, scopekind.BUILTIN)
    func = _Builtin_Func(1, _print_wrapper)
    p = _Py_Object(objkind.BUILTIN_FUNC, func, False)
    s.add_symbol("print", p)
    return s

def evaluate(module_map, entry_name):
    if not entry_name in module_map:
        return Error("entry module not in module map", None)

    s = _create_builtin_scope()
    node = _Call_Node(None, s)
    ctx = _Context(module_map, node, s)
    res = _eval_module(ctx, entry_name)
    return res.error
