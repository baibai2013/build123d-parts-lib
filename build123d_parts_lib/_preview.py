"""Preview rendering utility (VTK 后端).

用 VTK offscreen 渲染器做真正的 Phong 平滑着色：
- `vtkPolyDataNormals` 自动计算 per-vertex 法向
- FeatureAngle=60°：尖锐边（棱/角）保留，曲面（圆柱/圆弧）平滑
- 无三角面接缝，无 seam 条纹

License: MIT
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from build123d import Shape


def save_preview_png(
    part: "Shape",
    png_path: str | Path,
    title: str | None = None,
    size: tuple[int, int] = (480, 480),
    face_color: tuple[float, float, float] = (0.56, 0.70, 0.85),  # #8fb4d8
    bg_color: tuple[float, float, float] = (1.0, 1.0, 1.0),
    feature_angle: float = 60.0,
    elev: float = 25.0,
    azim: float = -55.0,
) -> Path:
    """把 Part 渲染成 PNG 缩略图（VTK 后端，Phong 平滑着色）。

    Args:
        part: build123d Shape（Part / Compound / Solid）。
        png_path: 输出 PNG 路径。
        title: 图片标题（叠加在顶部）。
        size: 图像像素尺寸 (w, h)。
        face_color: RGB 0-1。
        feature_angle: 超过此角度的边保留锐利（默认 60°）。
        elev / azim: 相机俯仰角/方位角（度）。
    """
    import vtk

    verts, faces = part.tessellate(tolerance=0.02, angular_tolerance=0.08)
    if not faces:
        raise ValueError("Part has no tessellated faces")

    # 1. 构建 vtkPolyData
    points = vtk.vtkPoints()
    for v in verts:
        points.InsertNextPoint(v.X, v.Y, v.Z)
    cells = vtk.vtkCellArray()
    for i, j, k in faces:
        tri = vtk.vtkTriangle()
        tri.GetPointIds().SetId(0, int(i))
        tri.GetPointIds().SetId(1, int(j))
        tri.GetPointIds().SetId(2, int(k))
        cells.InsertNextCell(tri)
    poly = vtk.vtkPolyData()
    poly.SetPoints(points)
    poly.SetPolys(cells)

    # 2a. 焊合重复顶点（关键：boolean 操作后同一圆柱面可能被拆成多块 BRep face，
    #     tessellate 返回重复顶点；不清理就会在接缝处出现条纹）
    clean = vtk.vtkCleanPolyData()
    clean.SetInputData(poly)
    clean.SetAbsoluteTolerance(1e-2)
    clean.ToleranceIsAbsoluteOn()
    clean.ConvertLinesToPointsOff()
    clean.ConvertPolysToLinesOff()
    clean.ConvertStripsToPolysOff()
    clean.PointMergingOn()
    clean.Update()

    # 2b. 生成平滑法向（SplittingOn + FeatureAngle 保尖锐边、平滑曲面）
    normals = vtk.vtkPolyDataNormals()
    normals.SetInputConnection(clean.GetOutputPort())
    normals.SetFeatureAngle(feature_angle)
    normals.SplittingOn()
    normals.ComputeCellNormalsOff()
    normals.ComputePointNormalsOn()
    normals.ConsistencyOn()
    normals.AutoOrientNormalsOn()
    normals.Update()

    # 3. Mapper + Actor（Phong 材质）
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(normals.GetOutputPort())
    mapper.ScalarVisibilityOff()

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    prop = actor.GetProperty()
    prop.SetColor(*face_color)
    prop.SetAmbient(0.18)
    prop.SetDiffuse(0.85)
    prop.SetSpecular(0.20)
    prop.SetSpecularPower(18)
    prop.SetInterpolationToPhong()

    # 4. Renderer + Camera + Light
    renderer = vtk.vtkRenderer()
    renderer.AddActor(actor)
    renderer.SetBackground(*bg_color)
    renderer.SetUseDepthPeeling(0)

    # 关闭默认 light，手动加主光
    renderer.AutomaticLightCreationOff()
    key_light = vtk.vtkLight()
    key_light.SetLightTypeToSceneLight()
    key_light.SetPosition(-1.2, -1.5, 2.0)
    key_light.SetFocalPoint(0, 0, 0)
    key_light.SetIntensity(0.9)
    key_light.SetColor(1.0, 1.0, 1.0)
    renderer.AddLight(key_light)

    fill_light = vtk.vtkLight()
    fill_light.SetLightTypeToSceneLight()
    fill_light.SetPosition(2.0, -1.0, 0.5)
    fill_light.SetFocalPoint(0, 0, 0)
    fill_light.SetIntensity(0.35)
    fill_light.SetColor(1.0, 0.98, 0.95)
    renderer.AddLight(fill_light)

    # 自动框定 + 等轴视角
    renderer.ResetCamera()
    cam = renderer.GetActiveCamera()
    cam.Azimuth(azim)
    cam.Elevation(elev)
    cam.OrthogonalizeViewUp()
    cam.Zoom(1.15)
    renderer.ResetCameraClippingRange()

    # 标题（vtkTextActor 2D 叠层）
    if title:
        txt = vtk.vtkTextActor()
        txt.SetInput(title)
        tprop = txt.GetTextProperty()
        tprop.SetFontSize(14)
        tprop.SetColor(0.12, 0.12, 0.12)
        tprop.SetFontFamilyToArial()
        tprop.SetJustificationToCentered()
        tprop.SetVerticalJustificationToTop()
        txt.SetPosition(size[0] // 2, size[1] - 8)
        renderer.AddActor2D(txt)

    # 5. Offscreen 渲染窗口
    win = vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.AddRenderer(renderer)
    win.SetSize(*size)
    win.SetMultiSamples(8)   # MSAA 抗锯齿
    win.Render()

    # 6. 截屏到 PNG
    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(win)
    w2i.SetScale(1)
    w2i.ReadFrontBufferOff()
    w2i.Update()

    out = Path(png_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(str(out))
    writer.SetInputConnection(w2i.GetOutputPort())
    writer.Write()

    # 清理
    win.Finalize()
    return out
