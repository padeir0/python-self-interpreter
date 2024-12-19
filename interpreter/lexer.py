import lexkind
from core import Lexeme, Error

class Lexer:
    def __init__(self, string):
        self.string = string
        self.start = 0
        self.end = 0
        self.word = None

    def next(self):
        self.word = self._any()
        return self.word

    def alltokens(self):
        all = []
        l = self.next()
        while l.kind != lexkind.EOF:
            all += [l]
            l = self.next()
        return all

    def _peek_rune(self):
        if self.end >= len(self.string):
            return ""
        return self.string[self.end]

    def _next_rune(self):
        if self.end >= len(self.string):
            return ""
        r = self.string[self.end]
        self.end += 1
        return r

    def _emit(self, kind):
        s = self.string[self.start:self.end]
        self.start = self.end
        return Lexeme(s, kind)

    def _ignore(self):
        self.start = self.end

    def _ignore_whitespace(self):
        r = self._peek_rune()
        while r == " ":
            self._next_rune()
            r = self._peek_rune()
        self._ignore()

    def _any(self):
        self._ignore_whitespace()
        r = self._peek_rune()
        if r.isnumeric():
            return self._number()
        elif r == "+":
            self._next_rune()
            return self._emit(lexkind.PLUS)
        elif r == "-":
            self._next_rune()
            return self._emit(lexkind.MINUS)
        elif r == "*":
            self._next_rune()
            return self._emit(lexkind.MULT)
        elif r == "/":
            self._next_rune()
            return self._emit(lexkind.DIV)
        elif r == "~":
            self._next_rune()
            return self._emit(lexkind.NEG)
        elif r == "(":
            self._next_rune()
            return self._emit(lexkind.LEFTPAREN)
        elif r == ")":
            self._next_rune()
            return self._emit(lexkind.RIGHTPAREN)
        elif r == "":
            return Lexeme("", lexkind.EOF)
        else:
            self._next_rune()
            return Lexeme(r, lexkind.INVALID)

    def _number(self):
        r = self._peek_rune()
        while r.isnumeric():
            self._next_rune()
            r = self._peek_rune()
        return self._emit(lexkind.NUM)

