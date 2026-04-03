# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

import re
from doctest import NORMALIZE_WHITESPACE, DocTestFinder, DocTestRunner
from pathlib import Path


def run_doctests(code):
    finder = DocTestFinder(recurse=False)
    runner = DocTestRunner(optionflags=NORMALIZE_WHITESPACE)
    for test in finder.find(code, "coordo-py", globs=globals()):
        result = runner.run(test)
        if result.failed:
            exit(1)


readme_content = (Path(__file__).parent / "README.md").read_text()

code_blocks = re.findall(r"```py\n(.*?)\n```", readme_content, re.DOTALL)

combined_code = "\n\n".join(code_blocks)

exec_lines = []
doctest_lines = []
for line in combined_code.splitlines():
    if line.startswith(">>>"):
        exec("\n".join(exec_lines), globals())
        exec_lines = []
        doctest_lines.append(line)
    elif doctest_lines:
        if line == "":
            run_doctests(
                "\n".join(doctest_lines),
            )
            doctest_lines = []
        else:
            doctest_lines.append(line)
    else:
        exec_lines.append(line)
