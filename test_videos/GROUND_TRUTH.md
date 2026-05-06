# Test Videos — Ground Truth

合成的 3 段测试视频，每段都是程序化拼接，切换点精确已知。
作者自带的 `__assets__/demo_video1-9.mp4` 也可以做基线测试，但没有 GT 标注。

## 输出环境
- 全部 30fps、yuv420p、libx264
- 与 OmniShotCut README 建议的「480p+ / 30fps」对齐

---

## test_01_hardcut.mp4 (640×360, 300 frames, 10s)

**场景**：纯硬切，最简单的 baseline。两个完全不同的视频片段直接拼接。

| Shot | 帧范围 | 时长 | 来源 |
|---|---|---|---|
| 1 | 0–149 | 5.00s | `demo_video1.mp4` 0–5s |
| 2 | 150–299 | 5.00s | `demo_video2.mp4` 0–5s |

**Ground truth**:
- 1 个边界，硬切在 **frame 149→150**
- inter-shot relation: `hard_cut`
- 无 sudden jump，无渐变转场

**期望**：所有 SBD 方法（PySceneDetect / TransNetV2 / OmniShotCut）都应该正确检出。
这是用来确认 baseline 都能通过的基础题。

---

## test_02_dissolve.mp4 (640×360, 270 frames, 9s)

**场景**：两个完全不同的视频之间做 1 秒 dissolve（溶解）渐变转场。

| Frames | 内容 | 长度 |
|---|---|---|
| 0–119 | `demo_video1.mp4` 0–4s 单独 | 4.00s (120f) |
| 120–149 | dissolve 渐变（A 和 B 混合） | 1.00s (30f) |
| 150–269 | `demo_video2.mp4` 1–5s 单独 | 4.00s (120f) |

**Ground truth**:
- 1 个转场区间 `[120, 149]`（30 帧）
- inter-shot relation: `transition`
- intra-shot relation: `dissolve`
- 转场 IoU = 检测区间与 [120, 149] 的交并比

**期望**：
- PySceneDetect / TransNetV2 / AutoShot 通常能检出大致位置但**边界不精确**
  （论文 Table 1：转场 IoU 0.18–0.25, doc:227-232）
- OmniShotCut 应该把边界对得更准（论文给出 0.632 IoU, doc:228）

---

## test_03_sudden_jump.mp4 (540×720, 300 frames, 10s)

**场景**：**OmniShotCut 的杀手锏测试**。
同一段数字人长镜头（45s.mov）抽取两个不连续片段直接拼接，
模拟 vlog 跳剪 / 视频被剪掉中间几秒的真实场景。
前后两段是同一个人、同一个背景、同一个机位，**只有动作位置突然错位**。

| Shot | 帧范围 | 时长 | 来源 |
|---|---|---|---|
| 1 | 0–149 | 5.00s | `45s.mov` 0–5s |
| 2 | 150–299 | 5.00s | `45s.mov` 20–25s（**同源跳了 15 秒**） |

**Ground truth**:
- 1 个边界在 frame 149→150
- inter-shot relation: **`sudden_jump`**（关键！不是 hard_cut）
- 因为前后是同一场景，只是时间不连续

**期望**：
- PySceneDetect: 大概率漏检（颜色直方图相似，过不了阈值）
- TransNetV2: 准确率仅 0.261（论文 Table 1, doc:228）→ 大概率漏检
- AutoShot: 0.455 → 一半概率漏检
- **OmniShotCut: 0.761 → 应该能检出，并标记为 sudden_jump**

这是给 Insta360 / DJI 智能创作面试的关键 demo 场景：
*"vlog 跳剪 / 无人机视频中断 这种 同一场景内的不连续，传统 SBD 检测不出来，
OmniShotCut 是 2026 年首个把这一项做到 0.76 的开源模型。"*

---

## 用法

### 跑 OmniShotCut 推理
```bash
cd /home/yg/yg/code/github/OmniShotCut

# clean_shot 模式：直接出干净分镜
./run.sh infer --input_video_path test_videos/test_01_hardcut.mp4 --mode clean_shot
./run.sh infer --input_video_path test_videos/test_02_dissolve.mp4 --mode clean_shot
./run.sh infer --input_video_path test_videos/test_03_sudden_jump.mp4 --mode clean_shot

# default 模式：完整三件套（含转场类型 + sudden jump 标记）
./run.sh infer --input_video_path test_videos/test_03_sudden_jump.mp4 --mode default
```

### Gradio 上传测试
浏览器打开 http://127.0.0.1:7860，上传 test_videos/ 下的任一视频。

### 后续做对比 demo
拿这三段视频喂到 PySceneDetect、TransNetV2、OmniShotCut，
对比每个方法的：
- 边界位置精度（IoU）
- 转场类型识别准确率（dissolve / sudden_jump 标签）
- 漏检率（test_03 是关键）
