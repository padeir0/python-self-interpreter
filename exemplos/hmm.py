some = {"a": 1, "b": 2}

def a():
    global some
    return some

a()["a"] = 2

print(some)
