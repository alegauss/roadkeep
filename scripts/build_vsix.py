"""Write the archive an editor installs, from the files this tree already holds (RK1013).

A folder under the editor's extensions directory works and is how the host was developed,
but it is a copy somebody makes by hand: the two supported routes — a marketplace and `code
--install-extension` — both take one archive.

**Written here rather than by `vsce`**, which is the whole decision. A `.vsix` is an OPC
package: a zip carrying the extension under `extension/`, a manifest describing it, and a
content-types part. `zipfile` and `xml` are the standard library, so this repository can own
the format for the same reason it owns `argparse` over `click` — the alternative is node, a
lockfile and a step in every adopting CI, in a tree whose build rule is zero dependencies and
whose five other surfaces ship as files.

What it will **not** do is invent anything. Every field of the manifest is read from
`editor/package.json`, which the pre-commit hook already stamps with the module's version, so
an archive built from this tree is the version this tree is at and there is no second source
to disagree. A field that file does not carry is a field this script does not write.

    python scripts/build_vsix.py [--out DIR]

Prints the path it wrote. `tests/test_editor.py` reads the archive back.
"""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
EDITOR = ROOT / "editor"
MANIFEST = EDITOR / "package.json"

#: What goes into the archive, by name. A list and not a glob: `harness.js` is a test's
#: fixture and belongs in the repository rather than in what a reader installs, and a glob
#: would ship it the day nobody was looking (RK16's rule about what a derived write may take).
SHIPPED = ("package.json", "extension.js", "icon.svg", "README.md")

#: The two parts an OPC consumer opens before it looks at anything else. `.json` is declared
#: because the manifest is one, `.js` because the entry point is, and `.svg` for the icon —
#: an extension whose content types omit a part it carries is one the installer skips.
CONTENT_TYPES = """<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="json" ContentType="application/json"/>
  <Default Extension="js" ContentType="application/javascript"/>
  <Default Extension="svg" ContentType="image/svg+xml"/>
  <Default Extension="md" ContentType="text/markdown"/>
  <Default Extension="vsixmanifest" ContentType="text/xml"/>
</Types>
"""


def vsixmanifest(package: dict) -> str:
    """The manifest, every field of it read from `package.json`.

    The identity an editor installs by is `<publisher>.<name>`, which is also what the
    extensions directory is named after — so a manifest that spelled either differently from
    the file the host loads would install one extension and activate another.
    """
    return f"""<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011">
  <Metadata>
    <Identity Language="en-US" Id="{escape(package["name"])}" \
Version="{escape(package["version"])}" Publisher="{escape(package["publisher"])}"/>
    <DisplayName>{escape(package["displayName"])}</DisplayName>
    <Description xml:space="preserve">{escape(package["description"])}</Description>
    <Tags/>
    <Categories>{escape(",".join(package["categories"]))}</Categories>
    <GalleryFlags>Public</GalleryFlags>
  </Metadata>
  <Installation>
    <InstallationTarget Id="Microsoft.VisualStudio.Code"/>
  </Installation>
  <Dependencies/>
  <Assets>
    <Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true"/>
    <Asset Type="Microsoft.VisualStudio.Services.Content.Details" Path="extension/README.md" Addressable="true"/>
  </Assets>
</PackageManifest>
"""


def build(out: Path) -> Path:
    package = json.loads(MANIFEST.read_text(encoding="utf-8"))
    out.mkdir(parents=True, exist_ok=True)
    target = out / f"{package['publisher']}.{package['name']}-{package['version']}.vsix"
    # Deflated and written whole: an archive half a build wrote is the state RK118 refuses a
    # governed file over, and the same argument holds for a file somebody is about to install.
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", CONTENT_TYPES)
        archive.writestr("extension.vsixmanifest", vsixmanifest(package))
        for name in SHIPPED:
            archive.write(EDITOR / name, f"extension/{name}")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="Write the editor host as a .vsix.")
    parser.add_argument(
        "--out",
        default=str(ROOT / "dist"),
        help="Where to write the archive (default: dist/, which git ignores).",
    )
    args = parser.parse_args()
    print(build(Path(args.out)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
