def fact(n):
    if n <= 0:
        return 1
    return n * fact(n-1)

def test():
    if fact(0) != 1:
        return False
    if fact(1) != 1:
        return False
    if fact(2) != 2:
        return False
    if fact(3) != 6:
        return False
    if fact(4) != 24:
        return False
    if fact(5) != 120:
        return False
    return True

if test():
    print("fact: OK!")
else:
    print("fact: FAIL!")
