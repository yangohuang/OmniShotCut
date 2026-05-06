"""Run TransNetV2 (PyTorch port via kunato/transnetv2pt) on the 3 test videos.
predict_video returns ndarray of shape (N, 2): each row is [start_frame, end_frame].
Boundaries are derived as the start_frame of every scene after the first.
"""
import json
from pathlib import Path

import numpy as np
from transnetv2pt import predict_video

REPO = Path("/home/yg/yg/code/github/OmniShotCut")
TEST_VIDEOS = [
    REPO / "test_videos/test_01_hardcut.mp4",
    REPO / "test_videos/test_02_dissolve.mp4",
    REPO / "test_videos/test_03_sudden_jump.mp4",
]
OUT_DIR = REPO / "eval_runs/baseline_transnetv2"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    results = []
    for video in TEST_VIDEOS:
        print(f"\n=== {video.name} ===")
        scenes = np.asarray(predict_video(str(video)))
        scenes_list = [[int(s), int(e)] for s, e in scenes]
        boundaries = [scenes_list[i][0] for i in range(1, len(scenes_list))]

        print(f"  num scenes: {len(scenes_list)}")
        print(f"  scenes: {scenes_list}")
        print(f"  inferred boundaries (start of shot 2..N): {boundaries}")

        results.append({
            "video_path": f"test_videos/{video.name}",
            "num_scenes": len(scenes_list),
            "scenes": scenes_list,
            "boundaries": boundaries,
        })

    out_path = OUT_DIR / "results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
