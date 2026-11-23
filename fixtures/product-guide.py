#!/usr/bin/env python3
"""Check Carrier's product guide through Base's neutral reading fixture.

Base renders its neutral reading workspace through Carrier and keeps it. This
fixture adds one neutral guide to that workspace's nested collection, renders it
again through the same Gazette build and checks the guide and its collection deck.
No preview server, publication or configured output is involved.
"""
import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

THEME = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gazette", required=True, help="Exact built Gazette executable")
    parser.add_argument("--resource-bindings", type=Path, required=True, help="JSON bindings for this world's external resource inputs")
    parser.add_argument("--base", type=Path, default=THEME.parent / "gazette-theme-base", help="Base checkout; defaults to the sibling directory")
    parser.add_argument("--keep", action="store_true", help="Retain the temporary workspace for browser inspection")
    args = parser.parse_args()
    fixtures = args.base.resolve(strict=True) / "fixtures"
    # Base's fixture is captured as a Theme source, so it must stay free of bytecode.
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(fixtures))
    from reading import Document, nodes, page, run

    base = subprocess.run(
        [sys.executable, str(fixtures / "reading.py"), "--gazette", args.gazette, "--theme", str(THEME),
         "--resource-bindings", str(args.resource_bindings), "--keep"],
        capture_output=True, text=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    retained = re.search(r"^fixture retained: (.+)\n", base.stdout, re.M)
    # This fixture reports the retained workspace itself, after adding its guide.
    print(base.stdout.replace(retained[0], "") if retained else base.stdout, end="")
    print(base.stderr, end="", file=sys.stderr)
    if base.returncode:
        if retained:
            shutil.rmtree(retained[1])
        return base.returncode
    work = Path(retained[1])
    try:
        guide = work / "content" / "canonical-product-guide"
        guide.mkdir()
        (guide / "index.md").write_text(page("article:canonical-product-guide", "An article guide", "/canonical-product-guide/",
                                             '{ kind = "page", family = { kind = "article" } }').replace(
            '+++\n[content]', '+++\ncollections = ["collection:nested"]\ntemplate = "carrier/product-guide.html"\n[content]', 1)
            + "\n## A guide question\n\nThe question retains its reading context.\n\n## A guide answer\n\nThe answer remains an authored account.\n")
        (guide / "notes.md").write_text("## A separate qualification\n\nThe guide keeps this separate qualification.\n")
        result = run(args.gazette, ["render-site", "--local", "--site", "site:reading", "--output-parent", str(work / "stages")],
                     (work / "workspace.toml").read_text())
        output = Path(result["directory"])
        output = output / "mount" if (output / "mount").is_dir() else output

        source = (output / "canonical-product-guide/index.html").read_text()
        assert 'data-page-mode="product"' in source and 'data-family="article"' in source
        assert 'publication-body--product' not in source
        assert 'href="#a-guide-question"' in source and 'href="#a-guide-answer"' in source
        assert 'class="reading-outline' in source
        assert '<details class="reading-notes" id="article-notes">' in source
        assert 'The guide keeps this separate qualification.' in source
        assert len(re.findall(r'<h1(?:\s|>)', source)) == 1
        print("PASS: Carrier article guide keeps Product mode, its native outline and Notes without the product-detail body role")

        nested = Document((output / "nested/index.html").read_text()).root
        main = next(node for node in nodes(nested) if node["tag"] == "main")
        deck = next(node for node in nodes(main) if "data-content-deck" in node["attrs"])
        cards = [node for node in nodes(deck) if "quote-deck__card" in node["attrs"].get("class", "").split()]
        members = [next(node for node in nodes(card) if node["tag"] == "a")["attrs"].get("data-gazette-destination-content") for card in cards]
        assert members == ["article:canonical-product-guide", "article:collection-reader", "article:collection-sibling", "journey:questions"], members
        assert deck["attrs"].get("data-autoplay") == "true", "a collection deck of more than three members autoplays"
        print("PASS: the guide joins its collection deck first, in native order, and the larger deck autoplays")
    finally:
        if args.keep:
            print("fixture retained:", work)
        else:
            shutil.rmtree(work)
    return 0


if __name__ == "__main__":
    sys.exit(main())
