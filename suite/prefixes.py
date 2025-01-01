def test():
    if --1 != 1:
        return False
    if not not True != True:
        return False
    if not not not False != True:
        return False
    return True

if test():
    print("prefixes: OK!")
else:
    print("prefixes: FAIL!")
