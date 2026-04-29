"""Preview rendering via OCP CAD Viewer (VS Code / Cursor 扩展).

走 VS Code / Cursor 的 OCP CAD Viewer 端口（3939 / 4567）调用 `save_screenshot`,
得到 WebGL 渲染出的高质量 PNG(带边线、阴影、材质)。

仅在 Viewer 已运行时可用；否则抛 RuntimeError，调用方应回退到 `_preview.save_preview_png` (VTK 版).

License: MIT
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from build123d import Shape


def _find_active_port() -> int | None:
    """自动探测活跃的 OCP Viewer 端口（3939 / 4567）。"""
    try:
        from ocp_vscode.comms import port_check
        from ocp_vscode.state import get_ports

        for p in get_ports():
            p = int(p)
            if port_check(p):
                return p
    except Exception:
        pass
    # Fallback: 手动 socket 探测
    import socket

    for p in (3939, 4567):
        try:
            s = socket.create_connection(("localhost", p), timeout=0.5)
            s.close()
            return p
        except OSError:
            pass
    return None


def save_preview_png_ocp(
    part: "Shape",
    png_path: str | Path,
    title: str | None = None,
    wait_s: float = 2.0,
) -> Path:
    """Render a PNG via OCP CAD Viewer's WebGL backend.

    Args:
        part:     build123d Shape / Part / Compound.
        png_path: 输出 PNG 路径。
        title:    （当前未用；保留参数与 VTK 版签名对齐）
        wait_s:   show() 后等待渲染稳定的时间(秒)。

    Raises:
        RuntimeError: OCP Viewer 未运行或连接失败。
    """
    port = _find_active_port()
    if port is None:
        raise RuntimeError(
            "OCP Viewer not running; start the CAD Viewer extension (port 3939 / 4567)"
        )

    from ocp_vscode import Camera, save_screenshot, set_port, show

    out = Path(png_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    set_port(port)
    show(part, reset_camera=Camera.RESET)
    time.sleep(wait_s)  # WebGL render settle
    save_screenshot(str(out))
    return out


def save_preview_png_auto(
    part: "Shape",
    png_path: str | Path,
    title: str | None = None,
) -> tuple[Path, str]:
    """Prefer OCP Viewer screenshot; fall back to VTK offscreen.

    Returns:
        (path, backend) — backend ∈ {"ocp", "vtk"}
    """
    try:
        p = save_preview_png_ocp(part, png_path, title=title)
        return p, "ocp"
    except Exception as e_ocp:
        # 兜底：VTK 离屏渲染 / VTK offscreen fallback
        from build123d_parts_lib._preview import save_preview_png

        p = save_preview_png(part, png_path, title=title)
        return p, f"vtk (ocp 失败: {type(e_ocp).__name__})"
