def is_one_of(word_kind, kinds):
    i = 0
    while i < len(kinds):
        kind = kinds[i]
        if word_kind == kind:
            return True
        i += 1
    return False

def test():
    if not is_one_of(1, [1, 2, 3]):
        return False
    if not is_one_of(2, [1, 2, 3]):
        return False
    if not is_one_of(3, [1, 2, 3]):
        return False
    return True

if test():
    print("iter: OK!")
else:
    print("iter: FAIL!")
