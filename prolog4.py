from dataclasses import dataclass
from typing import ChainMap, Generator, Iterable, Mapping, List
dataclass = dataclass(eq = True, frozen=True)

# Term := Relation([Term]) | Var | Const
# Predicate := Top | Just(Relation) | Conj(Predicate) | Disj(Predicate) | Not(Predicate)
# Rule := Rule (Term Predicate)
# Env := Mapping(Term Term)
# TopLevel := [Rule]


class Term: pass
class Relation(Term): 
    def __init__(self, *args): self.data = args
    def __getitem__(self, idx): return self.data[idx]
    def __len__(self): return len(self.data)
    def __repr__(self): return str(self.data)

@dataclass
class Var(Term): x : object
@dataclass
class Const(Term): x : object

class Predicate: pass
@dataclass
class Rule:
    term : Term
    body : Predicate

class Top(Predicate): pass
@dataclass
class Not(Predicate): 
    body : Predicate
@dataclass
class Conj(Predicate): 
    clauses : List[Predicate]
@dataclass
class Disj(Predicate): 
    clauses : List[Predicate]
@dataclass
class Just(Predicate):
    body : Relation

# reduce a variable into a constant if it can be reduced in the env
def walk(var : Term, env : Mapping):
    if isinstance(var, Var) and var in env: return walk(env[var], env)
    else:                                   return var

# unify two terms
def unify(u : Term, v : Term, env : Mapping = dict()) -> Mapping:
    if env is None: return None
    if isinstance(u, Relation) and isinstance(v, Relation):
        if len(u) != len(v): return None
        for u_, v_ in zip(u, v):
            env = unify(u_, v_, env)
        return env
    u = walk(u, env)
    v = walk(v, env)
    if u == v:              return env    
    if isinstance(u, Var):  return {u : v, **env}
    if isinstance(v, Var):  return {v : u, **env}
    else:                   return None

def query(u : Term, topLevel : List[Rule], env = dict()):
    """
    if there is a result, yield env else return None
    """
    for i in topLevel:
        e = unify(u, i.term, env)
        if e is not None:
            yield from match(i.body, e, topLevel)

# check if a predicate is true in current env
# if is true yield env
def match(pred : Predicate, env, topLevel):
    if isinstance(pred, Top):    yield env
    elif isinstance(pred, Just): yield from query(pred.body, topLevel, env)
    elif isinstance(pred, Conj):
        if len(pred.clauses) == 1:
            yield from match(pred.clauses[0], env, topLevel)
        else:
            for e in match(pred.clauses[0], env, topLevel):
                yield from match(Conj(pred.clauses[1:]), e, topLevel)
    elif isinstance(pred, Disj):
        for _pred in pred.clauses:
            e = match(_pred, env, topLevel)
            if e is not None: yield e
    elif isinstance(pred, Not):
        temp = match(pred.body, topLevel, env)
        if temp is not None: return None
        else:                return env


def testWalk():
    assert (Const(10) ==
        walk(Var(1), {Var(1) : Const(10)}))
    assert (Const(10) ==
        walk(Var(1), {Var(1) : Var(2), Var(2) : Const(10)}))

def testUnify():
    assert({Var(1) : Var(2), Var(2) : Const(10)} ==
        dict(unify(Relation(Var(1), Const(2)), Relation(Var(2), Var(2)))))
    assert({Var(2) : Relation(Const(2), Const(2)), Var(1) : Var(2)} ==
        dict(unify(Relation(Var(1), Relation(Const(2), Const(2))), Relation(Var(2), Var(2)))))
    pass



# def testQuery():
#     r = Relation(Const("friend"), Const("Bob"), Var(1))
#     rules = [
#         Rule(Relation(Const("friend"), Const("Bob"), Const("Alice")), Top()),
#         Rule(Relation(Const("friend"), Const("Charlie"), Const("Alice")), Top()),
#         Rule(Relation(Const("friend"), Const("David"), Const("Bob")), Top()),
#         # Rule(Relation(Const("friend"), Var(3), Var(4)), 
#         #     Just(Relation(Const("friend"), Var(4), Var(3)))),
#         Rule(Relation(Const("friend"), Var(5), Var(6)),
#             Conj([
#                 Just(Relation(Const("friend"), Var(5), Var(7))),
#                 Just(Relation(Const("friend"), Var(7), Var(6)))
#             ])),
#         # Rule(Relation(Const("friend"), Const("Bob"), Var(2)), 
#         #     Just(Relation(Const("friend"), Var(2), Const("Bob")))),
#     ]
#     for i in query(r, rules):
#         print(i)

# testQuery()
MARY = Const("Mary")
JOHN = Const("John")
ALICE = Const("Alice")
BOB = Const("Bob")
LIKES = Const("likes")
WINE = Const("wine")
FOOD = Const("food")

def testQuery2():
    ask1 = Relation(LIKES, MARY, WINE)
    ask2 = Relation(LIKES, JOHN, FOOD)
    rules = [
        Rule(Relation(LIKES, MARY, WINE), Top()),
        Rule(Relation(LIKES, JOHN, WINE), Top()),
        Rule(Relation(LIKES, ALICE, WINE), Top()),
        Rule(Relation(LIKES, MARY, FOOD), Top())]
    for _ in query(ask1, rules):
        print("yes")
        break
    else:
        print("no")
    for _ in query(ask2, rules):
        print("yes")
        break
    else:
        print("no")

testQuery2()

# family tree

JamesI = Const("JamesI")
CharlesI = Const("CharlesI")

CharlesII = Const("CharlesII")
JamesII = Const("JamesII")
Catherine = Const("Catherine")

Elizabeth = Const("Elizabeth")

Sophia = Const("Sophia")

GeorgeI = Const("GeorgeI")

Male = Const("male")
Female = Const("female")
Parent = Const("parent")

Mother = Const("mother")
Father = Const("father")

Uncle = Const("uncle")

def familyTree():
    rules = [
        Rule(Relation(Male, JamesI), Top()),
        Rule(Relation(Male, CharlesI), Top()),
        Rule(Relation(Male, CharlesII), Top()),
        Rule(Relation(Male, JamesII), Top()),
        Rule(Relation(Male, GeorgeI), Top()),

        Rule(Relation(Female, Elizabeth), Top()),
        Rule(Relation(Female, Sophia), Top()),
        Rule(Relation(Female, Catherine), Top()),

        Rule(Relation(Parent, CharlesI, JamesI), Top()),
        Rule(Relation(Parent, Elizabeth, JamesI), Top()),

        Rule(Relation(Parent, Catherine, CharlesI), Top()),
        Rule(Relation(Parent, CharlesII, CharlesI), Top()),
        Rule(Relation(Parent, JamesII, CharlesI), Top()),

        Rule(Relation(Parent, Sophia, Elizabeth), Top()),

        Rule(Relation(Parent, GeorgeI, Sophia), Top()),

        Rule(Relation(Mother, Var(1), Var(2)), 
            Conj([
                Just(Relation(Parent, Var(1), Var(2))),
                Just(Relation(Female, Var(2))),
            ])),

        Rule(Relation(Father, Var(3), Var(4)), 
            Conj([
                Just(Relation(Parent, Var(3), Var(4))),
                Just(Relation(Male, Var(4))),
            ]))
    ]
    for _ in query(Relation(Father, CharlesI, JamesI), rules):
        print("yes")
        break
    else:
        print("no")
    for i in query(Relation(Father, Var(5), CharlesI), rules):
        print(i)
    for i in query(Relation(Father, Var(6), Var(7)), rules):
        print(i)
    
familyTree()


