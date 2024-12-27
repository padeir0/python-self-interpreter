def Exemplo_1():
    a = [0, 1, 2]    
    b = a[1]
    b = 9

    i = 0
    while i < len(a):
        print(a[i])
        i += 1

def Exemplo_2():
    class Ref:
        def __init__(self, obj):
            self.obj = obj

    a = [Ref(0), Ref(1), Ref(2)]
    b = a[1]
    b.obj = 9

    i = 0
    while i < len(a):
        print(a[i].obj)
        i += 1

print("Exemplo 1:")
Exemplo_1()
print("\nExemplo 2:")
Exemplo_2()
