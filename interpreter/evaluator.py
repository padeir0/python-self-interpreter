import lexkind

def evaluate(node):
    if node.value.kind == lexkind.PLUS:
        return evaluate(node.left()) + evaluate(node.right())
    elif node.value.kind == lexkind.MINUS:
        return evaluate(node.left()) - evaluate(node.right())
    elif node.value.kind == lexkind.NEG:
        return -evaluate(node.left())
    elif node.value.kind == lexkind.MULT:
        return evaluate(node.left()) * evaluate(node.right())
    elif node.value.kind == lexkind.DIV:
        return evaluate(node.left()) / evaluate(node.right())
    elif node.value.kind == lexkind.NUM:
        return int(node.value.text)
