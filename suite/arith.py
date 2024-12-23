def test():
    if 1+2+3+4 != 10:
        print("ERROR: 1+2+3+4 != 10")
        return False
    if (1+2)/(3) != 1:
        print("ERROR: 1+2/3 != 1")
        return False
    if (1+2)*(3) != 9:
        print("ERROR: (1+2)*(3) != 9")
        return False
    return True

print("arith:")
if test():
    print("OK")
