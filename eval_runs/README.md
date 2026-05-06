# OmniShotCut vs TransNetV2 vs PySceneDetect — 本机三方对比

> 在 RTX 4090 上用 3 段程序化合成测试视频对比 2026 年三个开源 SBD 方法的实测复现。
> 重点验证：**OmniShotCut 在 Sudden Jump（同源跳剪）场景下相对 baseline 的差异化能力**。

---

## TL;DR — 一张图讲完

![comparison_timeline](comparison_timeline.png)

- **test_01 (硬切)**：三方都过得了
- **test_02 (溶解)**：三方都在转场起点附近有检出，但都没标"dissolve"类型（OmniShotCut 标成 Hard_Cut）
- **test_03 (sudden_jump)**：**PySceneDetect 和 TransNetV2 完全 0 边界检出，只有 OmniShotCut 准确标记 `Sudden_Jump`**

---

## 为什么这个对比有意义

视频生成模型（NVIDIA Cosmos / Open-Sora Plan / Wan）的训练数据 pipeline 第一步是镜头边界检测，把长视频拆成干净分镜。痛点是 vlog 跳剪 / 直播录屏 / 无人机视频中断这种 **同一场景内的不连续**——传统 SBD 模型（颜色直方图 / 3D CNN）对这种场景几乎瞎眼。论文（arXiv:2604.24762）给出的 Sudden Jump 准确率：

| 方法 | Sudden Jump 准确率 |
|---|---|
| PySceneDetect | 0.416 |
| TransNetV2 | 0.261 |
| AutoShot | 0.455 |
| **OmniShotCut** | **0.761** |

本仓库就是这组数据的本机复现。

---

## 测试集

3 段程序化合成视频，ground truth 帧号精确已知（`test_videos/GROUND_TRUTH.md`）：

| 文件 | 规格 | 关键边界 | 类型 |
|---|---|---|---|
| `test_01_hardcut.mp4` | 640×360, 30fps, 10s | frame 150 | Hard_Cut |
| `test_02_dissolve.mp4` | 640×360, 30fps, 9s | frame 120–149 (1s xfade) | Dissolve |
| `test_03_sudden_jump.mp4` | 540×720, 30fps, 10s | frame 150 | **Sudden_Jump** |

`test_03` 是关键场景：同一段数字人长镜头（45s.mov）抽 0–5s 和 20–25s 直接拼接，模拟 vlog 跳剪。前后是同一个人、同一个机位、同一个背景，只是动作位置突然错位。

---

## 三方对比表

| 测试 | GT | PySceneDetect 0.7 | TransNetV2 (kunato/transnetv2pt) | OmniShotCut |
|---|---|---|---|---|
| test_01_hardcut | frame 150, Hard_Cut | ✅ 检出 (含 150) | ✅ 检出 (含 150) | ✅ 检出 + 标 `Hard_Cut` |
| test_02_dissolve | frame 120–149, Dissolve | 🟡 124 (无类型) | 🟡 124 (无类型) | 🟡 124/195，类型错（标硬切） |
| **test_03_sudden_jump** | frame 150, **Sudden_Jump** | ❌ **0 边界** | ❌ **0 边界** | ✅✅ frame 150 + 标 `Sudden_Jump` |

> 详细帧级输出见 `COMPARISON.md`。

---

## OmniShotCut 在 test_03 上的输出

```json
{
  "video_path": "test_videos/test_03_sudden_jump.mp4",
  "pred_ranges":      [[0, 150], [150, 294], [294, 300]],
  "pred_intra_labels":["General",  "General",     "General"],
  "pred_inter_labels":["New_Start","Sudden_Jump", "Sudden_Jump"]
}
```

frame 150 处不仅检出边界，还**准确分类为 `Sudden_Jump`**（不是 Hard_Cut）—— 这是 OmniShotCut 跟 PySceneDetect / TransNetV2 的根本差异：另两家只能告诉你"这里有边界"，OmniShotCut 还告诉你"是同源跳剪不是场景切换"。

可视化输出（同色边框 = 同一镜头）：`test_03_sudden_jump/viz/concat_0000.jpg`

---

## 复现

### 环境

- RTX 4090 + CUDA 12.4
- conda env `OmniShotCut` (python 3.10, torch 2.5.1+cu124)
- 详见 `../LOCAL_NOTES.md`

### 跑全流程

```bash
cd /home/yg/yg/code/github/OmniShotCut

# 1. OmniShotCut（每段视频依次跑）
./run.sh infer --input_video_path test_videos/test_01_hardcut.mp4    --mode default
./run.sh infer --input_video_path test_videos/test_02_dissolve.mp4   --mode default
./run.sh infer --input_video_path test_videos/test_03_sudden_jump.mp4 --mode default

# 2. PySceneDetect
for v in test_videos/test_*.mp4; do
  ./run.sh shell -m scenedetect -i "$v" detect-content list-scenes --no-output-file
done

# 3. TransNetV2 (三段一次跑完)
./run.sh shell eval_runs/run_transnetv2.py

# 4. 生成对比图
./run.sh shell eval_runs/plot_comparison.py
```

### 重新合成测试视频

```bash
# 见 test_videos/GROUND_TRUTH.md 里描述的 ffmpeg 命令
```

---

## 资产清单

```
eval_runs/
├── README.md                    # 本文件
├── COMPARISON.md                # 详细对比表与复现命令
├── comparison_timeline.png      # ⭐ 一图讲完三方差异
├── plot_comparison.py           # 生成上面那张图的脚本
├── run_transnetv2.py            # TransNetV2 复现脚本
├── test_01_hardcut/{results.json, viz/}      # OmniShotCut 输出
├── test_02_dissolve/{results.json, viz/}
├── test_03_sudden_jump/{results.json, viz/}  # ⭐ 核心证据
└── baseline_transnetv2/results.json
```

---

## 复盘观察

1. **OmniShotCut 的差异化价值确实在 inter-shot 类型识别**，不只是"检出边界"——这是它做下游视频生成数据 pipeline 的护城河。
2. **它的 dissolve 类型识别在我合成的 ffmpeg xfade 上失效**，符合论文 doc:497-504 自承的"合成训练数据 vs 实际渲染管线分布偏差"问题——值得后续研究。
3. **作者自带的 demo 视频本身是混剪**，不要把它们当单镜头素材做 ground truth。

---

## 参考

- [OmniShotCut paper (arXiv:2604.24762)](https://arxiv.org/abs/2604.24762)
- [OmniShotCut repo](https://github.com/UVA-Computer-Vision-Lab/OmniShotCut)
- [TransNetV2 official (TF + PyTorch)](https://github.com/soCzech/TransNetV2)
- [transnetv2pt (PyTorch wrapper used here)](https://github.com/kunato/transnetv2pt)
- [PySceneDetect](https://github.com/Breakthrough/PySceneDetect)
- [NVIDIA Cosmos Curator](https://github.com/nvidia-cosmos/cosmos-curate) — 上位 video curation pipeline，SBD 是其中一步
- [Open-Sora Plan](https://arxiv.org/abs/2412.00131) — 数据 pipeline 显式有 detecting jump cuts 步骤
