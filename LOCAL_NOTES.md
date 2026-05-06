# 本地部署速查（光哥本机 RTX 4090, conda env: OmniShotCut）

## 启动 Gradio demo
```bash
cd /home/yg/yg/code/github/OmniShotCut
./run.sh app
```
浏览器打开 http://127.0.0.1:7860

## 命令行推理（推荐做对比 demo 用）
```bash
# clean_shot 模式：直接吐出干净分镜（不带转场标签）
./run.sh infer --input_video_path /path/to/your.mp4 --mode clean_shot

# default 模式：完整三件套（范围 + 镜头内类型 + 镜头间关系）
./run.sh infer --input_video_path /path/to/your.mp4 --mode default
```
结果默认写入 `demo_video_results/`。

## 关键约束（踩过的坑）

1. **必须 `PYTHONNOUSERSITE=1`**：~/.local/ 在 sys.path 里优先级高于 conda env，
   不屏蔽就会从 ~/.local/ 加载到旧版 torch / gradio。`run.sh` 已经 export 了，
   只要走 `run.sh` 就没事。直接 `python app.py` 会炸。
2. **绝不要 `pip install`，要用 `python -m pip`**：env 创建时 PATH 里 `pip` 命令
   指向 `~/.local/bin/pip`，会把包装到 ~/.local/ 污染所有环境。要装包：
   ```bash
   PYTHONNOUSERSITE=1 /home/yg/miniforge3/envs/OmniShotCut/bin/python -m pip install <pkg>
   ```
3. **app.py 已改本地化**：原版 `demo.launch(share=True)` 会开 gradio.live 公网
   隧道，违反公司 staff-wifi 网络规则。已改为 `server_name="127.0.0.1", share=False`。
4. **GPU 显存**：模型本身 < 1GB，但有其他进程占着显存时（ollama / vllm / digithuman
   服务），可能 OOM。冲突时先 `nvidia-smi` 看占用并选择性 kill。

## 仓库改动清单
- `app.py:357` — `share=True` → `server_name="127.0.0.1", server_port=7860, share=False`
- 新增 `run.sh` — 永久解决 PYTHONNOUSERSITE
- 新增 `LOCAL_NOTES.md`（本文）
