"""Production sorting restriction; test/reference oracles are outside this scope."""
import ast
from pathlib import Path

import pytest

MODULES = (
    "rle.py", "lzw.py", "container.py", "huffman.py",
    "rq2/h0.py", "rq2/reorder.py", "rq2/huffman.py", "rq3/bpe.py",
)


@pytest.mark.parametrize("module", MODULES)
def test_algorithm_has_no_builtin_sort(module):
    root = Path(__file__).resolve().parents[2]
    tree = ast.parse((root / module).read_text(encoding="utf-8"))
    violations = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if (isinstance(func, ast.Name) and func.id == "sorted") or (
            isinstance(func, ast.Attribute) and func.attr in {"sort", "sorted"}
        ):
            violations.append(node.lineno)
    assert not violations, f"{module}: forbidden sort at lines {violations}"
