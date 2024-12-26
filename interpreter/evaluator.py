from core import Result, Error, Node
from parser import parse
import lexkind
import nodekind
import objkind
import scopekind

# Considerations:
# - All built-in functions must be implemented using CPython's built-in functions.
# - `print` takes a single argument (no varags) and uses __str__ method if present
# - to iterate on maps, use the map.items() method

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

class _User_Function:
    def __init__(self, name, block, formal_args):
        self.name = name
        self.block = block
        # lista dos nomes dos argumentos
        self.formal_args = formal_args
    def call(self, ctx, args):
        ctx.push_env(scopekind.FUNCTION)
        if len(args) != len(self.formal_args):
            return Error("invalid number of arguments")

        i = 0
        while i < len(args):
            name = self.formal_args[i]
            obj = args[i]
            ctx.add_symbol(name, obj)
            i += 1

        err = eval_block(ctx, self.block)
        if err != None:
            return err

        ctx.pop_env()
        return None
    
class _User_Method:
    def __init__(self, node, formal_args):
        self.node = node
        self.formal_args = formal_args
        self.num_args = len(formal_args)

    def call(self, ctx, instance, args):
        # passa 'self' como um identificador no ambiente
        pass

class _User_Object_Template:
    def __init__(self, node):
        self.node = node

class _User_Object_Instance:
    def __init__(self, template):
        self.template = template
        self.value = None

    # preenche self.value usando a logica do __init__ criado pelo usuario
    # emitir um erro se não existir __init__
    def eval_init(self, args):
        pass

    # retorna um atributo do objeto
    def get_attr(self, ctx, method_name, args):
        pass

class _Module:
    def __init__(self, name, mod_scope):
        self.name = name
        self.scope = mod_scope

class _Py_Object:
    def __init__(self, kind, value):
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
    def __init__(self, source_map, call_node):
        self.source_map = source_map
        self.curr_call_node = call_node

    def push_env(self, kind):
        s = _Scope(self.curr_call_node.curr_scope, kind)
        next = _Call_Node(self.curr_call_node, s)
        self.curr_call_node = next

    def pop_env(self):
        self.curr_call_node = self.curr_call_node.parent

    def curr_scope(self):
        return self.curr_call_node.curr_scope

    def add_symbol(self, name, obj):
        self.curr_call_node.curr_scope.add_symbol(name, obj)

    def add_symbols(self, obj_map):
        self.curr_call_node.curr_scope.add_symbols(obj_map)

    def set_symbol(self, name, obj):
        return self.curr_call_node.curr_scope.set_symbol(name, obj):

def _bin_operator(ctx, node):
    pass

def _una_operator(ctx, node):
    pass

def _terminal(ctx, node):
    pass

def _dict(ctx, node):
    pass

def _list(ctx, node):
    pass

def _call(ctx, node):
    pass

def _index(ctx, node):
    pass

def _field_access(ctx, node):
    pass

def _slice(ctx, node):
    pass

def eval_expr(ctx, node):
    if node.kind == nodekind.BIN_OPERATOR:
        return _bin_operator(ctx, node)
    elif node.kind == nodekind.UNA_OPERATOR:
        return _una_operator(ctx, node)
    elif node.kind == nodekind.TERMINAL:
        return _terminal(ctx, node)
    elif node.kind == nodekind.DICT:
        return _dict(ctx, node)
    elif node.kind == nodekind.LIST:
        return _list(ctx, node)
    elif node.kind == nodekind.CALL:
        return _call(ctx, node)
    elif node.kind == nodekind.INDEX:
        return _index(ctx, node)
    elif node.kind == nodekind.FIELD_ACCESS:
        return _field_access(ctx, node)
    elif node.kind == nodekind.SLICE:
        return _slice(ctx, node)
    else:
        err = Error("invalid expression", node.range.copy())
        return Result(None, err)

def _exprlist_sttm(ctx, node):
    i = 0
    while i < len(node.leaves):
        leaf = node.leaves[i]
        res = _eval_expr(ctx, leaf)
        if res.failed():
            return res.error
        i += 1
    return None

# begin
def _import(ctx, node):
    i = 0
    while i < len(node.leaves):
        leaf = node.leaves[i]
        name = leaf.value.text
        res = eval_module(ctx, name)
        if res.failed():
            return res.error()
        mod = res.value
        obj = _Py_Object(mod, objkind.MODULE)
        ctx.add_symbol(name, obj)
        i += 1
    return None

def _from(ctx, node):
    id = node.leaves[0]
    idlist = node.leaves[1]

    name = id.value.text
    res = eval_module(ctx, name)
    if res.failed():
        return res.error
    mod = res.value

    i = 0
    while i < len(idlist.leaves):
        leaf = node.leaves[i]
        name = leaf.value.text
        if mod.scope.contains(name):
            res = mod.scope.retrieve(name)
            ctx.add_symbol(name, res.value)
        else:
            return Error("symbol not found in module", leaf.range.copy())
        i += 1
    return None

def extract_names(arg_list):
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
    arg_names = extract_names(args.leaves)

    func = _User_Function(name, arg_names, block)
    ctx.add_symbol(name, func)
    return None

def _assign(ctx, node):
    pass
# end

def _aug_assign(ctx, node):
    pass

def _while(ctx, node):
    pass

def _if(ctx, node):
    pass

def _return(ctx, node):
    pass

def _declare_class(ctx, node):
    pass

def eval_sttm(ctx, node):
    if node.kind == nodekind.EXPR:
        return _expr_sttm(ctx, node)
    elif node.kind == nodekind.IMPORT:
        return _import(ctx, node)
    elif node.kind == nodekind.FROM:
        return _from(ctx, node)
    elif node.kind == nodekind.DEF:
        return _def(ctx, node)
    elif node.kind == nodekind.ASSIGN:
        return _assign(ctx, node)
    elif node.kind == nodekind.MULTI_ASSIGN:
        return _multi_assign(ctx, node)
    elif node.kind == nodekind.AUGMENTED_ASSIGN:
        return _aug_assign(ctx, node)
    elif node.kind == nodekind.WHILE:
        return _while(ctx, node)
    elif node.kind == nodekind.IF:
        return _if(ctx, node)
    elif node.kind == nodekind.RETURN:
        return _return(ctx, node)
    elif node.kind == nodekind.CLASS:
        return _declare_class(ctx, node)
    elif node.kind == nodekind.PASS:
        return None
    else:
        return Error("invalid statement", node.range.copy())

def eval_block(ctx, node):
    i = 0
    while i < len(node.leaves):
        sttm = node.leaves[i]
        err = eval_sttm(ctx, sttm)
        if err != None:
            return err
        i += 1
    return None

def eval_module(ctx, name):
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

    ctx.push_env(scopekind.MODULE)
    module = _Module(name, ctx.curr_scope())

    err = eval_block(ctx, n)
    if err != None:
        return Result(None, err)

    ctx.pop_env()
    return Result(module, None)
    
def create_builtin_scope():
    s = _Scope(None, scopekind.BUILTIN)
    p = _Builtin_Func(1, print)
    s.add_symbol("print", p)
    return s
    
def evaluate(module_map, entry_name):
    if not entry_name in module_map:
        return Error("entry module not in module map", None)

    s = create_builtin_scope()
    node = _Call_Node(None, s)
    ctx = _Context(module_map, node)
    source = module_map[entry_name]
    res = eval_module(ctx, source)
    return res.error

