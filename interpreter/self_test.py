import scopekind
import objkind
from evaluator import _Scope, _Builtin_Func, _Py_Object, evaluate
from lexer import Lexer

def _str_obj(obj):
    if obj.is_kind(objkind.MODULE):
        return "module<" + obj.value.name + ">"
    elif obj.is_kind(objkind.USER_OBJECT):
        return "object<" + obj.value.class_name + ">"
    elif obj.is_kind(objkind.USER_FUNCTION):
        return "function<" + obj.value.name + ">"
    elif obj.is_kind(objkind.USER_CLASS):
        return "class<" + obj.value.name + ">"
    else:
        return str(obj.value)

def _obj_none():
    return _Py_Object(objkind.NONE, None, False)

def _print_wrapper(obj):
    print(_str_obj(obj))
    return _obj_none()

def _int_wrapper(obj):
    value = int(obj.value)
    return _Py_Object(objkind.NUM, value, False)

def _str_wrapper(obj):
    value = _str_obj(obj)
    return _Py_Object(objkind.STR, value, False)

def _len_wrapper(obj):
    value = len(obj.value)
    return _Py_Object(objkind.NUM, value, False)

def _create_func(func):
    bf = _Builtin_Func(1, func)
    return _Py_Object(objkind.BUILTIN_FUNC, bf, False)

builtins = _Scope(None, scopekind.BUILTIN)
builtins.add_symbol("print", _create_func(_print_wrapper))
builtins.add_symbol("int", _create_func(_int_wrapper))
builtins.add_symbol("str", _create_func(_str_wrapper))
builtins.add_symbol("len", _create_func(_len_wrapper))

modmap = {
    "main": "print(\"Hello, World!\")\n",
}

print("SELF TEST")

tks = Lexer("main", "print(\"Hello, World!\")\n").all_tokens()
i = 0
while i < len(tks):
    print(tks[i].__str__())
    i += 1

# err = evaluate(builtins, modmap, "main", True)
# if err != None:
#     e = err.copy()
#     e.correct_editor_view() 
#     print(e.__str__())
