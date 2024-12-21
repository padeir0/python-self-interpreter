INVALID = -1

NUM = 0
STR = 1
ID = 2

TRUE = 3
FALSE = 4
NOT = 5
AND = 6
OR = 7
SELF = 8
NONE = 9
IF = 10
ELIF = 11
ELSE = 12
FOR = 13
WHILE = 14
RETURN = 15
DEF = 16
CLASS = 17
IMPORT = 18
FROM = 19
PASS = 101
IN = 102

PLUS = 20
MINUS = 21
MULT = 22
DIV = 23
REM = 24

ASSIGN = 25
ASSIGN_PLUS = 26
ASSIGN_MINUS = 27
ASSIGN_MULT = 28
ASSIGN_DIV = 29
ASSIGN_REM = 30

EQUALS = 31
DIFF = 32
GREATER = 33
GREATER_OR_EQUALS = 34
LESS = 35
LESS_OR_EQUALS = 36

LEFT_PAREN = 37
RIGHT_PAREN = 38
LEFT_BRACKET = 39
RIGHT_BRACKET = 40
LEFT_BRACE = 41
RIGHT_BRACE = 42

COLON = 43
COMMA = 44
DOT = 45

NL = 46
EOF = 47



def to_string(kind):
    if kind == INVALID:
        return "INVALID"

    elif kind == NUM:
        return "NUM"
    elif kind == STR:
        return "STR"
    elif kind == ID:
        return "ID"

    elif kind == TRUE:
        return "TRUE"
    elif kind == FALSE:
        return "FALSE"
    elif kind == NOT:
        return "NOT"
    elif kind == AND:
        return "AND"
    elif kind == OR:
        return "OR"
    elif kind == SELF:
        return "SELF"
    elif kind == NONE:
        return "NONE"
    elif kind == IF:
        return "IF"
    elif kind == ELIF:
        return "ELIF"
    elif kind == ELSE:
        return "ELSE"
    elif kind == FOR:
        return "FOR"
    elif kind == WHILE:
        return "WHILE"
    elif kind == RETURN:
        return "RETURN"
    elif kind == DEF:
        return "DEF"
    elif kind == CLASS:
        return "CLASS"
    elif kind == IMPORT:
        return "IMPORT"
    elif kind == FROM:
        return "FROM"
    elif kind == PASS:
        return "PASS"
    elif kind == IN:
        return "IN"

    elif kind == PLUS:
        return "PLUS"
    elif kind == MINUS:
        return "MINUS"
    elif kind == MULT:
        return "MULT"
    elif kind == DIV:
        return "DIV"
    elif kind == REM:
        return "REM"

    elif kind == ASSIGN:
        return "ASSIGN"
    elif kind == ASSIGN_PLUS:
        return "ASSIGN_PLUS"
    elif kind == ASSIGN_MINUS:
        return "ASSIGN_MINUS"
    elif kind == ASSIGN_MULT:
        return "ASSIGN_MULT"
    elif kind == ASSIGN_DIV:
        return "ASSIGN_DIV"
    elif kind == ASSIGN_REM:
        return "ASSIGN_REM"

    elif kind == EQUALS:
        return "EQUALS"
    elif kind == DIFF:
        return "DIFF"
    elif kind == GREATER:
        return "GREATER"
    elif kind == GREATER_OR_EQUALS:
        return "GREATER_OR_EQUALS"
    elif kind == LESS:
        return "LESS"
    elif kind == LESS_OR_EQUALS:
        return "LESS_OR_EQUALS"

    elif kind == LEFT_PAREN:
        return "LEFT_PAREN"
    elif kind == RIGHT_PAREN:
        return "RIGHT_PAREN"
    elif kind == LEFT_BRACKET:
        return "LEFT_BRACKET"
    elif kind == RIGHT_BRACKET:
        return "RIGHT_BRACKET"
    elif kind == LEFT_BRACE:
        return "LEFT_BRACE"
    elif kind == RIGHT_BRACE:
        return "RIGHT_BRACE"

    elif kind == COLON:
        return "COLON"
    elif kind == COMMA:
        return "COMMA"
    elif kind == DOT:
        return "DOT"

    elif kind == NL:
        return "NL"
    elif kind == EOF:
        return "EOF"
    return "??"
