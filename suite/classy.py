class A:
    def __init__(self, prop):
        self.prop = prop
    def double(self):
        self.prop *= 2

def test():
    # for some reason, after evaluating __init__
    # the interpreter does not return to the current
    # call node, and keeps the environment created inside __init__
    # TODO: fix this bug
    myA = A(1)
    if myA.prop != 1:
        return False
    myA.double()
    if myA.prop != 2:
        return False
    myA.double()
    if myA.prop != 4:
        return False
    myA.double()
    if myA.prop != 8:
        return False
    return True

if test():
    print("classy: OK!")
else:
    print("classy: FAIL!")
