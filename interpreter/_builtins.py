import objkind
import scopekind
from evaluator import _Scope, _Builtin_Func, _Py_Object

def _str_dict(dict):
    keys = list(dict.value.keys())
    out = "{"
    i = 0
    while i < len(keys):
        key = keys[i]
        value = dict.value[key]
        key_str = str(key)
        if type(key) is str:
            key_str = "\"" + key_str + "\""
        out += key_str + ": " + _str_obj(value)
        if i + 1 < len(keys):
            out += ", "
        i += 1
    out += "}"
    return out

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
        return obj.value
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
        return "class<" +obj.value.name+ ">" + str(obj.value)
    else:
        return "<unknown>"

def _obj_none():
    return _Py_Object(objkind.NONE, None, False)

def _print_wrapper(obj):
    try:
        print(_str_obj(obj))
    except:
        pass
    return _obj_none()

def _int_wrapper(obj):
    if obj.is_kind(objkind.STR):
        try:
            value = int(obj.value)
            return _Py_Object(objkind.NUM, value, False)
        except:
            pass
    return _obj_none()

def _str_wrapper(obj):
    try:
        value = _str_obj(obj)
        return _Py_Object(objkind.STR, value, False)
    except:
        pass
    return _obj_none()

def _len_wrapper(obj):
    if obj.is_kinds([objkind.LIST, objkind.STR]):
        try:
            value = len(obj.value)
            return _Py_Object(objkind.NUM, value, False)
        except:
            pass
    return _obj_none()

def _create_func(func):
    bf = _Builtin_Func(1, func)
    return _Py_Object(objkind.BUILTIN_FUNC, bf, False)

def create_builtin_scope():
    s = _Scope(None, scopekind.BUILTIN)
    s.add_symbol("print", _create_func(_print_wrapper))
    s.add_symbol("int", _create_func(_int_wrapper))
    s.add_symbol("str", _create_func(_str_wrapper))
    s.add_symbol("len", _create_func(_len_wrapper))
    return s

