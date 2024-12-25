INVALID = -1
TERMINAL = 0        # None
BLOCK = 1           # [sttm_1, sttm_2, ...]
ID_LIST = 2         # [id_1, id_2, ...]
EXPR_LIST = 3       # [expr_1, expr_2, ...]
ARG_LIST = 4        # [arg_1, arg_2, ...]
KEY_VALUE_LIST = 5  # [kv_1, kv_2, ...]
FROM_IMPORT = 6     # [id, idlist]
IMPORT = 7          # [id_list]
WHILE = 9           # [expr, block]
IF = 10             # [exp, block, elifs, else]
ELIF = 11           # [exp, block]
ELSE = 12           # [block]
CLASS = 13          # [id, methods]
METHODS = 14        # [method_1, method_2, ...]
TUPLE = 15          # [expr_list]
BIN_OPERATOR = 16   # [left_op, right_op]
ASSIGN = 17          # [lhs_expr, rhs_expr]
AUGMENTED_ASSIGN = 18 # [lhs_expr, rhs_expr]
MULTI_ASSIGN = 19   # [lhs_expr_list, rhs_expr]
SLICE = 20          # [expr_1, expr_2, operand_expr]
FIELD_ACCESS = 21   # [field, operand_expr]
FUNC = 22           # [id, args, block]
CALL = 23           # [expr_list, operand_expr]
LIST = 24           # [expr_list]
DICT = 25           # [kv_list]
INDEX = 26          # [expr_1, operand_expr]
KEY_VALUE_PAIR = 27 # [key, value]
ELIF_LIST = 28      # [elif1, elif2, ...]
UNA_OPERATOR = 29   # [operand]
RETURN = 30         # [expr_list]

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
    elif kind == BIN_OPERATOR: 
        return "BIN_OPERATOR"
    elif kind == UNA_OPERATOR: 
        return "UNA_OPERATOR"
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
    elif kind == ELIF_LIST:
        return "ELIF_LIST"
    elif kind == RETURN:
        return "RETURN"
    else:
        return "???"
