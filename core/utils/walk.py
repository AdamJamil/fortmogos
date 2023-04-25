import importlib
import inspect
import os
from typing import Dict, List, Set
import re


def subclasses_of(cls: type) -> List[type]:
    subclasses: Dict[str, List[str]] = {}
    module_def: Dict[str, str] = {}  # keep track of where classes are defined so we can
    # import them later

    for root, _, files in os.walk("."):
        if root[:3] != ".\\." and "venv" not in root:
            for file in files:
                if file.endswith(".py"):
                    module_name = f"{root.replace(os.path.sep, '.')[2:]}.{file[:-3]}"
                    if module_name.startswith("."):
                        continue

                    with open(root + os.path.sep + file, "r", encoding="utf8") as f:
                        for name, bases in re.findall(
                            r"class\s+(\w+)\(([\w\s,]+)\)", f.read()
                        ):
                            for super_cls in re.split(r"\s*,\s*", bases):
                                if super_cls not in subclasses:
                                    subclasses[super_cls] = []
                                subclasses[super_cls].append(name)
                            module_def[name] = module_name

    to_import: Set[str] = set()
    q: List[str] = subclasses[cls.__name__]

    while q:
        curr = q.pop()
        to_import.add(module_def[curr])
        q.extend(subclasses[curr] if curr in subclasses else [])

    res: List[type] = []
    for module_name in to_import:
        module = importlib.import_module(module_name)
        for _, obj in inspect.getmembers(module):
            if (
                inspect.isclass(obj)
                and issubclass(obj, cls)
                and obj is not cls
                and obj not in res
            ):
                res.append(obj)

    return res
