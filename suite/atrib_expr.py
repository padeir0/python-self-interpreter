def test():
    a = 1
    if a != 1:
        return False

    list = [0, 0]
    list[0] = 1
    list[1] = 2
    if list[0] != 1 or list[1] != 2:
        return False

    dict = {"a":0, "b":0}
    dict["a"] = 1
    dict["b"] = 2
    if dict["a"] != 1 or dict["b"] != 2:
        return False

    return True

if test():
    print("atrib_expr: OK!")
else:
    print("atrib_expr: FAIL!")
