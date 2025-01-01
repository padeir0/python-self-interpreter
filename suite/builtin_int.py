def test():
    if int("0") != 0:
        return False
    if int("123") != 123:
        return False
    if int("-123") != -123:
        return False
    return True

if test():
    print("builtin_int: OK!")
else:
    print("builtin_int: FAIL!")
