import scopekind
import objkind
from parser import parse
from evaluator import _Scope, _Builtin_Func, _Py_Object, evaluate

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

program = "def generation(prev, curr):\n"
program += "    i = 1\n"
program += "    while i < len(prev)-1:\n"
program += "        curr[i] = rule(prev, i)\n"
program += "        i += 1\n"
program += "    return curr\n"
program += "rulemap = {\n"
program += "    \"   \": \" \",\n"
program += "    \"O  \": \" \",\n"
program += "    \" O \": \"O\",\n"
program += "    \"  O\": \"O\",\n"
program += "    \"OO \": \"O\",\n"
program += "    \"O O\": \"O\",\n"
program += "    \" OO\": \"O\",\n"
program += "    \"OOO\": \" \",\n"
program += "}\n"
program += "def rule(prev, i):\n"
program += "    chunk = make_str(prev[i-1:i+2])\n"
program += "    return rulemap[chunk]\n"
program += "def make_array(str):\n"
program += "    out = []\n"
program += "    i = 0\n"
program += "    while i < len(str):\n"
program += "        out += [str[i]]\n"
program += "        i += 1\n"
program += "    return out\n"
program += "def make_str(chunk):\n"
program += "    out = \"\"\n"
program += "    i = 0\n"
program += "    while i < len(chunk):\n"
program += "        out += chunk[i]\n"
program += "        i += 1\n"
program += "    return out\n"
program += "A = make_array(\"                                O \")\n"
program += "B = make_array(\"                                  \")\n"
program += "i = 0\n"
program += "while i < 32:\n"
program += "    print(make_str(A))\n"
program += "    B = generation(A, B)\n"
program += "    C = A\n"
program += "    A = B\n"
program += "    B = C\n"
program += "    i += 1\n"

modmap = {
    "main": program,
}

err = evaluate(builtins, modmap, "main", False)
if err != None:
    e = err.copy()
    e.correct_editor_view() 
    print(e.__str__())
