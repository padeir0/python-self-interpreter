from core import Result, Error, Node
from parser import parse
import lexkind
import nodekind
import objkind
import scopekind

class _Builtin_Func:
    def __init__(self, num_args, wrapper):
        self.num_args = num_args
        self.wrapper = wrapper

    def call(self, ctx, args):
        if len(args) != self.num_args:
            err = ctx.blank_error("invalid number of arguments")
            return Result(None, err)

        obj = None
        if self.num_args == 1:
            obj = self.wrapper(args[0])
        elif self.num_args == 2:
            obj = self.wrapper(args[0], args[1])
        elif self.num_args == 3:
            obj = self.wrapper(args[0], args[1], args[2])
        else:
            err = ctx.blank_error("too many arguments")
            return Result(None, err)
        return Result(obj, None)

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
            return ctx.blank_error("invalid number of arguments")

        s = _Scope(self.parent_scope, scopekind.FUNCTION)
        ctx.push_env(s)
        ctx.reset_return()

        i = 0
        while i < len(args):
            name = self.formal_args[i]
            obj = args[i]
            ctx.add_symbol(name, obj)
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
        obj = _Py_Object(objkind.USER_OBJECT, instance, True)
        if "__init__" in self.methods:
            res = instance.get_method("__init__")
            if res.failed():
                return res
            func = res.value
            news = _Scope(func.parent_scope, scopekind.FUNCTION)
            news.add_symbol("self", obj)
            func.parent_scope = news
            err = func.call(ctx, args)
            if err != None:
                return Result(None, err)
            return Result(obj, None)
        else:
            err = ctx.blank_error("object has no __init__ procedure")
            return Result(None, err)

class _User_Object_Instance:
    def __init__(self, template):
        # dicionario de tipo str->_Py_Object que contém as propriedades
        # do objeto
        self.properties = {}
        # dicionario de tipo str->_User_Function que contém os métodos
        # do objeto
        self.methods = template.methods
        self.class_name = template.name

    def get_method(self, name):
        if name in self.methods:
            method = self.methods[name]
            copy = _User_Function(
                method.name,
                method.formal_args,
                method.block,
                method.parent_scope,
            )
            return Result(copy, None)
        else:
            return Result(None, True)
    
    # retorna um atributo do objeto
    def get_attr(self, attr_name):
        if attr_name in self.properties:
            return Result(self.properties[attr_name], None)
        else:
            return Result(None, True)

    def create_attr(self, attr_name):
        self.properties[attr_name] = _Py_Object(objkind.NONE, None, True)
        return self.properties[attr_name]

class _Module:
    def __init__(self, name, mod_scope):
        self.name = name
        self.scope = mod_scope

    def get_global(self, name):
        if self.scope.contains(name):
            return self.scope.retrieve(name)
        return Result(None, True)

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
        return self.kind in kinds
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
        self.name = ""
        self.dict = {}
    def add_symbol(self, name, obj):
        self.dict[name] = obj
    def set_symbol(self, name, obj):
        if name in self.dict:
            self.dict[name] = obj
            return True
        else:
            return False
    # set_scope_name é usado nos modulos
    def set_scope_name(self, name):
        self.name = name
    def contains(self, name):
        return name in self.dict
    def retrieve(self, name):
        if name in self.dict:
            return Result(self.dict[name], None)
        elif self.parent != None:
            return self.parent.retrieve(name)
        else:
            return Result(None, True)
    def __str__(self):
        out = ""
        curr = self
        while curr != None:
            out += str(curr.dict)
            out += "\n"
            curr = curr.parent
        return out

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

    def __str__(self):
        return str(self.curr_scope.dict)

class _Context:
    def __init__(self, source_map, call_node, builtin_scope):
        self.builtin_scope = builtin_scope
        self.source_map = source_map
        self.curr_call_node = call_node
        self.evaluated_mods = {}
        self.is_returning = False
        self.verbose = False

    def find_module_name(self):
        curr_scope = self.curr_call_node.curr_scope

        while curr_scope != None:
            if curr_scope.name != "":
                return curr_scope.name
            curr_scope = curr_scope.parent

        return ""

    def blank_error(self, message):
        modname = self.find_module_name()
        return Error(modname, message, None)

    def error(self, message, node):
        modname = self.find_module_name()
        return Error(modname, message, node.range.copy())

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

    def reset_return(self):
        none = _Py_Object(objkind.NONE, None, True)
        self.curr_call_node.parent.return_obj = none

    def get_return(self):
        self.is_returning = False
        return self.curr_call_node.return_obj

    def set_return(self, obj):
        if self.curr_call_node.parent == None:
            return ctx.blank_error("invalid return (outside function?)")
        self.curr_call_node.parent.return_obj = obj
        self.is_returning = True
        return None

    def toggle_verbose(self):
        self.verbose = not self.verbose

    def __str__(self):
        out = ""
        curr = self.curr_call_node
        while curr != None:
            out += curr.__str__()
            out += "\n"
            curr = curr.parent
        return out

def _check_unif_bin_types(ctx, node, left_obj, right_obj, typelist):
    if left_obj.kind != right_obj.kind:
        a = objkind.to_str(left_obj.kind)
        b = objkind.to_str(right_obj.kind)
        msg = "objects have different types: " + a + " vs " + b
        return ctx.error(msg, node)
    if not left_obj.is_kinds(typelist):
        msg = "invalid operation on object of type: " + objkind.to_str(left_obj.kind)
        return ctx.error(msg, node)
    return None

def _eval_arith(ctx, left_obj, right_obj, node):
    err = _check_unif_bin_types(ctx, node, left_obj, right_obj, [objkind.NUM])
    if err != None:
        return Result(None, err)

    out = None
    if node.has_lexkind(lexkind.MINUS):
        out = left_obj.value - right_obj.value
    elif node.has_lexkind(lexkind.MULT):
        out = left_obj.value * right_obj.value
    elif node.has_lexkind(lexkind.DIV):
        if right_obj.value == 0:
            err = ctx.error("division by zero", node)
            return Result(None, err)
        out = left_obj.value / right_obj.value
    elif node.has_lexkind(lexkind.REM):
        if right_obj.value == 0:
            err = ctx.error("division by zero", node)
            return Result(None, err)
        out = left_obj.value % right_obj.value
    obj = _Py_Object(objkind.NUM, out, True)
    return Result(obj, None)

def _identity(a, b):
    if a.kind == objkind.LIST:
        return _eq_list(a, b)
    else:
        return a.value == b.value

def _eq_list(a, b):
    A = a.value
    B = b.value
    i = 0
    while i < len(A):
        if not _identity(A[i], B[i]):
            return False
        i += 1
    return True

def _eval_identity(ctx, left_obj, right_obj, node):
    if left_obj.kind == objkind.DICT:
        err = ctx.error("map has no identity", node)
        return Result(None, err)

    if left_obj.kind != right_obj.kind:
        out = False
    else:
        out = _identity(left_obj, right_obj)

    if node.has_lexkind(lexkind.DIFF):
        out = not out

    obj = _Py_Object(objkind.BOOL, out, True)
    return Result(obj, None)

def _eval_order(ctx, left_obj, right_obj, node):
    err = _check_unif_bin_types(ctx, node, left_obj, right_obj, [objkind.NUM, objkind.STR])
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

    obj = _Py_Object(objkind.BOOL, out, True)
    return Result(obj, None)

def _eval_or(ctx, node):
    left = node.leaves[0]
    right = node.leaves[1]

    res = _eval_expr(ctx, left)
    if res.failed():
        return res
    left_obj = res.value

    if left_obj.value:
        obj = _Py_Object(objkind.BOOL, True, True)
        return Result(obj, None)

    res = _eval_expr(ctx, right)
    if res.failed():
        return res
    right_obj = res.value

    out = left_obj.value or right_obj.value
    obj = _Py_Object(objkind.BOOL, out, True)
    return Result(obj, None)

def _eval_and(ctx, node):
    left = node.leaves[0]
    right = node.leaves[1]

    res = _eval_expr(ctx, left)
    if res.failed():
        return res
    left_obj = res.value

    if not left_obj.value:
        obj = _Py_Object(objkind.BOOL, False, True)
        return Result(obj, None)

    res = _eval_expr(ctx, right)
    if res.failed():
        return res
    right_obj = res.value

    out = left_obj.value and right_obj.value
    obj = _Py_Object(objkind.BOOL, out, True)
    return Result(obj, None)

def _eval_plus(ctx, left_obj, right_obj, node):
    kinds = [objkind.NUM, objkind.LIST, objkind.STR]
    err = _check_unif_bin_types(ctx, node, left_obj, right_obj, kinds)
    if err != None:
        return Result(None, err)

    out = left_obj.value + right_obj.value
    obj = _Py_Object(left_obj.kind, out, True)
    return Result(obj, None)

def _in(value, list):
    i = 0
    while i < len(list):
        if list[i].value == value:
            return True
        i += 1
    return False

def _eval_in(ctx, left_obj, right_obj, node):
    if right_obj.is_kind(objkind.DICT):
        if not left_obj.is_hashable():
            err = ctx.error("object is not hashable", node.left())
            return Result(None, err)
        out = left_obj.value in right_obj.value
        obj = _Py_Object(objkind.BOOL, out, True)
        return Result(obj, None)
    elif right_obj.is_kind(objkind.LIST):
        out = _in(left_obj.value, right_obj.value)
        obj = _Py_Object(objkind.BOOL, out, True)
        return Result(obj, None)
    else:
        err = ctx.error("object is not a dictionary or list", node.right())
        return Result(None, err)

def _eval_bin_operator(ctx, node):
    # esses precisam ser short-circuited
    if node.has_lexkind(lexkind.AND):
        return _eval_and(ctx, node)
    elif node.has_lexkind(lexkind.OR):
        return _eval_or(ctx, node)

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
    
    if node.has_lexkind(lexkind.IN):
        return _eval_in(ctx, left_obj, right_obj, node)
    elif node.has_lexkind(lexkind.PLUS):
        return _eval_plus(ctx, left_obj, right_obj, node)
    elif node.has_lexkinds(arith):
        return _eval_arith(ctx, left_obj, right_obj, node)
    elif node.has_lexkinds(identity):
        return _eval_identity(ctx, left_obj, right_obj, node)
    elif node.has_lexkinds(order):
        return _eval_order(ctx, left_obj, right_obj, node)
    else:
        err = ctx.error("invalid lexkind for binary operator", node)
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
            obj = _Py_Object(objkind.BOOL, new_value, True)
            return Result(obj, None)
        else:
            err = ctx.error("object is not a boolean", operand)
            return Result(None, err)
    elif node.has_lexkind(lexkind.MINUS):
        if obj.is_kind(objkind.NUM):
            new_value = -obj.value
            obj = _Py_Object(objkind.NUM, new_value, True)
            return Result(obj, None)
        else:
            err = ctx.error("object is not a number", operand)
            return Result(None, err)
    else:
        err = ctx.error("invalid lexkind for unary operator", node)
        return Result(None, err)

def _eval_terminal(ctx, node):
    obj = None
    if node.has_lexkind(lexkind.TRUE):
        obj = _Py_Object(objkind.BOOL, True, True)
    elif node.has_lexkind(lexkind.FALSE):
        obj = _Py_Object(objkind.BOOL, False, True)
    elif node.has_lexkind(lexkind.NONE):
        obj = _Py_Object(objkind.NONE, None, True)
    elif node.has_lexkind(lexkind.ID) or node.has_lexkind(lexkind.SELF):
        name = node.value.text
        res = ctx.retrieve(name)
        if res.failed():
            err = ctx.error("name not found", node)
            return Result(None, err)
        obj = res.value
    elif node.has_lexkind(lexkind.STR):
        obj = _Py_Object(objkind.STR, node.value.text, True)
    elif node.has_lexkind(lexkind.NUM):
        obj = _Py_Object(objkind.NUM, int(node.value.text), True)
    else:
        err = ctx.error("invalid lexkind for terminal", node)
        return Result(None, err)
    return Result(obj, None)

def _eval_dict(ctx, node):
    kvlist = node.leaves[0]
    i = 0
    out = {}
    if kvlist != None:
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
            value = res.value.copy()

            if not key.is_hashable():
                err = ctx.error("object is not hashable", key_expr)
                return Result(None, err)

            out[key.value] = value
            i += 1

    obj = _Py_Object(objkind.DICT, out, True)
    return Result(obj, None)

def _eval_list(ctx, node):
    exprlist = node.leaves[0]
    i = 0
    out = []
    if exprlist != None:
        while i < len(exprlist.leaves):
            expr = exprlist.leaves[i]
            res = _eval_expr(ctx, expr)
            if res.failed():
                return res
            item = res.value.copy()
            out += [item]
            i += 1
    obj = _Py_Object(objkind.LIST, out, True)
    return Result(obj, None)

def _eval_call(ctx, node):
    if ctx.verbose:
        print("_eval_call")
    exprlist = node.leaves[0]
    callee = node.leaves[1]

    res = _eval_expr(ctx, callee)
    if res.failed():
        return res
    thing = res.value

    args = []
    if exprlist != None:
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
            if err.range == None:
                err.range = node.range.copy()
            return Result(None, err)
        obj = ctx.get_return()
        return Result(obj, None)
    elif thing.is_kind(objkind.BUILTIN_FUNC):
        res = thing.value.call(ctx, args)
        if res.failed():
            if res.error.range == None:
                res.error.range = node.range.copy()
            return res
        obj = res.value
        return Result(obj, None)
    elif thing.is_kind(objkind.USER_CLASS):
        res = thing.value.eval_init(ctx, args)
        if res.failed():
            if res.error.range == None:
                res.error.range = callee.range.copy()
            return res
        obj = res.value
        return Result(obj, None)
    else:
        err = ctx.error("object is not callable", callee)
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
        err = ctx.error("object has no properties", operand)
        return Result(None, err)

    name = field.value.text
    if obj.is_kind(objkind.MODULE):
        res = obj.value.get_global(name)
        if res.failed():
            msg = "name not found in module"
            err = ctx.error(msg, field)
            return Result(None, err)
        return Result(res.value, None)
    elif obj.is_kind(objkind.USER_OBJECT):
        if name in obj.value.methods:
            func = obj.value.get_method(name).value
            news = _Scope(func.parent_scope, scopekind.FUNCTION)
            news.add_symbol("self", obj)
            func.parent_scope = news
            obj = _Py_Object(objkind.USER_FUNCTION, func, False)
        elif name in obj.value.properties:
            obj = obj.value.get_attr(name).value
        else:
            err = ctx.error("property not found", field)
            return Result(err, None)
        return Result(obj, None)
    else:
        msg = "object has invalid type: " + objkind.to_str(obj.kind)
        err = ctx.error(msg, operand)
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
                err = ctx.error("key not found", expr)
                return Result(None, err)
        else:
            err = ctx.error("object not hashable", expr)
            return Result(None, err)
    elif obj.is_kind(objkind.LIST):
        if index.is_kind(objkind.NUM):
            if index.value >= 0 and index.value < len(obj.value):
                obj = obj.value[index.value]
                return Result(obj, None)
            else:
                err = ctx.error("index out of range", expr)
                return Result(None, err)
        else:
            err = ctx.error("index is not a number", expr)
            return Result(None, err)
    elif obj.is_kind(objkind.STR):
        if index.is_kind(objkind.NUM):
            if index.value >= 0 and index.value < len(obj.value):
                value = obj.value[index.value]
                obj = _Py_Object(objkind.STR, value, True)
                return Result(obj, None)
            else:
                err = ctx.error("index out of range", expr)
                return Result(None, err)
        else:
            err = ctx.error("index is not a number", expr)
            return Result(None, err)
    else:
        msg = "unexpected type for indexing: " + objkind.to_str(obj.kind)
        err = ctx.error(msg, operand)
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
        err = ctx.error("expected an integer", begin_expr)
        return Result(None, err)
    if not end.is_kind(objkind.NUM):
        err = ctx.error("expected an integer", end_expr)
        return Result(None, err)
    if not obj.is_kinds([objkind.LIST, objkind.STR]):
        err = ctx.error("expected a list or string", operand_expr)
        return Result(None, err)

    if begin.value < 0 or begin.value > len(obj.value):
        err = ctx.error("out of bounds", begin_expr)
        return Result(None, err)
    elif end.value < 0 or end.value > len(obj.value):
        err = ctx.error("out of bounds", end_expr)
        return Result(None, err)

    out = obj.value[begin.value:end.value]
    out_obj = _Py_Object(obj.kind, out, True)
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
        err = ctx.error("invalid expression", node)
        return Result(None, err)

def _eval_import(ctx, node):
    idlist = node.leaves[0]
    i = 0
    while i < len(idlist.leaves):
        leaf = idlist.leaves[i]
        name = leaf.value.text

        mod = ctx.get_mod(name)
        if mod == None:
            res = _eval_module(ctx, name)
            if res.failed():
                if res.error.range == None:
                    res.error.range = leaf.range.copy()
                return res.error
            mod = res.value
            obj = _Py_Object(objkind.MODULE, mod, False)
            ctx.add_symbol(name, obj)
            ctx.set_mod(name, mod)
        else:
            obj = _Py_Object(objkind.MODULE, mod, False)
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
        leaf = idlist.leaves[i]
        name = leaf.value.text
        if mod.scope.contains(name):
            res = mod.scope.retrieve(name)
            cpy = res.value.copy()
            cpy.mutable = False
            ctx.add_symbol(name, cpy)
        else:
            return ctx.error("symbol not found in module", leaf)
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
    arg_names = {}
    if args != None:
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
        err = ctx.error("object is not mutable", list)
        return Result(None, err)

    res = _eval_expr(ctx, index_expr)
    if res.failed():
        return res
    index_val = res.value

    out = None
    if obj.is_kind(objkind.DICT):
        if not index_val.value in obj.value:
            obj.value[index_val.value] = _Py_Object(objkind.NONE, None, True)
        out = obj.value[index_val.value]
    elif obj.is_kind(objkind.LIST) and index_val.is_kind(objkind.NUM):
        if index_val.value >= 0 and index_val.value < len(obj.value):
            out = obj.value[index_val.value]
        else:
            err = ctx.error("index out of range", index_expr)
            return Result(None, err)
    else:
        err = ctx.error("invalid indexing expression", lhs)
        return Result(None, err)

    if not out.mutable:
        err = ctx.error("object is not mutable", lhs)
        return Result(None, err)

    return Result(out, None)

def _eval_lhs_field_access(ctx, lhs):
    op = lhs.leaves[1]
    field = lhs.leaves[0]

    if field.kind != nodekind.TERMINAL or field.value.kind != lexkind.ID:
        err = ctx.error("field must be an identifier", field)
        return Result(None, err)

    res = _eval_expr(ctx, op)
    if res.failed():
        return res
    obj = res.value

    if obj.is_kinds([objkind.STR, objkind.DICT, objkind.NUM,
                     objkind.LIST, objkind.USER_FUNCTION,
                     objkind.BUILTIN_FUNC]):
        err = ctx.error("object has no properties", op)
        return Result(None, err)

    if obj.is_kinds([objkind.MODULE]):
        err = ctx.error("object is not mutable", lhs)
        return Result(None, err)

    if obj.is_kind(objkind.USER_OBJECT):
        name = field.value.text
        if name in obj.value.methods:
            err = ctx.error("methods are not mutable", field)
            return Result(None, err)
        elif name in obj.value.properties:
            obj = obj.value.get_attr(name).value
        else:
            obj = obj.value.create_attr(name)
        return Result(obj, None)
    else:
        msg = "object has invalid type: " + objkind.to_str(obj.kind)
        err = ctx.error(msg, op)
        return Result(None, err)

# O lado esquerdo deve obedecer uma semantica mais estrita que o direito,
# por necessitar ter um objeto atribuivel.
# A função eval_lhs retorna um _Py_Object, esse, por ser passado por
# referência, pode ser atribuido futuramente.
def _eval_lhs(ctx, lhs):
    if lhs.kind == nodekind.TERMINAL and lhs.value.kind == lexkind.ID:
        name = lhs.value.text
        if not ctx.contains_symbol(name):
            newnone = _Py_Object(objkind.NONE, None, True)
            ctx.add_symbol(name, newnone)
        res = ctx.retrieve(name)
        if res.failed():
            err = ctx.error("name not found", lhs)
            return Result(None, err)
        obj = res.value
        return Result(obj, None)
    elif lhs.kind == nodekind.INDEX:
        return _eval_lhs_index(ctx, lhs)
    elif lhs.kind == nodekind.FIELD_ACCESS:
        return _eval_lhs_field_access(ctx, lhs)
    else:
        err = ctx.error("expression is not assignable", lhs)
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
    if err != None and err.range != None:
        err.range = node.range.copy()

    return err

def _check_unif_aug_ass_types(ctx, node, left_obj, right_obj, typelist):
    if left_obj.kind != right_obj.kind:
        return ctx.error("objects have different types", node)
    if not left_obj.is_kinds(typelist):
        msg = "invalid operation on object of type: " + objkind.to_str(left_obj.kind)
        return ctx.error(msg, node)
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
        err = _check_unif_aug_ass_types(ctx, node, lhs_obj, rhs_obj, kinds)
        if err != None:
            return err
        lhs_obj.set(lhs_obj.kind, lhs_obj.value + rhs_obj.value)
    else:
        kinds = [objkind.NUM]
        err = _check_unif_aug_ass_types(ctx, node, lhs_obj, rhs_obj, kinds)
        if err != None:
            return err

        if node.has_lexkind(lexkind.ASSIGN_MINUS):
            lhs_obj.set(lhs_obj.kind, lhs_obj.value - rhs_obj.value)
        elif node.has_lexkind(lexkind.ASSIGN_MULT):
            lhs_obj.set(lhs_obj.kind, lhs_obj.value * rhs_obj.value)
        elif node.has_lexkind(lexkind.ASSIGN_DIV):
            if rhs_obj.value == 0:
                return ctx.error("division by zero", rhs_expr)
            lhs_obj.set(lhs_obj.kind, lhs_obj.value / rhs_obj.value)
        elif node.has_lexkind(lexkind.ASSIGN_REM):
            if rhs_obj.value == 0:
                return ctx.error("division by zero", rhs_expr)
            lhs_obj.set(lhs_obj.kind, lhs_obj.value % rhs_obj.value)
        else:
            return ctx.error("invalid lexkind for augmented assign", node)

def _eval_do(ctx, node):
    expr = node.leaves[0]
    block = node.leaves[1]

    loop = True
    while loop:
        err = _eval_block(ctx, block)
        if err != None:
            return err

        if ctx.is_returning:
            loop = False
        else:
            res = _eval_expr(ctx, expr)
            if res.failed():
                return res.error
            obj = res.value

            if not obj.is_kind(objkind.BOOL):
                err = ctx.error("expression is not a boolean", expr)
                return err
            loop = obj.value
    
    return None

def _eval_while(ctx, node):
    expr = node.leaves[0]
    block = node.leaves[1]

    loop = True
    while loop:
        res = _eval_expr(ctx, expr)
        if res.failed():
            return res.error
        obj = res.value

        if not obj.is_kind(objkind.BOOL):
            err = ctx.error("expression is not a boolean", expr)
            return err
        cond = obj.value

        if cond:
            err = _eval_block(ctx, block)
            if err != None:
                return err
            if ctx.is_returning:
                loop = False
        else:
            loop = False

    
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
        return ctx.error("condition expected to be boolean", expr)

    if obj.value:
        return _eval_block(ctx, block)

    if elifs != None:
        i = 0
        while i < len(elifs.leaves):
            _elif = elifs.leaves[i]
            cond = _elif.leaves[0]
            block = _elif.leaves[1]

            res = _eval_expr(ctx, cond)
            if res.failed():
                return res.error
            obj = res.value

            if not obj.is_kind(objkind.BOOL):
                return ctx.error("condition expected to be boolean", expr)

            if obj.value:
                return _eval_block(ctx, block)
            i += 1

    if _else != None:
        return _eval_block(ctx, _else.leaves[0])
    
    return None

def _eval_sttm(ctx, node):
    if ctx.verbose:
        print("_eval_sttm")
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
    elif node.kind == nodekind.DO:
        return _eval_do(ctx, node)
    elif node.kind == nodekind.IF:
        return _eval_if(ctx, node)
    elif node.kind == nodekind.RETURN:
        return _eval_return(ctx, node)
    elif node.kind == nodekind.CLASS:
        return _eval_declare_class(ctx, node)
    elif node.kind == nodekind.PASS:
        pass
    else:
        res = _eval_expr(ctx, node)
        return res.error

def _eval_block(ctx, node):
    if ctx.verbose:
        print("_eval_block")
    i = 0
    while i < len(node.leaves) and not ctx.is_returning:
        sttm = node.leaves[i]
        err = _eval_sttm(ctx, sttm)
        if err != None:
            return err
        i += 1
    return None

def _eval_module(ctx, name):
    if ctx.verbose:
        print("_eval_module: " + name)
    if not (name in ctx.source_map):
        err = ctx.blank_error("module '"+name+"' not found")
        return Result(None, err)
    source = ctx.source_map[name]

    res = parse(name, source, False)
    if res.failed():
        return Result(None, res.error)
    n = res.value
    if n.kind != nodekind.BLOCK:
        err = ctx.blank_error("expected root node to be a _block")
        return Result(None, err)

    n.compute_range()

    s = _Scope(ctx.builtin_scope, scopekind.MODULE)
    s.set_scope_name(name)
    ctx.push_env(s)
    module = _Module(name, s)

    err = _eval_block(ctx, n)
    if err != None:
        return Result(None, err)

    ctx.pop_env()
    return Result(module, None)

def evaluate(builtins, module_map, entry_name, verbose):
    if not (entry_name in module_map):
        return Error("", "entry module not in module map", None)

    node = _Call_Node(None, builtins)
    ctx = _Context(module_map, node, builtins)
    if verbose:
        print("\nevaluate\n")
        ctx.toggle_verbose()
    res = _eval_module(ctx, entry_name)
    return res.error
