def generation(prev, curr):
    i = 1
    while i < len(prev)-1:
        curr[i] = rule(prev, i)
        i += 1
    return curr

rulemap = {
    "   ": " ",
    "O  ": " ",
    " O ": "O",
    "  O": "O",
    "OO ": "O",
    "O O": "O",
    " OO": "O",
    "OOO": " ",
}

def rule(prev, i):
    chunk = make_str(prev[i-1:i+2])
    return rulemap[chunk]

def make_array(str):
    out = []
    i = 0
    while i < len(str):
        out += [str[i]]
        i += 1
    return out

def make_str(chunk):
    out = ""
    i = 0
    while i < len(chunk):
        out += chunk[i]
        i += 1
    return out

A = make_array("                                O ")
B = make_array("                                  ")
i = 0
while i < 32:
    print(make_str(A))
    B = generation(A, B)

    C = A
    A = B
    B = C

    i += 1
