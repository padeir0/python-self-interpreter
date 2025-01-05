class MyObj:
    def __init__(self, value):
        self.value = value
    def inc_less(self, value):
        self.value += 1
        return self.value < value
    def inc_eq(self, value):
        self.value += 1
        return self.value < value

def thing_if():
    obj = MyObj(0)
    if obj.inc_eq(0):
        return obj.value
    elif obj.inc_eq(1):
        return obj.value
    elif obj.inc_eq(2):
        return obj.value
    else:
        return obj.value # 3

def thing_while():
    obj = MyObj(0)

    while obj.inc_less(10):
        if obj.value == 5:
            return obj.value

    return -1

def thing_do():
    obj = MyObj(0)

    do:
        if obj.value == 5:
            return obj.value
    while obj.inc_less(10)

    return -1

def test():
    if thing_while() != 5:
        return False
    if thing_do() != 5:
        return False
    if thing_if() != 3:
        return False
    return True

if test():
    print("impure_cond: OK!")
else:
    print("impure_cond: FAIL!")
