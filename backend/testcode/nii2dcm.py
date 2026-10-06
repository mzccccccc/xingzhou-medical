"""NIfTI (.nii/.nii.gz) → DICOM 序列转换工具

原理：
  1. SimpleITK 读取 NIfTI 体数据（SimpleITK 与 DICOM 同为 LPS 坐标系，
     方向余弦/原点/间距可直接搬进 DICOM 字段，无需坐标翻转）
  2. 逐层（轴位）写出标准 CT DICOM 文件，含完整几何信息
     （ImagePositionPatient / ImageOrientationPatient / PixelSpacing），
     OHIF 能据此正确做三维重建和 MPR
  3. 像素值按 HU（CT 值）原样保存为 int16 有符号（RescaleIntercept=0）

用法：
  uv run python nii2dcm.py <输入.nii.gz> <输出目录> [患者ID]
示例：
  uv run python nii2dcm.py "/mnt/f/桌面/BTCV/imagesTr/img0001.nii.gz" btcv_dicom BTCV-0001
"""
import sys
from copy import deepcopy
from pathlib import Path

import numpy as np
import SimpleITK as sitk
from pydicom import dcmread
from pydicom.data import get_testdata_file  # 用 pydicom 自带 CT 作头部字段模板
from pydicom.uid import ExplicitVRLittleEndian, generate_uid


def convert(nifti_path: str, out_dir: str, patient_id: str = "ANON-001") -> int:
    img = sitk.ReadImage(nifti_path)
    img = sitk.Cast(img, sitk.sitkInt16)          # CT 的 HU 值域 int16 足够
    arr = sitk.GetArrayFromImage(img)             # numpy: [z, y, x]
    nz, rows, cols = arr.shape

    sx, sy, sz = img.GetSpacing()                 # 体素间距 mm (x, y, z)
    origin = np.array(img.GetOrigin())            # 第一层左上角的物理坐标
    d = img.GetDirection()                        # 3x3 方向余弦（行优先）

    # DICOM 几何字段：前两组 = 行/列方向；第三组 × 层厚 = 每层位置增量
    iop = [d[0], d[1], d[2], d[3], d[4], d[5]]
    slice_vec = np.array([d[6], d[7], d[8]]) * sz

    tpl = dcmread(get_testdata_file("CT_small.dcm"))
    study_uid = generate_uid()
    series_uid = generate_uid()

    out = Path(out_dir).expanduser()
    out.mkdir(parents=True, exist_ok=True)

    for k in range(nz):
        ds = deepcopy(tpl)
        ipp = origin + slice_vec * k              # 本层在人体坐标系中的位置

        # --- 标识 ---
        ds.PatientName = patient_id.replace("-", "^")
        ds.PatientID = patient_id
        ds.StudyDate = "20261005"
        ds.Modality = "CT"
        ds.StudyInstanceUID = study_uid
        ds.SeriesInstanceUID = series_uid
        ds.SOPInstanceUID = generate_uid()
        ds.InstanceNumber = k + 1
        ds.SeriesNumber = 1
        ds.SeriesDescription = "NIfTI converted"

        # --- 几何（三维重建/MPR 全靠这些）---
        ds.ImagePositionPatient = [round(float(v), 4) for v in ipp]
        ds.ImageOrientationPatient = [round(float(v), 6) for v in iop]
        ds.PixelSpacing = [round(sy, 4), round(sx, 4)]   # DICOM 顺序: 行(y), 列(x)
        ds.SliceThickness = round(sz, 4)

        # --- 像素 ---
        ds.Rows, ds.Columns = rows, cols
        ds.BitsAllocated = 16
        ds.BitsStored = 16
        ds.HighBit = 15
        ds.PixelRepresentation = 1                 # 有符号（HU 有负值）
        ds.RescaleIntercept = 0                    # 数组里已是 HU，原样存
        ds.RescaleSlope = 1
        ds.WindowCenter = 40                       # 腹部窗（软组织）
        ds.WindowWidth = 400
        ds.PixelData = np.ascontiguousarray(arr[k], dtype=np.int16).tobytes()

        # --- 文件元信息 ---
        ds.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.2"  # CT Image Storage
        ds.file_meta.MediaStorageSOPInstanceUID = ds.SOPInstanceUID
        ds.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

        ds.save_as(out / f"slice_{k + 1:04d}.dcm", enforce_file_format=True)

    print(f"OK: {nifti_path}")
    print(f"    {nz} 层, {rows}x{cols}, 体素间距 {sx:.3f}x{sy:.3f}x{sz:.3f} mm")
    print(f"    输出目录: {out.resolve()}")
    return nz


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    convert(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "ANON-001")
