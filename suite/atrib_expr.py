def test():
    a = 1
    if a != 1:
        print("ERROR: a is not 1")
        return False

    list = [0, 0]
    list[0] = 1
    list[1] = 2
    if list[0] != 1 or list[1] != 2:
        print("ERROR: failed assignment on list")
        return False

    list = {"a":0, "b":0}
    list["a"] = 1
    list["b"] = 2
    if list["a"] != 1 or list["b"] != 2:
        print("ERROR: failed assignment on dict")
        return False

    return True

print("atrib_expr:")
if test():
    print("OK")

