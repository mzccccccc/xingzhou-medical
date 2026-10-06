#!/usr/bin/env bash
# 一次性脚本：装依赖 → 生成合成 CT → 上传 Orthanc → 验证
set -e
export PATH="$HOME/.local/bin:$PATH"

cd ~/dev/backend

echo '=== 1. 安装 pydicom + numpy（走 aliyun 镜像）==='
uv add pydicom numpy 2>&1 | tail -3

echo '=== 2. 生成合成 CT 序列 ==='
uv run python gen_phantom.py

echo '=== 3. 上传 40 张到 Orthanc（每张贴图返回一个状态码，200=成功）==='
for f in phantom/*.dcm; do
  curl -s -o /dev/null -w '%{http_code} ' -X POST http://localhost:8042/instances --data-binary @"$f"
done
echo

echo '=== 4. 验证 DICOMweb 查询接口 ==='
curl -s 'http://localhost:8042/dicom-web/studies' | head -c 600
echo
