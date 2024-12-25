import core
import lexkind
import nodekind

# Considerations:
# - All built-in functions must be implemented using CPython's built-in functions.
# - `print` takes a single argument (no varags) and uses __str__ method if present
# - to iterate on maps, use the map.items() method

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

class _Py_Object:
    def __init__(self, kind, value):
        self.kind = kind
        self.value = value

class _Scope:
    def __init__(self, parent, kind):
        
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

# we evaluate each module, filling up their scopes with
# declared names
class _Module:
    def __init__(self, name, root, builtin_scope):
        self.name = name
        self.root = root
        self.scope = _Scope(builtin_scope)

# _Context define um nó numa pilha de chamada
class _Context:
    def __init__(self, parent):
        # toda função tem um escopo, podendo variar apenas localmente (no escopo de função)
        # ou globalmente (no escopo de módulo), por isso é necessário que esse campo esteja
        # presente e aponte para o escopo onde a função foi declarada
        self.curr_scope = None
        # preenchido por qualquer função chamada dentro desse contexto
        self.return_obj = None
        # ao retornar de uma função, é necessário ter acesso ao contexto pai
        self.parent = parent

def evaluate_sttm(ctx, node):
def evaluate_expr(ctx, node):


def create_builtin_namespace():
    builtin_functions = {
        "print": print,
    }
    
def evaluate(module_map, entry_name):

