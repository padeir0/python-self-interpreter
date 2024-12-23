INVALID = -1
TERMINAL = 0
BLOCK = 1
ID_LIST = 2        # [id_1, id_2, ...]
EXPR_LIST = 3      # [expr_1, expr_2, ...]
ARG_LIST = 4       # [arg_1, arg_2, ...]
KEY_VALUE_LIST = 5  # [kv_1, kv_2, ...]
FROM_IMPORT = 6    # [id, idlist]
IMPORT = 7         # [idlist]
FOR = 8
WHILE = 9
IF = 10
ELIF = 11
ELSE = 12
CLASS = 13
METHODS = 14
TUPLE = 15
OPERATOR = 16
ASSIGN = 17
AUGMENTED_ASSIGN = 18
MULTI_ASSIGN = 19
SLICE = 20
FIELD_ACCESS = 21
FUNC = 22
CALL = 23
LIST = 24
DICT = 25
INDEX = 26
KEY_VALUE_PAIR = 27

def to_str(kind):
    if kind == INVALID: 
        return "INVALID"
    elif kind == TERMINAL: 
        return "TERMINAL"
    elif kind == BLOCK: 
        return "BLOCK"
    elif kind == ID_LIST: 
        return "ID_LIST"
    elif kind == EXPR_LIST: 
        return "EXPR_LIST"
    elif kind == ARG_LIST: 
        return "ARG_LIST"
    elif kind == KEY_VALUE_LIST: 
        return "KEY_VALUE_LIST"
    elif kind == FROM_IMPORT: 
        return "FROM_IMPORT"
    elif kind == IMPORT: 
        return "IMPORT"
    elif kind == FOR: 
        return "FOR"
    elif kind == WHILE: 
        return "WHILE"
    elif kind == IF: 
        return "IF"
    elif kind == ELIF: 
        return "ELIF"
    elif kind == ELSE: 
        return "ELSE"
    elif kind == CLASS: 
        return "CLASS"
    elif kind == METHODS: 
        return "METHODS"
    elif kind == TUPLE: 
        return "TUPLE"
    elif kind == OPERATOR: 
        return "OPERATOR"
    elif kind == ASSIGN: 
        return "ASSIGN"
    elif kind == AUGMENTED_ASSIGN: 
        return "AUGMENTED_ASSIGN"
    elif kind == MULTI_ASSIGN: 
        return "MULTI_ASSIGN"
    elif kind == SLICE: 
        return "SLICE"
    elif kind == FIELD_ACCESS:
        return "FIELD_ACCESS"
    elif kind == FUNC: 
        return "FUNC"
    elif kind == CALL:
        return "CALL"
    elif kind == LIST:
        return "LIST"
    elif kind == DICT:
        return "DICT"
    elif kind == INDEX:
        return "INDEX"
    elif kind == KEY_VALUE_PAIR:
        return "KEY_VALUE_PAIR"
    else:
        return "???"
