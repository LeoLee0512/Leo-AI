"""One product identity for the manifest and Windows executable metadata."""
from pathlib import Path
import argparse
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from leo_shell import DISPLAY_NAME, PRODUCT_NAME, __version__


def product_identity():
    return {"name": PRODUCT_NAME, "display_name": DISPLAY_NAME, "version": __version__}


def executable_identity(path):
    import pefile
    with pefile.PE(str(path), fast_load=False) as pe:
        values = {}
        for entries in getattr(pe, "FileInfo", []):
            for entry in entries:
                for table in getattr(entry, "StringTable", []):
                    values.update({k.decode(): v.decode() for k, v in table.entries.items()})
        return {"name": values.get("ProductName"), "display_name": values.get("FileDescription"),
                "version": values.get("ProductVersion")}


def version_info():
    version = tuple(int(p) for p in __version__.split(".")) + (0,)
    fields = {"CompanyName": "Leo Li+ Studio", "FileDescription": DISPLAY_NAME,
              "FileVersion": __version__, "InternalName": "LeoAIStudio",
              "OriginalFilename": "LeoAIStudio.exe", "ProductName": PRODUCT_NAME,
              "ProductVersion": __version__}
    strings = ",\n".join(f"StringStruct({k!r}, {v!r})" for k, v in fields.items())
    return f"""VSVersionInfo(ffi=FixedFileInfo(filevers={version!r}, prodvers={version!r},
mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
kids=[StringFileInfo([StringTable('040904B0', [{strings}])]),
VarFileInfo([VarStruct('Translation', [1033, 1200])])])
"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.write_text(version_info(), encoding="utf-8", newline="\n")
