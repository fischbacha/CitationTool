from __future__ import annotations

import platform
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RenderResult:
    requested: str
    renderer: str | None
    output: Path | None
    skipped: bool = False
    reason: str | None = None


def _tool_path(name: str) -> str | None:
    found = shutil.which(name)
    if found:
        return found
    if name == "soffice":
        mac_path = Path("/Applications/LibreOffice.app/Contents/MacOS/soffice")
        if mac_path.exists():
            return str(mac_path)
    return None


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, capture_output=True, text=True)


def _command_error(exc: subprocess.CalledProcessError) -> str:
    details = (exc.stderr or exc.stdout or "").strip()
    if details:
        return details
    return f"command exited with status {exc.returncode}: {' '.join(exc.cmd)}"


def _quicklook(docx: Path, out_dir: Path) -> RenderResult:
    qlmanage = _tool_path("qlmanage")
    if not qlmanage:
        raise RuntimeError("Quick Look renderer is unavailable because `qlmanage` was not found.")

    out_dir.mkdir(parents=True, exist_ok=True)
    _run([qlmanage, "-t", "-s", "1600", "-o", str(out_dir), str(docx)])

    expected = out_dir / f"{docx.name}.png"
    if expected.exists():
        return RenderResult("quicklook", "quicklook", expected)

    candidates = sorted(out_dir.glob(f"{docx.name}*.png"))
    if candidates:
        return RenderResult("quicklook", "quicklook", candidates[-1])

    raise RuntimeError(f"Quick Look completed but no PNG render was found in {out_dir}.")


def _libreoffice(docx: Path, out_dir: Path) -> RenderResult:
    soffice = _tool_path("soffice") or _tool_path("libreoffice")
    if not soffice:
        raise RuntimeError("LibreOffice renderer is unavailable because `soffice`/`libreoffice` was not found.")

    out_dir.mkdir(parents=True, exist_ok=True)
    _run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(out_dir), str(docx)])

    pdf = out_dir / f"{docx.stem}.pdf"
    if not pdf.exists():
        candidates = sorted(out_dir.glob(f"{docx.stem}*.pdf"))
        if candidates:
            pdf = candidates[-1]
        else:
            raise RuntimeError(f"LibreOffice completed but no PDF render was found in {out_dir}.")

    pdftoppm = _tool_path("pdftoppm")
    if pdftoppm:
        png_stem = out_dir / docx.stem
        _run([pdftoppm, "-png", "-singlefile", "-r", "160", str(pdf), str(png_stem)])
        png = png_stem.with_suffix(".png")
        if png.exists():
            return RenderResult("libreoffice", "libreoffice", png)

    return RenderResult("libreoffice", "libreoffice", pdf)


def render_docx(docx: Path, out_dir: Path, mode: str) -> RenderResult:
    if mode == "none":
        return RenderResult("none", None, None, skipped=True, reason="Rendering was not requested.")

    renderers = {
        "quicklook": _quicklook,
        "libreoffice": _libreoffice,
    }
    if mode in renderers:
        try:
            return renderers[mode](docx, out_dir)
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"{mode} render failed: {_command_error(exc)}") from exc

    if mode != "auto":
        raise RuntimeError(f"Unknown render mode: {mode}")

    order = ["quicklook", "libreoffice"] if platform.system() == "Darwin" else ["libreoffice", "quicklook"]
    failures: list[str] = []
    for renderer in order:
        try:
            return renderers[renderer](docx, out_dir)
        except subprocess.CalledProcessError as exc:
            failures.append(f"{renderer}: {_command_error(exc)}")
        except RuntimeError as exc:
            failures.append(f"{renderer}: {exc}")

    return RenderResult(
        "auto",
        None,
        None,
        skipped=True,
        reason="No visual renderer succeeded. " + " | ".join(failures),
    )
