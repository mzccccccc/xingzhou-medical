#!/usr/bin/env bash
# 上传本地 DICOM 数据到 Orthanc
# 用法:
#   bash upload_dicom.sh <单个.dcm文件>
#   bash upload_dicom.sh <目录>          # 递归上传目录下所有 DICOM
# 说明:
#   医院导出的 DICOM 常见三种形态: *.dcm / *.ima / 无扩展名，本脚本都处理；
#   非 DICOM 文件会被 Orthanc 拒绝(非200)，计入失败数，不会污染数据库。
set -e

SRC="${1:?用法: bash upload_dicom.sh <目录或单个.dcm文件>}"
ORTHANC="http://localhost:8042"
OK=0
FAIL=0

upload_one() {
  local f="$1"
  local code
  code=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$ORTHANC/instances" --data-binary @"$f")
  if [ "$code" = "200" ]; then
    OK=$((OK + 1))
    printf '\r已上传: %s 张' "$OK"
  else
    FAIL=$((FAIL + 1))
    echo "失败($code): $f"
  fi
}

if [ -f "$SRC" ]; then
  upload_one "$SRC"
elif [ -d "$SRC" ]; then
  # -iname '*.dcm' -o -iname '*.ima' -o 无扩展名文件(! -name '*.*')
  while IFS= read -r -d '' f; do
    upload_one "$f"
  done < <(find "$SRC" -type f \( -iname '*.dcm' -o -iname '*.ima' -o ! -name '*.*' \) -print0)
else
  echo "路径不存在: $SRC"
  exit 1
fi

echo
echo "==== 上传完成: 成功 $OK 张, 失败 $FAIL 张 ===="
echo '---- Orthanc 当前检查(Study)数量 ----'
curl -s "$ORTHANC/dicom-web/studies?limit=1000" | grep -c '0020000D' || true
echo '刷新 OHIF (http://localhost:3000) 即可看到新数据'
