import random
import string
import argparse
from enum import Enum


class Kind(Enum):
    GOOD = "good"
    UBD = "ubd"
    DUP = "dup"
    BLOCK = "block"


def random_var(pool):
    """Pick a random variable name from the pool."""
    return random.choice(pool)


def make_var_pool(n):
    """Generate a pool of variable names of any size."""
    names = []
    for i in range(n):
        name = ""
        x = i
        while True:
            name = string.ascii_lowercase[x % 26] + name
            x = x // 26 - 1
            if x < 0:
                break
        names.append(name)
    random.shuffle(names)
    return names


OPS = ["+", "-", "*", "/"]


def random_expr(var_pool, declared, force_good=False):
    """
    Build a random RHS expression.
    If force_good is True, only use declared variables or literals.
    Otherwise, may introduce use-before-declaration references.
    """
    parts = []
    num_terms = random.choices([1, 2, 3], weights=[2, 5, 3])[0]

    for i in range(num_terms):
        if i > 0:
            parts.append(random.choice(OPS))

        use_literal = random.random() < 0.3
        if use_literal:
            parts.append(str(random.randint(1, 100)))
        elif force_good:
            # Only use already-declared variables or literals
            if declared:
                parts.append(random.choice(list(declared)))
            else:
                parts.append(str(random.randint(1, 100)))
        else:
            # Deliberately pick an undeclared variable (use-before-decl)
            undeclared = [v for v in var_pool if v not in declared]
            if undeclared:
                parts.append(random.choice(undeclared))
            else:
                parts.append(str(random.randint(1, 100)))

    return " ".join(parts)


def generate_block(var_pool, declared, current_depth, target_depth, indent=0):
    """
    Generate a list of assignment statements (and nested blocks).
    Returns (lines, max_depth_reached).
    """
    lines = []
    pad = "  " * indent
    num_stmts = random.randint(3, 7)

    local_declared = set(declared)  # copy — scoping
    max_depth_reached = current_depth

    kinds = []
    for _ in range(num_stmts):
        if current_depth < target_depth:
            kinds.append(random.choices(
                [Kind.GOOD, Kind.UBD, Kind.DUP, Kind.BLOCK],
                weights=[50, 17, 17, 16]
            )[0])
        else:
            kinds.append(random.choices(
                [Kind.GOOD, Kind.UBD, Kind.DUP],
                weights=[50, 25, 25]
            )[0])

    for kind in kinds:
        if kind == Kind.BLOCK:
            lines.append(f"{pad}{{")
            inner, inner_depth = generate_block(var_pool, local_declared, current_depth + 1, target_depth, indent + 1)
            lines.extend(inner)
            lines.append(f"{pad}}}")
            max_depth_reached = max(max_depth_reached, inner_depth)
            continue

        if kind == Kind.GOOD:
            # Pick a fresh LHS, use only declared vars / literals on RHS
            undeclared_vars = [v for v in var_pool if v not in local_declared]
            lhs = random.choice(undeclared_vars) if undeclared_vars else random_var(var_pool)
            rhs = random_expr(var_pool, local_declared, force_good=True)
        elif kind == Kind.UBD:
            # Use-before-declaration: RHS references undeclared variables
            lhs = random_var(var_pool)
            rhs = random_expr(var_pool, local_declared, force_good=False)
        elif kind == Kind.DUP:
            # Duplicate assignment: re-assign an already-declared variable
            if local_declared:
                lhs = random.choice(list(local_declared))
                rhs = random_expr(var_pool, local_declared, force_good=True)
            else:
                # Nothing declared yet — fall back to use-before-decl error
                lhs = random_var(var_pool)
                rhs = random_expr(var_pool, local_declared, force_good=False)

        lines.append(f"{pad}{lhs} = {rhs};")
        local_declared.add(lhs)

    return lines, max_depth_reached


def generate_program(depth=2):
    num_vars = 5 + depth * 5
    while True:
        var_pool = make_var_pool(num_vars)
        declared = set()
        lines, achieved = generate_block(var_pool, declared, current_depth=0, target_depth=depth)
        if achieved == depth:
            break

    header = f"// Validating Farrow's use-before-declaration (depth={depth}, vars={num_vars})"
    return header + "\n" + "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate random Farrow use-before-declaration programs."
    )
    parser.add_argument(
        "--depth", type=int, default=2,
        help="Exact nesting depth for blocks (default: 2)"
    )
    args = parser.parse_args()

    print(generate_program(args.depth))


if __name__ == "__main__":
    main()
