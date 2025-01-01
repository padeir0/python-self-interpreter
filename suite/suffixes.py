def test():
    def f():
        return [1, 2, 3]
    if f()[0] != 1 or f()[1] != 2 or f()[2] != 3:
        return False
    if f()[1:2][0] != 2:
        return False
    return True


if test():
    print("suffixes: OK!")
else:
    print("suffixes: FAIL!")
