"""生成一套合成 CT 测试序列（40 层，含随层号移动的高密度小球），用于灌入 Orthanc。

原理：以 pydicom 自带的真实头部 CT（CT_small.dcm）为头部字段模板，
像素数据替换为合成模体，保证 DICOM 各字段合法、OHIF/Cornerstone 能正常渲染。

用法：cd ~/dev/backend && uv run python gen_phantom.py
输出：phantom/slice_001.dcm ~ slice_040.dcm
"""
from copy import deepcopy
from pathlib import Path

import numpy as np
from pydicom import dcmread
from pydicom.data import get_testdata_file
from pydicom.uid import ExplicitVRLittleEndian, generate_uid

N_SLICES = 40        # 层数
SLICE_MM = 3.0       # 层厚(mm)
INTERCEPT = -1024    # CT 标准 HU 偏移
OUT_DIR = Path(__file__).resolve().parent / "phantom"


def make_slice(i: int, rows: int, cols: int) -> np.ndarray:
    """生成第 i 层的 HU 值：空气背景 + 圆形软组织 + 沿圆周移动的"病灶"球。"""
    yy, xx = np.mgrid[0:rows, 0:cols].astype(float)
    cy, cx = rows / 2, cols / 2

    hu = np.full((rows, cols), -1000, dtype=np.float32)           # 空气
    tissue = ((yy - cy) ** 2 + (xx - cx) ** 2) < (0.42 * rows) ** 2
    hu[tissue] = 40                                               # 软组织

    t = i / N_SLICES                                              # 球心随层号转一圈
    by = cy + (0.25 * rows) * np.sin(2 * np.pi * t)
    bx = cx + (0.25 * cols) * np.cos(2 * np.pi * t)
    ball = ((yy - by) ** 2 + (xx - bx) ** 2) < (0.08 * rows) ** 2
    hu[ball] = 900                                                # 高密度（类骨）
    return hu


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    tpl = dcmread(get_testdata_file("CT_small.dcm"))  # pydicom 离线自带，无需下载
    rows, cols = int(tpl.Rows), int(tpl.Columns)
    study_uid = generate_uid()      # 一次检查
    series_uid = generate_uid()     # 一个序列

    for i in range(N_SLICES):
        ds = deepcopy(tpl)
        hu = make_slice(i, rows, cols)
        pixels = np.clip(hu - INTERCEPT, 0, 65535).astype(np.uint16)

        # --- 患者/检查/序列标识 ---
        ds.PatientName = "Phantom^Test"
        ds.PatientID = "PHANTOM-001"
        ds.StudyDate = "20261004"
        ds.Modality = "CT"
        ds.StudyInstanceUID = study_uid
        ds.SeriesInstanceUID = series_uid
        ds.SOPInstanceUID = generate_uid()   # 每张图唯一
        ds.InstanceNumber = i + 1
        ds.SeriesNumber = 1

        # --- 像素与几何信息（三维重建/MPR 全靠这些字段）---
        ds.Rows, ds.Columns = rows, cols
        ds.BitsAllocated = 16
        ds.BitsStored = 16
        ds.HighBit = 15
        ds.PixelRepresentation = 0           # 无符号
        ds.RescaleIntercept = INTERCEPT
        ds.RescaleSlope = 1
        ds.WindowCenter = 40
        ds.WindowWidth = 400
        ds.SliceThickness = SLICE_MM
        ds.PixelSpacing = list(tpl.PixelSpacing) if "PixelSpacing" in tpl else [1.0, 1.0]
        ds.ImagePositionPatient = [0.0, 0.0, round(i * SLICE_MM, 3)]
        ds.ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
        ds.PixelData = pixels.tobytes()

        # --- 文件元信息 ---
        ds.file_meta.MediaStorageSOPInstanceUID = ds.SOPInstanceUID
        ds.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

        path = OUT_DIR / f"slice_{i + 1:03d}.dcm"
        ds.save_as(path, enforce_file_format=True)

    print(f"OK: 已生成 {N_SLICES} 层 -> {OUT_DIR}")


if __name__ == "__main__":
    main()
