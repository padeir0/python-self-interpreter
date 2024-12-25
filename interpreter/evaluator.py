from core import Error, Node
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

class _User_Function_Template:
    def __init__(self, node, formal_args):
        self.node = node
        self.formal_args = formal_args
        self.num_args = len(formal_args)

class _User_Function_Instance:
    def __init__(self, template):
        self.template = template

    def call(self, ctx, args):
        pass
    
class _User_Method:
    def __init__(self, node, formal_args):
        self.node = node
        self.formal_args = formal_args
        self.num_args = len(formal_args)

    def call(self, ctx, instance, args):
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
    def find_scope(self, name):
        if name in self.dict:
            return self
        elif self.parent != None:
            return self.parent.find_scope(name)
        else:
            return None
    def retrieve(self, name):
        if name in self.dict:
            return self.dict[name]
        else:
            print("internal error: should be unreachable")
            return None

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
        self.module_map = {}

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

def _tuple(ctx, node):
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
    elif node.kind == nodekind.TUPLE:
        return _tuple(ctx, node)
    elif node.kind == nodekind.INDEX:
        return _index(ctx, node)
    elif node.kind == nodekind.FIELD_ACCESS:
        return _field_access(ctx, node)
    elif node.kind == nodekind.SLICE:
        return _slice(ctx, node)
    else:
        return Error("invalid expression", node.range.copy())

def _exprlist_sttm(ctx, node):
    pass

# begin
def _import(ctx, node):
    i = 0
    while i < len(node.leaves):
        i += 1

def _from(ctx, node):
    pass

def _def(ctx, node):
    pass

def _assign(ctx, node):
    pass
# end

def _multi_assign(ctx, node):
    pass

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
    if node.kind == nodekind.EXPR_LIST:
        return _exprlist_sttm(ctx, node)
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

def eval_module(ctx, module, source_code):
    n, err = parse(source_code, False)
    if err != None:
        return err
    if n.kind != nodekind.BLOCK:
        return Error("expected root node to be a _block", None)

    i = 0
    while i < len(n.leaves):
        sttm = n.leaves[i]
        err = eval_sttm(ctx, sttm)
        if err != None:
            return err
        i += 1

    return None
    
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
    return eval_module(ctx, source)

