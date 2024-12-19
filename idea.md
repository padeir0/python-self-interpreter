# Python self-interpreter

Objective: implement a simple subset of python that can interpret itself,
while still looking like python.

Features:
 - Module system: will be implemented using a dictionary of all files in a directory,
the interpreter will have an eval function that accepts a str->str dictionary,
that maps module names to file contents, and a str,
that represents the name of the main module. When calling the interpreter on a folder,
the full folder will be transformed in this map, so that the interpreter can use it
without depending on built-in open, os library and "with" construct
 - Objects: we need objects because python is oop, and we will need to implement trees
using this.
 - Dictionaries, lists, numbers and strings: since python already provides it
 - The only necessary built-ins are `print` and `len`, i think
 - Control flow is `for`, `while`, `if` and `return`
 - Comments with `#`

## Grammar

```ebnf
WhiteSpace = ' ' | '\r' | Comment.
Comment = '#' {ascii} nl.
nl = '\n'.

Module = Block.
Block = { Statement NL }.
NL = nl {nl}.

Statement = While  | If    | For | Atrib_Expr
          | Return | Class | Func
          | Import | FromImport.

Import = 'import' IdList.
FromImport = 'from' id 'import' IdList.
IdList = id {',' id}.

While = 'while' Expr ':' NL >Block.

If = 'if' Expr ':' NL >Block {Elif} [Else].
Elif = 'elif' Expr ':' NL >Block.
Else = 'else' ':' NL >Block.

For = 'for' Expr 'in' Expr ':' NL >Block.
Atrib_Expr = Expr ['=' Expr].
Return = 'return' ExprList.

Class = 'class' id ':' NL >Methods.
Methods = {Func}.

Func = 'def' id '[' ArgList ']' ':' NL >Block.
ArgList = Arg {',' Arg}.
Arg = 'self' | id.

MultiLine_ExprList = Expr {',' [NL] Expr} [','].
ExprList = Expr {',' Expr}.
Expr = And {'or' And}.
And = Comp {'and' Comp}.
Comp = Sum {compOp Sum}.
compOp = '==' | '!=' | '>' | '>=' | '<' | '<='.
Sum = Mult {sumOp Mult}.
sumOp = '+' | '-'.
Mult = UnaryPrefix {multOp UnaryPrefix}.
multOp = '*' | '/' | '%'.
UnaryPrefix = {Prefix} UnarySuffix.
UnarySuffix = Term {Suffix}.
Term = 'self' | 'None' | bool | num
       | str  | id     | NestedExpr_Tuple
       | Dict | List.

prefix = 'not' | '-'.
Suffix = Call
    | DotAccess
    | Index.
Call = '(' [MultiLine_ExprList] ')'.
Index = '[' [MultiLine_ExprList] ']'.
DotAccess = '.' id.
Dict = '{' AtribList '}'.
List = '[' AtribList ']'.
AtribList = Atrib_Expr {',' [NL] Atrib_Expr}.
Atrib_Expr = Expr [Assign_Op Expr].
NestedExpr_Tuple = '(' MultiLine_ExprList ')'.

Assign_Op = '=' | '+=' | '-=' | '*=' | '/=' | '%='.

bool = 'True' | 'False'.
num = .
str = .
id = /[a-zA-Z_][a-zA-Z0-9_]*/.
```
