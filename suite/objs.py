class S:
    def __init__(s):
        self.s = s
        self.i = 0
    def next(self):
        if self.i >= len(self.s):
            return ""
        out = self.s[self.i]
        self.i += 1
        return out

def chars(s):
    all = []
    c = s.next()
    while c != "":
        all += [c]
        c = s.next()
    return all

def copy(s):
    all = ""
    c = s.next()
    while c != "":
        all += c
        c = s.next()
    return all

def test():
    if copy(S("text")) != "text":
        return False
    if chars(S("text")) != ["t", "e", "x", "t"]:
        return False
    return True

if test():
    print("objs: OK!")
else:
    print("objs: FAIL!")
