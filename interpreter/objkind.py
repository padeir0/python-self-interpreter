INVALID       = -1
NUM           = 0
STR           = 1
LIST          = 2
DICT          = 3
USER_OBJECT   = 4
USER_FUNCTION = 6
MODULE        = 7
BUILTIN_FUNC  = 8
NONE          = 9
BOOL          = 10
USER_CLASS    = 11

def to_str(kind):
    if kind == INVALID:
        return "INVALID"
    elif kind == NUM:
        return "NUM"
    elif kind == STR:
        return "STR"
    elif kind == LIST:
        return "LIST"
    elif kind == DICT:
        return "DICT"
    elif kind == USER_OBJECT:
        return "USER_OBJECT"
    elif kind == USER_FUNCTION:
        return "USER_FUNCTION"
    elif kind == MODULE:
        return "MODULE"
    elif kind == BUILTIN_FUNC:
        return "BUILTIN_FUNC"
    elif kind == NONE:
        return "NONE"
    elif kind == BOOL:
        return "BOOL"
    elif kind == USER_CLASS:
        return "USER_CLASS"
    else:
        return "???"
