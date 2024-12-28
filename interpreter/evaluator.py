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
    def __init__(self, num_args, function):
        self.num_args = num_args
        self.function = function
    def call(self, args):
        if len(args) != self.num_args:
            return Error("invalid number of arguments", None)
        if self.num_args == 1:
            self.function(args[0])
        elif self.num_args == 2:
            self.function(args[0], args[1])
        elif self.num_args == 3:
            self.function(args[0], args[1], args[2])
        else:
            return Error("too many arguments", None)
        return None

# implementamos métodos passando um escopo onde o "self"
# é uma variável respresentando a instancia do objeto
class _User_Function:
    def __init__(self, name, block, formal_args, parent_scope):
        self.name = name
        self.block = block
        # lista dos nomes dos argumentos
        self.formal_args = formal_args
        # toda função captura o ambiente que ela ta inserida,
        # ie, é uma closure
        self.parent_scope = parent_scope

    def call(self, ctx, args):
        if len(args) != len(self.formal_args):
            return Error("invalid number of arguments")

        s = _Scope(self.parent_scope, scopekind.FUNCTION)
        ctx.push_env(s)

        i = 0
        while i < len(args):
            name = self.formal_args[i]
            obj = args[i]
            s.add_symbol(name, obj)
            i += 1

        err = eval_block(ctx, self.block)
        if err != None:
            return err

        ctx.pop_env()
        return None
    
class _User_Object_Template:
    def __init__(self, node, scope):
        self.node = node
        self.scope = scope

class _User_Object_Instance:
    def __init__(self, template):
        self.template = template
        # dicionario de tipo str->_Py_Object que contém as propriedades
        # do objeto
        self.value = None

    # preenche self.value usando a logica do __init__ criado pelo usuario
    # emitir um erro se não existir __init__
    def eval_init(self, args):
        # TODO: implement evaling __init__
        pass

    # retorna um atributo do objeto
    def get_attr(self, attr_name):
        if attr_name in self.value:
            return Result(self.value[attr_name], None)
        else:
            return Result(None, True)

    def get_create_attr(self, attr_name):
        if not attr_name in self.value:
            self.value[attr_name] = _Py_Object(objkind.NONE, None, false)
        return self.value[attr_name]

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
    def set(self, obj):
        self.value = obj.value

class _Scope:
    def __init__(self, parent, kind):
        # é necessário diferenciar entre escopos de função
        # e escopos de módulo
        self.kind = kind
        self.parent = parent
        self.dict = {}
    def add_symbol(self, name, obj):
        self.dict[name] = obj
    def add_symbols(self, obj_map):
        kv_pairs = obj_map.items()
        i = 0
        while i < len(kv_pairs):
            key = kv_pair[0]
            value = kv_pair[1]
            self.dict[key] = value
            i += 1
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

    def retrieve(self, name):
        return self.curr_call_node.curr_scope.retrieve(name)

    def add_symbol(self, name, obj):
        self.curr_call_node.curr_scope.add_symbol(name, obj)

    def add_symbols(self, obj_map):
        self.curr_call_node.curr_scope.add_symbols(obj_map)

    def set_symbol(self, name, obj):
        return self.curr_call_node.curr_scope.set_symbol(name, obj):

    def set_mod(self, mod_name, mod):
        self.evaluated_mods[mod_name] = mod

    def get_mod(self, mod_name):
        if mod_name in self.evaluated_mods:
            return self.evaluated_mods[mod_name]
        return None

    def get_return(self):
        return self.curr_call_node.return_obj

def _eval_bin_operator(ctx, node):
    # TODO: implement binary operators
    pass

def _eval_una_operator(ctx, node):
    operand = node.leaves[0]
    res = _eval_expr(ctx, operand)
    if res.failed():
        return res
    obj = res.value
    if node.has_lexkind(lexkind.NOT):
        if obj.is_kind(objkind.BOOL):
            new_value = not obj.value
            obj = _Py_Object(objkind.BOOL, new_value, false)
            return Result(obj, None)
        else:
            err = Error("object is not a boolean", operand.range.copy())
            return Result(None, err)
    elif node.has_lexkind(lexkind.MINUS):
        if obj.is_kind(objkind.NUM):
            new_value = -obj.value
            obj = _Py_Object(objkind.NUM, new_value, false)
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
        obj = _Py_Object(objkind.BOOL, True, false)
    elif node.has_lexkind(lexkind.FALSE):
        obj = _Py_Object(objkind.BOOL, False, false)
    elif node.has_lexkind(lexkind.NONE):
        obj = _Py_Object(objkind.NONE, None, false)
    elif node.has_lexkind(lexkind.ID):
        name = node.value.text
        res = ctx.retrieve(name)
        if res.failed():
            err = res.error
            err.range = node.range.copy()
            return Result(None, err)
        obj = res.value
    elif node.has_lexkind(lexkind.STR):
        obj = _Py_Object(objkind.STR, node.value.text, false)
    elif node.has_lexkind(lexkind.NUM):
        obj = _Py_Object(objkind.NUM, int(node.value.text), false)
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

        # TODO: properly check the type of the key
        out[key.value] = value
        i += 1

    # TODO: check if this mutability is okay
    obj = _Py_Object(objkind.DICT, out, false)
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
    obj = _Py_Object(objkind.LIST, out, false)
    return Result(obj, None)

def _eval_special_call_int(ctx, node):
    # TODO: implement int()
    pass
def _eval_special_call_len(ctx, node):
    # TODO: implement len()
    pass
def _eval_special_map_items(ctx, node):
    # TODO: implement map.items()
    pass

# SPECIAL_CASES:
#     map.items()
#     int(<str>)
#     len(<list>)
def _eval_call(ctx, node):
    exprlist = node.leaves[0]
    callee = node.leaves[1]

    if callee.kind == nodekind.TERMINAL and callee.has_lexkind(lexkind.ID):
        name = callee.value.text
        if name == "int":
            return _eval_special_call_int(ctx, node)
        elif name == "len":
            return _eval_special_call_len(ctx, node)

    thing = None
    if callee.kind == nodekind.FIELD_ACCESS:
        field = callee.leaves[0]
        operand = callee.leaves[1]
        res = _eval_expr(ctx, operand)
        if res.failed():
            return res
        obj = res.value

        if obj.is_kind(objkind.DICT):
            return _eval_special_map_items(ctx, obj, field)
        else:
            res = _eval_field_access_obj(ctx, obj, field)
            if res.failed():
                return res
            thing = res.value
    else:
        thing = _eval_expr(ctx, callee)

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
        obj = ctx.
        return Result(None, err)
    elif thing.is_kind(objkind.BUILTIN_FUNC):
        err = thing.value.call(args)
        obj = ctx.get_return()
        return Result(obj, err)
    elif thing.is_kind(objkind.USER_OBJECT):
        # TODO: implement call to __init__
        pass
    else:
        err = Error("object is not callable", callee.range.copy())
        return Result(None, err)

def _eval_field_access_obj(ctx, obj, field):
    if obj.is_kinds([objkind.STR, objkind.DICT, objkind.NUM,
                     objkind.LIST, objkind.USER_METHOD, objkind.USER_FUNCTION,
                     objkind.BUILTIN_FUNC]):
        err = Error("object has no properties", obj.range.copy())
        return Result(None, err)

    name = field.value.text
    if obj.is_kinds([objkind.MODULE]):
        res = obj.value.get_global(name)
        if res.failed():
            res.error.range = field.range.copy()
            return res
        return Result(res.value, None)
    elif obj.is_kind([objkind.USER_OBJECT]):
        obj = obj.value.get_create_attr(name)
        return Result(obj, None)
    else:
        err = Error("object has invalid type", obj.range.copy())
        return Result(None, err)

def _eval_field_access(ctx, node):
    field = node.leaves[0]
    operand = node.leaves[1]
    res = _eval_expr(ctx, operand)
    if res.failed():
        return res
    obj = res.value

    return _eval_field_access_obj(ctx, obj, field)

def _eval_index(ctx, node):
    # TODO: implement indexing
    pass

def _eval_slice(ctx, node):
    # TODO: implement slicing
    pass

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
            res = eval_module(ctx, name)
            if res.failed():
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

def _def(ctx, node):
    id = node.leaves[0]
    args = node.leaves[1]
    block = node.leaves[2]

    name = id.value.text
    arg_names = _extract_names(args.leaves)

    func = _User_Function(name, arg_names, block, ctx.curr_scope())
    ctx.add_symbol(name, func)
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
                     objkind.LIST, objkind.USER_METHOD, objkind.USER_FUNCTION,
                     objkind.BUILTIN_FUNC]):
        err = Error("object has no properties", obj.range.copy())
        return Result(None, err)

    if obj.is_kinds([objkind.MODULE]):
        err = Error("object is not mutable", lhs.range.copy())
        return Result(None, err)

    if obj.is_kind([objkind.USER_OBJECT]):
        name = field.value.text
        obj = obj.value.get_create_attr(name)
        return Result(obj, None)
    else:
        err = Error("object has invalid type", obj.range.copy())
        return Result(None, err)

# O lado esquerdo deve obedecer uma semantica mais estrita que o direito,
# por necessitar ter um objeto atribuivel.
# A função eval_lhs retorna um _Py_Object, esse, por ser passado por
# referência, pode ser atribuido futuramente.
def _eval_lhs(ctx, lhs):
    if lhs.kind == nodekind.TERMINAL and lhs.value.kind == nodekind.ID:
        name = lhs.value.text
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
        return res
    obj = res.value

    res = _eval_expr(ctx, rhs)
    if res.failed():
        return res
    exp = res.value

    obj.set(exp)
    return Result(None, None)

def _eval_declare_class(ctx, node):
    # TODO: class declaration
    pass

def _eval_return(ctx, node):
    # TODO: return statement
    pass

def _eval_aug_assign(ctx, node):
    # TODO: augmented assign
    pass

def _eval_while(ctx, node):
    # TODO: while statement
    pass

def _eval_if(ctx, node):
    # TODO: if statement
    pass

def _eval_sttm(ctx, node):
    if node.kind == nodekind.EXPR:
        return _eval_expr_sttm(ctx, node)
    elif node.kind == nodekind.IMPORT:
        return _eval_import(ctx, node)
    elif node.kind == nodekind.FROM:
        return _eval_from(ctx, node)
    elif node.kind == nodekind.DEF:
        return _eval_def(ctx, node)
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
        return Error("invalid statement", node.range.copy())

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
        err = Error("module '"+name+"' not found", leaf.range.copy())
        return Result(None, err)
    source = ctx.source_map[name]

    res = parse(source, False)
    if res.failed():
        return Result(None, res.error)
    n = res.value
    if n.kind != nodekind.BLOCK:
        err = Error("expected root node to be a _block", None)
        return Result(None, err)

    s = _Scope(ctx.builtin_scope, scopekind.MODULE)
    ctx.push_env(s)
    module = _Module(name, s)

    err = _eval_block(ctx, n)
    if err != None:
        return Result(None, err)

    ctx.pop_env()
    return Result(module, None)
    
def _create_builtin_scope():
    s = _Scope(None, scopekind.BUILTIN)
    p = _Builtin_Func(1, print)
    s.add_symbol("print", p)
    return s
    
def evaluate(module_map, entry_name):
    if not entry_name in module_map:
        return Error("entry module not in module map", None)

    s = _create_builtin_scope()
    node = _Call_Node(None, s)
    ctx = _Context(module_map, node, s)
    source = module_map[entry_name]
    res = _eval_module(ctx, source)
    return res.error
