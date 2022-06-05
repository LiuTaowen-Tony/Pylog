from dataclasses import dataclass
from typing import Mapping, List
from uuid import uuid1
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

class Top(Predicate): pass
@dataclass
class Not(Predicate): body : Predicate
@dataclass
class Conj(Predicate): clauses : List[Predicate]
@dataclass
class Disj(Predicate): clauses : List[Predicate]
@dataclass
class Just(Predicate): body : Relation

@dataclass
class Rule:
    term : Term
    body : Predicate

Env = Mapping[Term, Term]
TopLevel = List[Rule]

def changeName(r : Rule):
    def helper(scheme : Mapping[Var, Var], pred : Predicate) -> Predicate :
        match pred:
            case Top():         return pred
            case Not(body):     return Not(helper(scheme, body))
            case Conj(clauses): return Conj([helper(scheme, i) for i in clauses])
            case Disj(clauses): return Disj([helper(scheme, i) for i in clauses])
            case Just(body):    return Just(Relation(*[
                scheme[i] if i in scheme else i for i in body]))
    match r.term:
        case Relation():
            vars    = filter(lambda x: isinstance(x, Var), r.term)
            mapping = dict(zip(vars, (Var(uuid1()) for _ in vars)))
            term    = Relation(*[mapping[i] if i in mapping else i for i in r.term])
            return Rule(term, helper(mapping, r.body))
        case Var(x): # kinda wired... 
            y    = Var(uuid1())
            return Rule(y, helper({Var(x) : y}, r.body))
        case _ : return r

# reduce a variable into a constant if it can be reduced in the env
def walk(var : Term, env : Env):
    if isinstance(var, Var) and var in env: return walk(env[var], env)
    else:                                   return var

# unify two terms
def unify(u : Term, v : Term, env : Env = dict()) -> Mapping:
    if env is None: return env
    u = walk(u, env)
    v = walk(v, env)
    if u == v: return env
    match (u, v):
        case (Var(_), _): return {u : v, **env}
        case (_, Var(_)): return {v : u, **env}
        case (Relation(), Relation()):
            if len(u) != len(v): return None
            for x, y in zip(u, v):
                env = unify(x, y, env)
            return env
        case _: return None

def query(u : Term, topLevel : TopLevel, env : Env = dict()):
    for r in topLevel:
        rule = changeName(r)
        e = unify(u, rule.term, env)
        if e is not None:
            yield from match(rule.body, e, topLevel)

def match(pred : Predicate, env : Env, topLevel : TopLevel):
    match pred:
        case Top():          yield env
        case Just(body):     yield from query(body, topLevel, env)
        case Conj([clause]): yield from match(clause, env, topLevel)
        case Conj([clause, *clauses]):
            for e in match(clause, env, topLevel):
                yield from match(Conj(clauses), e, topLevel)
        case Disj(clauses):
            for clause in clauses:
                if (e := match(clause, env, topLevel)) is not None:
                    yield e
        case Not(body):
            if match(body, env, topLevel) is not None: return None
            else:                                      yield env

def driverLoop(u : Term, rules : TopLevel):
    print("----------------------------------------------------")
    match u:
        case Var(x):     var = [Var(x)]
        case Relation(): var = list(filter(lambda x: isinstance(x, Var), u))
        case _         : var = []
    if not var: # is empty
        if next(query(u, rules)) is not None: print("yes")
        else:                                 print("no")
    else:
        for env in query(u, rules):
            print("env = ", env)
            for v in var: print(v, "=", walk(v, env))
            match input("input . to terminate, otherwise continue"):
                case ".": break
    print("\nterminated!\n")


def testWalk():
    assert (Const(10) == walk(Var(1), {Var(1) : Const(10)}))
    assert (Const(10) == walk(Var(1), {Var(1) : Var(2), Var(2) : Const(10)}))

def testUnify():
    assert({Var(1) : Var(2), Var(2) : Const(10)} ==
        dict(unify(Relation(Var(1), Const(2)), Relation(Var(2), Var(2)))))
    assert({Var(2) : Relation(Const(2), Const(2)), Var(1) : Var(2)} ==
        dict(unify(Relation(Var(1), Relation(Const(2), Const(2))), Relation(Var(2), Var(2)))))


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

        Rule(Relation(Father, Var(1), Var(2)), 
            Conj([
                Just(Relation(Parent, Var(1), Var(2))),
                Just(Relation(Male, Var(2))),
            ]))
    ]
    driverLoop(Relation(Father, CharlesI, JamesI), rules)
    driverLoop(Relation(Father, Var(1), CharlesI), rules)
    driverLoop(Relation(Father, Var(1), Var(2)), rules)
    
# familyTree()

Nat = Const("Nat")
Z = Const("Z")
S = Const("S")

Add = Const("add")

def pianoNumbers():
    rules = [
        Rule(Relation(Nat, Z), Top()),
        Rule(Relation(Nat, Relation(S, Var(1))), Top()),
        Rule(Relation(Add, Z, Var(1), Var(1)), Top()),
        Rule(Relation(Add, Relation(S, Var(1)), Var(2), Var(3)), 
            Conj([
                Just(Relation(Nat, Var(3))),
                Just(Relation(Add, Var(1), Relation(S, Var(2)), Var(3)))])),
    ]
    driverLoop(Relation(Add, Z, Relation(S, Z), Relation(S, Z)), rules)
    driverLoop(Relation(Add, Relation(S, Z), Relation(S, Z), Relation(S, Relation(S ,Z))), rules)
    # driverLoop(Relation(Add, Var(1), Var(2), Relation(S, Relation(S ,Z))), rules)
    driverLoop(Relation(Add, Var(1), Var(2), Var(3)), rules)


pianoNumbers()
