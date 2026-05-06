#!/usr/bin/env bash
# OmniShotCut launcher — 必须用 PYTHONNOUSERSITE=1 屏蔽 ~/.local/ 污染
# (~/.local/ 在 sys.path 里优先级高于 conda env, 不屏蔽会加载到旧版 torch/gradio)
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONNOUSERSITE=1
ENV_PYTHON="/home/yg/miniforge3/envs/OmniShotCut/bin/python"

case "${1:-app}" in
  app)
    exec "$ENV_PYTHON" app.py
    ;;
  infer)
    shift
    exec "$ENV_PYTHON" test_code/inference.py \
      --checkpoint_path "${CKPT:-checkpoints/OmniShotCut_ckpt.pth}" "$@"
    ;;
  shell)
    exec "$ENV_PYTHON" "$@"
    ;;
  *)
    echo "Usage: $0 [app|infer|shell] ..."
    echo "  app                  Start Gradio demo on 127.0.0.1:7860"
    echo "  infer --input_video_path X --mode clean_shot   Run CLI inference"
    echo "  shell <script.py>    Run a script under env Python"
    exit 1
    ;;
esac
