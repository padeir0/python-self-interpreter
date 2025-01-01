def test():
    def make_adder(n):
        def adder(m):
            return n + m
        return adder

    add_5 = make_adder(5)

    if add_5(0) != 5:
        return False
    if add_5(1) != 6:
        return False
    if add_5(-5) != 0:
        return False
    return True

if test():
    print("closure: OK!")
else:
    print("closure: FAIL!")
