def test():
    if not (1 in [1, 2, 3]):
        return False
    if not (2 in [1, 2, 3]):
        return False
    if not (3 in [1, 2, 3]):
        return False
    return True

if test():
    print("in: OK!")
else:
    print("in: FAIL!")
