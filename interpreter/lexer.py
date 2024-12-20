import lexkind
from core import Position, Range, Lexeme, Error

def _is_alpha(s):
    return (s >= "a" and s <= "z") or (s >= "A" and s <= "Z")

def _is_digit(s):
    return s >= "0" and s <= "9"

def _is_identifier(s):
    return _is_alpha(s) or _is_digit(s) or s == "_"

class Lexer:
    def __init__(self, string):
        self.string = string
        self.start = 0
        self.end = 0
        self.range = Range(Position(0, 0), Position(0, 0))
        self.word = None
        self.peeked = None

    def next(self):
        if self.peeked != None:
            self.word = self.peeked
            self.peeked = None
        else:
            self.word = self._any()
        self._advance()
        return self.word

    def peek(self):
        if self.peeked == None:
            self.peeked = self._any()
        return self.peeked

    def all_tokens(self):
        all = []
        l = self.next()
        while l.kind != lexkind.EOF:
            all += [l]
            l = self.next()
        return all

    def _selected(self):
        return self.string[self.start:self.end]

    def _peek_rune(self):
        if self.end >= len(self.string):
            return ""
        return self.string[self.end]

    def _next_rune(self):
        if self.end >= len(self.string):
            return ""
        r = self.string[self.end]
        self.end += 1

        self.range.end.column += 1
        if r == "\n":
            self.range.end.line += 1
            self.range.end.column = 0
        
        return r

    def _emit(self, kind):
        s = self.string[self.start:self.end]
        return Lexeme(s, kind, self.range.copy())

    def _advance(self):
        self.start = self.end
        self.range.start = self.range.end.copy()

    # TODO: incluir comentários aqui
    def _ignore_whitespace(self):
        r = self._peek_rune()
        while r == " ":
            self._next_rune()
            r = self._peek_rune()
        self._advance()

    def _any(self):
        self._ignore_whitespace()
        r = self._peek_rune()
        if _is_digit(r):
            return self._number()
        elif _is_alpha(r):
            return self._identifier()
        elif r == "\"":
            return self._string()
        elif r == "+":
            self._next_rune()
            r = self._peek_rune()
            if r == "=":
                self._next_rune()
                return self._emit(lexkind.ASSIGN_PLUS)
            else:
                return self._emit(lexkind.PLUS)
        elif r == "-":
            self._next_rune()
            r = self._peek_rune()
            if r == "=":
                self._next_rune()
                return self._emit(lexkind.ASSIGN_MINUS)
            else:
                return self._emit(lexkind.MINUS)
        elif r == "*":
            self._next_rune()
            r = self._peek_rune()
            if r == "=":
                self._next_rune()
                return self._emit(lexkind.ASSIGN_MULT)
            else:
                return self._emit(lexkind.MULT)
        elif r == "/":
            self._next_rune()
            r = self._peek_rune()
            if r == "=":
                self._next_rune()
                return self._emit(lexkind.ASSIGN_DIV)
            else:
                return self._emit(lexkind.DIV)
        elif r == "%":
            self._next_rune()
            r = self._peek_rune()
            if r == "=":
                self._next_rune()
                return self._emit(lexkind.ASSIGN_REM)
            else:
                return self._emit(lexkind.REM)
        elif r == "(":
            self._next_rune()
            return self._emit(lexkind.LEFT_PAREN)
        elif r == ")":
            self._next_rune()
            return self._emit(lexkind.RIGHT_PAREN)
        elif r == "[":
            self._next_rune()
            return self._emit(lexkind.LEFT_BRACKET)
        elif r == "]":
            self._next_rune()
            return self._emit(lexkind.RIGHT_BRACKET)
        elif r == "{":
            self._next_rune()
            return self._emit(lexkind.LEFT_BRACES)
        elif r == "}":
            self._next_rune()
            return self._emit(lexkind.RIGHT_BRACES)
        elif r == ":":
            self._next_rune()
            return self._emit(lexkind.COLON)
        elif r == ",":
            self._next_rune()
            return self._emit(lexkind.COMMA)
        elif r == ".":
            self._next_rune()
            return self._emit(lexkind.DOT)
        elif r == "=":
            self._next_rune()
            r = self._peek_rune()
            if r == "=":
                self._next_rune()
                return self._emit(lexkind.EQUALS)
            else:
                return self._emit(lexkind.ASSIGN)
        elif r == ">":
            self._next_rune()
            r = self._peek_rune()
            if r == "=":
                self._next_rune()
                return self._emit(lexkind.GREATER_OR_EQUALS)
            else:
                return self._emit(lexkind.GREATER)
        elif r == "<":
            self._next_rune()
            r = self._peek_rune()
            if r == "=":
                self._next_rune()
                return self._emit(lexkind.LESS_OR_EQUALS)
            else:
                return self._emit(lexkind.LESS)
        elif r == "!":
            self._next_rune()
            r = self._peek_rune()
            if r == "=":
                self._next_rune()
                return self._emit(lexkind.DIFF)
            else:
                return Lexeme(r, lexkind.INVALID, self.range.copy())
        elif r == "\n":
            self._next_rune()
            return self._emit(lexkind.NL)
        elif r == "":
            return Lexeme("", lexkind.EOF, self.range.copy())
        else:
            self._next_rune()
            return Lexeme(r, lexkind.INVALID, self.range.copy())

    def _number(self):
        r = self._peek_rune()
        while _is_digit(r):
            self._next_rune()
            r = self._peek_rune()
        return self._emit(lexkind.NUM)

    def _identifier(self):
        r = self._peek_rune()
        while _is_identifier(r):
            self._next_rune()
            r = self._peek_rune()

        s = self._selected()
        if s == "True":
            return self._emit(lexkind.TRUE)
        elif s == "False":
            return self._emit(lexkind.FALSE)
        elif s == "not":
            return self._emit(lexkind.NOT)
        elif s == "and":
            return self._emit(lexkind.AND)
        elif s == "or":
            return self._emit(lexkind.OR)
        elif s == "self":
            return self._emit(lexkind.SELF)
        elif s == "None":
            return self._emit(lexkind.NONE)
        elif s == "if":
            return self._emit(lexkind.IF)
        elif s == "elif":
            return self._emit(lexkind.ELIF)
        elif s == "else":
            return self._emit(lexkind.ELSE)
        elif s == "for":
            return self._emit(lexkind.FOR)
        elif s == "in":
            return self._emit(lexkind.IN)
        elif s == "while":
            return self._emit(lexkind.WHILE)
        elif s == "return":
            return self._emit(lexkind.RETURN)
        elif s == "def":
            return self._emit(lexkind.DEF)
        elif s == "class":
            return self._emit(lexkind.CLASS)
        elif s == "import":
            return self._emit(lexkind.IMPORT)
        elif s == "from":
            return self._emit(lexkind.FROM)
        elif s == "pass":
            return self._emit(lexkind.PASS)
        return self._emit(lexkind.ID)

    def _string(self):
        r = self._peek_rune()
        if r == "\"":
            self._next_rune()
            r = self._peek_rune()
        ok = True
        while ok:
            if r == "\\":
                self._next_rune()
                r = self._peek_rune()
                # permitimos apenas \n e \"
                if not r in ["n", "\""]:
                    return self._emit(lexkind.INVALID)
            elif r == "\"":
                ok = False
            self._next_rune()
            r = self._peek_rune()
        return self._emit(lexkind.STR)

