def test():
    if 1+2+3+4 != 10:
        return False
    if (1+2)/(3) != 1:
        return False
    if (1+2)*(3) != 9:
        return False
    return True

if test():
    print("arith: OK!")
else:
    print("arith: FAIL!")
