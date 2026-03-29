import doctest
import re
from pathlib import Path

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
            doctest.run_docstring_examples(
                "\n".join(doctest_lines),
                globals(),
                optionflags=doctest.NORMALIZE_WHITESPACE,
            )
            doctest_lines = []
        else:
            doctest_lines.append(line)
    else:
        exec_lines.append(line)
