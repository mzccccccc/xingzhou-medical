# OHIF v3 代码结构与功能总览

> 基于仓库 `/home/xingzhou/dev/ohif`（分支 release/3.13，版本 3.13.12）整理。
> OHIF（Open Health Imaging Foundation）Viewer 是一个可扩展的 Web 医学影像（DICOM）阅片平台。

## 1. 技术栈

- React 18 + TypeScript，Zustand（状态管理），TailwindCSS（样式）
- Cornerstone3D（@cornerstonejs/* 5.6.8，底层 vtk.js）：2D/3D 医学影像渲染
- ONNX Runtime：AI 推理（SAM 分割模型）
- pnpm workspaces monorepo（pnpm@12.8.1）+ Webpack 5（模块联邦，扩展动态加载）
- DICOMweb 协议取数；Jest 单测 + Playwright E2E

## 2. 顶层目录结构

```
ohif/
├── platform/          # 核心平台（应用壳 + 核心服务 + UI 库）
├── extensions/        # 功能扩展插件（影像渲染、DICOM 对象、测量跟踪等）
├── modes/             # 工作流模式（决定启用哪些扩展、布局和工具）
├── scripts/           # 辅助脚本（Playwright 截图审查 screenshot-reviewer 等）
├── tests/             # Playwright E2E 测试
├── testdata/          # 测试用 DICOM 数据（按需生成/下载）
├── node_modules/      # pnpm 安装的第三方依赖（.gitignore 忽略，不入库；
│                      #   monorepo 各子包的 node_modules 软链接到根目录的 .pnpm 存储）
├── rsbuild.config.ts / babel / jest / tsconfig 等构建配置
```

> 注：仓库根目录没有 `docs/`（文档站在 `platform/docs/`）；`pluginConfig.json` 位于 `platform/app/`。

### 2.1 platform/ —— 核心平台

| 目录 | 用途 |
|---|---|
| `platform/app/` | 主应用 `@ohif/viewer`：路由（`routes/Mode`）、`App.tsx`、`appInit.js`、ViewportGrid 组件、动态配置加载（`loadDynamicConfig.js`）、插件清单配置（`pluginConfig.json`）与生成的导入文件（`.webpack/writePluginImportsFile.js`） |
| `platform/core/` | 核心库：所有平台级服务（见 §3）、数据源实现（DicomWeb/本地/JSON）、DICOMWeb 客户端封装、测量注解基础设施、扩展/模块加载框架 |
| `platform/ui/` | 旧版 UI 组件库 |
| `platform/ui-next/` | 新版 UI 组件库（shadcn 风格）：组件、ViewportGridProvider 等 Context Provider、主题 |
| `platform/i18n/` | 国际化 |
| `platform/cli/` | 脚手架 CLI（创建扩展/模式模板） |
| `platform/docs/` | 文档站（Docusaurus） |

### 2.2 extensions/ —— 扩展（每个都是自包含插件）

| 扩展 | 用途 |
|---|---|
| `cornerstone/` | **核心渲染扩展**：Cornerstone3D 集成。含 Viewport 组件、工具注册（initCornerstoneTools.js）、ToolGroup/SyncGroup/CornerstoneCache/CornerstoneViewport 等服务、hanging protocols（hps/，含 mpr、fourUp 等）、同步器、面板（窗宽窗位/分段等）、命令模块、自定义项 |
| `cornerstone-dicom-seg/` | DICOM SEG 分割：加载/显示/编辑分割，分割面板 |
| `cornerstone-dicom-sr/` | DICOM SR 结构化报告：测量结果的 SR 保存/加载与映射 |
| `cornerstone-dicom-rt/` | DICOM RTSTRUCT/RTDOSE 放疗结构显示 |
| `cornerstone-dicom-pmap/` | DICOM 参数图（Parametric Map）支持 |
| `cornerstone-dynamic-volume/` | 4D 动态体积数据支持 |
| `measurement-tracking` | 测量跟踪：目标病灶跟踪面板、TrackedCornerstoneViewport、SR 导出跟踪流程 |
| `default/` | 标准功能：布局选择器/工具栏、数据源模块（DicomWeb/Local/JSON/Proxy/Merge）、SOP Class 处理器、布局模板、DicomTagBrowser、视口网格命令 |
| `dicom-pdf/` | DICOM 封装 PDF 显示 |
| `dicom-video/` | DICOM 视频显示 |
| `dicom-microscopy/` | 显微镜影像（DICOM Microscopy）支持 |
| `tmtv/` | 肿瘤治疗 PET/CT 融合（SUV 测量、融合 MPR） |
| `usAnnotation/` | 超声标注 |
| `test-extension/` | 测试示例扩展 |

### 2.3 modes/ —— 模式（工作流配置）

| 模式 | 用途 |
|---|---|
| `longitudinal/` | **旗舰模式**：纵向阅片（跟踪 + 分割 + SR + 全工具链），layoutTemplate 的标准示例 |
| `basic/` | 基础阅片模式（多数模式的底座，initToolGroups 定义各 tool group） |
| `segmentation/` | 分割专用模式 |
| `tmtv/` | PET/CT 肿瘤融合模式 |
| `microscopy/` | 显微镜模式 |
| `preclinical-4d/` | 临床前 4D 动态模式 |
| `usAnnotation/` | 超声标注模式 |
| `basic-dev-mode` / `basic-test-mode` | 开发/测试模式 |

## 3. 核心服务（platform/core/src/services，PUB-SUB 架构）

均实现 `pubSubServiceInterface`，经 `ServicesManager` 注册/访问：

- **DisplaySetService**：把 Study/Series 元数据组织为 DisplaySet（可显示的影像单元）
- **HangingProtocolService**：布局协议引擎（stage 切换、displaySet 匹配、图像加载策略）
- **ViewportGridService** + ui-next 的 ViewportGridProvider：视口网格布局状态
- **MeasurementService**：测量/注解的统一管理与 SOURCE 映射
- **ToolBarService**：工具栏按钮、工具状态、viewport action corners
- **PanelService**：左右侧面板管理
- **CustomizationService**：运行时组件/配置定制
- **UI 类服务**：UIModal / UIDialog / UIViewportDialog / UINotification
- **CineService**：电影播放；**StudyPrefetcherService**：检查预取；**DicomMetadataStore**：元数据存储
- **UserAuthenticationService**：token 注入（DICOMweb 请求）
- **WorkflowStepsService / MultiMonitorService**：工作流步骤、多显示器

cornerstone 扩展另有：**CornerstoneViewportService**（渲染引擎/视口生命周期/呈现状态）、**ToolGroupService**、**SyncGroupService**、**CornerstoneCacheService**（影像/volume 缓存）、**SegmentationService**（在扩展侧）。

## 4. 关键架构机制

- **Extension System**：每个扩展导出模块函数（`getViewportModule`、`getToolbarModule`、`getPanelModule`、`getCommandsModule`、`getHangingProtocolModule`、`getSopClassHandlerModule`、`getCustomizationModule` 等），由 ExtensionManager 聚合注册；构建时 `platform/app/.webpack/writePluginImportsFile.js` 按 `platform/app/pluginConfig.json` 自动生成导入。
- **Commands Manager**：命名命令按 context（activeContexts 顺序）查找执行，`commandsManager.runCommand(...)` 是 UI 与功能解耦的主要手段。
- **Mode**：模式声明依赖的扩展 + toolbarButtons + hanging protocol + layoutTemplate（`longitudinal/src/index.ts` 为标准示例）。
- **Hanging Protocols**（各扩展 `hps/` 目录）：JSON 式协议定义网格结构（rows/columns/layoutOptions）、每格的 viewportOptions（类型/方向/toolGroupId/syncGroups）、displaySet 选择规则与 stage。
- **同步组（SyncGroupService）**：HP 中声明 `{type, id}`，类型有 voi（窗宽窗位）、imageslice、cameraposition、zoompan、hydrateseg、frameview（自定义示例）等，底层复用 CS3D synchronizers。
- **数据源（Data Source）**：DicomWeb（QIDO/WUDO）、本地文件、DICOM JSON、Proxy、Merge 等，模式/配置决定用哪个。
- **开发规范**：优先 pub-sub 订阅而非 useEffect 轮询；新功能放扩展/模式，不改 core；新图标用 `addIcon` 注册；store 放扩展 `stores/`（zustand）。

## 5. 现有功能清单

**影像显示**
- 多模态 2D 阅片：CT、MRI、X 线、乳腺、超声等（stack 与 volume 视口）
- MPR 多平面重建：1×3 三视图（axial/sagittal/coronal）、Reformat 倾斜重排、2×2 三视图+3D（fourUp）；CrosshairsTool 实现定位线（彩色、可拖动平移/旋转/调 slab 厚度）、点击跳转、三平面交点联动；MPR slab 厚层
- 3D 体绘制视口（volume3d，CT-Bone 等预设）；动态 4D 数据支持
- DICOM 专用对象：SEG 分割（含编辑器）、SR 结构化报告、RTSTRUCT/RTDOSE、Parametric Map、PDF、视频、显微镜
- 图像叠加（Image Overlay）、呈色 LUT、多帧/超声

**测量与跟踪**
- Cornerstone Tools 全套：长度、双向、椭圆、矩形 ROI、多边形、角度、Cobb、箭头注释、自由文本、放大镜、窗宽窗位、缩放/平移、刻度尺等
- 目标病灶跟踪（measurement-tracking + longitudinal 模式）、SR 导出/导入（DICOM SR、CSV 报告）
- AI 辅助分割：SAM 模型（ONNX Runtime）、Circle/Rectangle scissor 等半自动工具

**联动与同步**
- 窗宽窗位同步、图像层面（解剖位置）同步、相机位置同步、缩放平移同步、frameView 固定间隔联动
- 布局变化后同步状态恢复（useSynchronizersStore）

**工作流与 UI**
- Hanging protocols 布局引擎 + 布局选择器（含 MPR、fourUp 等 Advanced 预设）、stage 翻页
- 可定制工具栏/右键菜单/热键（用户偏好持久化）、左右面板、多显示器、i18n 多语言
- 电影播放（Cine）、检查预取、视口对话框、通知/模态系统
- 呈现状态持久化（位置/LUT/分割 presentation stores）
- PET/CT 融合（TMTV）：融合 MPR、SUV 测量

**平台能力**
- 扩展/模式插件化架构、动态配置（app-config）、Customization Service 组件覆盖
- Dockerfile 部署、Netlify 配置、Playwright E2E + Jest 单测、CLI 脚手架

## 6. 常用命令

```bash
pnpm install                  # 安装依赖（monorepo 使用 pnpm）
pnpm dev                      # 启动查看器开发服务器（实际执行 @ohif/app 的 dev:viewer）
pnpm build                    # 生产构建（实际执行 @ohif/app 的 build:viewer）
pnpm --filter @ohif/app run dev:orthanc   # 连 Orthanc 数据源开发
```
