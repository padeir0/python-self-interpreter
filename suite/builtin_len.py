def test():
    if len([1, 2, 3]) != 3:
        return False
    if len([]) != 0:
        return False
    if len("abc") != 3:
        return False
    if len("") != 0:
        return False
    return True

if test():
    print("builtin_len: OK!")
else:
    print("builtin_len: FAIL!")
