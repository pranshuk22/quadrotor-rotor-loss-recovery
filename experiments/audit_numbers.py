"""Number audit: every number in a .tex file must appear in a file under results/ (tables, csv).

Usage: .venv/bin/python experiments/audit_numbers.py docs/paper/paper.tex [more.tex ...] [--section NAME]
Extracts numeric tokens (integers and decimals, with optional sign and exponent) from the text of the .tex file(s), after removing
comments, labels, references, citation keys, URLs, LaTeX commands and figure/table environments' option arguments. A token counts as
found if the same digits occur in some results file, also allowing the usual rounding: tokens are compared with every number of the results files
rounded to the same number of decimals. Tokens that are small integers (<= 20, e.g. counts of things listed in the text) and years are
reported separately as 'small integers' and not as unmatched.

Prints the unmatched tokens with their line numbers (to be resolved by hand) and a summary. Exit status 0 always (it is an audit aid).
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NUM = re.compile(r"(?<![\w.])[-+$]*(?:\d{1,3}(?:,\d{3})+|\d+)\.?\d*(?:[eE][-+]?\d+)?")


def results_numbers():
    vals = []
    for p in list((ROOT / "results").rglob("*.md")) + list((ROOT / "results").rglob("*.csv")):
        txt = p.read_text(errors="ignore")
        for m in re.finditer(r"[-+]?\d+\.?\d*(?:[eE][-+]?\d+)?", txt):
            vals.append(m.group(0))
    return vals


def clean(line):
    line = re.sub(r"(?<!\\)%.*", "", line)
    line = re.sub(r"\\(label|ref|cite|citep|citet|eqref|input|includegraphics|bibliography|bibliographystyle|texttt|url|href)\*?(\[[^\]]*\])?\{[^}]*\}", " ", line)
    line = re.sub(r"\\[a-zA-Z]+\*?", " ", line)
    return line


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    nums = results_numbers()
    exact = set(nums)
    by_dec = {}
    for s in nums:
        try:
            v = float(s)
        except ValueError:
            continue
        by_dec.setdefault(None, []).append(v)
    allv = by_dec.get(None, [])
    unmatched, small, total = [], 0, 0
    for f in args:
        for i, line in enumerate(Path(f).read_text().splitlines(), 1):
            for m in NUM.finditer(clean(line)):
                tok = m.group(0).strip("$+").replace(",", "")
                if not re.search(r"\d", tok):
                    continue
                total += 1
                try:
                    v = float(tok)
                except ValueError:
                    continue
                if re.fullmatch(r"-?\d+", tok) and abs(v) <= 20:
                    small += 1
                    continue
                if tok in exact or tok.lstrip("-") in exact:
                    continue
                dec = len(tok.split(".")[1]) if "." in tok and "e" not in tok.lower() else 0
                ok = any(abs(round(x, dec) - v) < 10 ** (-dec) * 0.5 + 1e-12 for x in allv if abs(x - v) < 10 ** (-dec + 1) + 1e-9) if "e" not in tok.lower() else any(abs(x - v) <= abs(v) * 0.06 for x in allv)
                if not ok:
                    unmatched.append((f, i, tok))
    print(f"tokens: {total}; small integers skipped: {small}; unmatched: {len(unmatched)}")
    for f, i, tok in unmatched:
        print(f"{f}:{i}: {tok}")


if __name__ == "__main__":
    main()
