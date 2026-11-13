"""Add World Builder navigation and draft instructions to a staged dashboard."""
from pathlib import Path
import sys


def main():
    source, destination = map(Path, sys.argv[1:])
    text = source.read_text()
    if source.name == "community.php":
        anchor = '<section class="v6-next">'
        if text.count(anchor) != 1 or "Transfer a World Builder draft" in text:
            raise SystemExit("Expected the existing Community page without draft instructions")
        update = """<section class="content-section">
  <div class="section-heading">
    <h2>Transfer a World Builder draft</h2>
    <p>In the private World Builder, name your draft and choose <strong>Export draft JSON</strong>.
    In another browser, choose <strong>Import draft JSON</strong>, then <strong>Save Draft</strong> after validation.</p>
    <p>Use <strong>Validate &amp; Export ZIP</strong> to prepare native rooms for isolated gameplay testing.</p>
  </div>
</section>

""" + anchor
        with destination.open("x") as output:
            output.write(text.replace(anchor, update))
        return
    anchor = "echo '</nav>';"
    if text.count(anchor) != 1 or "require_admin()" not in text or "world-builder-studio.php" in text:
        raise SystemExit("Expected the existing authenticated dashboard without the Studio link")
    update = """echo '<a href="world-builder-studio.php">World Builder Studio</a>';
echo '</nav>';
echo '<section class="panel"><h2>Transfer a World Builder draft</h2><p>In the private World Builder, give the draft a name and choose <strong>Export draft JSON</strong>. In another browser, choose <strong>Import draft JSON</strong>, then <strong>Save Draft</strong> after validation.</p><p>Use <strong>Validate &amp; Export ZIP</strong> to prepare native rooms for an isolated test.</p></section>';"""
    with destination.open("x") as output:
        output.write(text.replace(anchor, update))


if __name__ == "__main__":
    main()
