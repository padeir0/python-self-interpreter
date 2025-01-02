def test():
    n = 1
    i = 0
    while i < 10:
        n *= 2
        i += 1

    if n != 1024:
        return False
    return True

if test():
    print("while_loop: OK")
else:
    print("while_loop: FAIL")
