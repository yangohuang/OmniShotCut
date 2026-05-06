"""Three-way SBD comparison timeline plot.
Reads OmniShotCut + TransNetV2 + (hard-coded) PySceneDetect results,
overlays them on a per-video timeline with GT markers.
"""
import json
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

REPO = Path("/home/yg/yg/code/github/OmniShotCut")
OUT = REPO / "eval_runs"

# Ground truth + total frames (manual, from GROUND_TRUTH.md)
GT = {
    "test_01_hardcut": {
        "n_frames": 300,
        "boundaries": [150],
        "transitions": [],
        "gt_type": "Hard_Cut",
    },
    "test_02_dissolve": {
        "n_frames": 270,
        "boundaries": [],
        "transitions": [(120, 149)],
        "gt_type": "Dissolve",
    },
    "test_03_sudden_jump": {
        "n_frames": 300,
        "boundaries": [150],
        "transitions": [],
        "gt_type": "Sudden_Jump",
    },
}

# PySceneDetect results (from prior CLI run)
PSD = {
    "test_01_hardcut":     [60, 124, 150, 225],
    "test_02_dissolve":    [60, 124, 195],
    "test_03_sudden_jump": [],
}

# Load TransNetV2 + OmniShotCut JSONs
with open(OUT / "baseline_transnetv2/results.json") as f:
    tnv2_raw = {Path(r["video_path"]).stem: r["boundaries"] for r in json.load(f)}

osc_raw = {}
osc_labels = {}
for name in GT:
    p = OUT / name / "results.json"
    with open(p) as f:
        rec = json.load(f)[0]
    ranges = rec["pred_ranges"]
    inter = rec["pred_inter_labels"]
    bounds, labels = [], []
    for i, r in enumerate(ranges):
        if i == 0:
            continue
        bounds.append(r[0])
        labels.append(inter[i])
    osc_raw[name] = bounds
    osc_labels[name] = labels


def color_for_label(label: str) -> str:
    return {
        "Hard_Cut": "#2196f3",
        "Sudden_Jump": "#e53935",
        "Dissolve": "#fb8c00",
        "Transition": "#fb8c00",
        "New_Start": "#9e9e9e",
    }.get(label, "#7e57c2")


fig, axes = plt.subplots(3, 1, figsize=(13, 7), constrained_layout=True)

method_y = {"PySceneDetect": 2, "TransNetV2": 1, "OmniShotCut": 0}
method_color = {
    "PySceneDetect": "#777777",
    "TransNetV2":    "#777777",
    "OmniShotCut":   "#2196f3",
}

for ax, (name, gt) in zip(axes, GT.items()):
    n = gt["n_frames"]

    # GT shading for transitions
    for ts, te in gt["transitions"]:
        ax.axvspan(ts, te, color="#ffe082", alpha=0.6, zorder=0,
                   label=f"GT {gt['gt_type']} [{ts},{te}]")
    # GT boundary lines
    for b in gt["boundaries"]:
        ax.axvline(b, color="#d32f2f", linestyle="--", linewidth=2, zorder=1,
                   label=f"GT {gt['gt_type']} @ {b}")

    # Method lanes
    for method, y in method_y.items():
        ax.hlines(y, 0, n, color="#bbbbbb", linewidth=1, zorder=2)

    # PySceneDetect
    for b in PSD[name]:
        ax.plot(b, method_y["PySceneDetect"], "v",
                color=method_color["PySceneDetect"], markersize=10, zorder=3)
    # TransNetV2
    for b in tnv2_raw[name]:
        ax.plot(b, method_y["TransNetV2"], "v",
                color=method_color["TransNetV2"], markersize=10, zorder=3)
    # OmniShotCut (color by label)
    for b, lab in zip(osc_raw[name], osc_labels[name]):
        ax.plot(b, method_y["OmniShotCut"], "v",
                color=color_for_label(lab), markersize=12, zorder=4,
                markeredgecolor="black", markeredgewidth=0.5)
        ax.annotate(lab, (b, method_y["OmniShotCut"] - 0.18),
                    fontsize=7, ha="center", color=color_for_label(lab))

    ax.set_xlim(-5, n + 5)
    ax.set_ylim(-0.6, 2.6)
    ax.set_yticks(list(method_y.values()))
    ax.set_yticklabels(list(method_y.keys()))
    ax.set_xlabel("Frame index")
    ax.set_title(f"{name}.mp4  ({n} frames, GT type = {gt['gt_type']})",
                 fontsize=11, fontweight="bold")
    ax.grid(axis="x", linestyle=":", alpha=0.4)

    # Single legend
    handles = [
        mpatches.Patch(color="#d32f2f", label="GT boundary"),
        mpatches.Patch(color="#ffe082", label="GT transition zone"),
        plt.Line2D([0], [0], marker="v", color="w",
                   markerfacecolor="#777777", markersize=10,
                   label="baseline detection"),
        plt.Line2D([0], [0], marker="v", color="w",
                   markerfacecolor="#e53935", markersize=10,
                   label="OmniShotCut: Sudden_Jump"),
        plt.Line2D([0], [0], marker="v", color="w",
                   markerfacecolor="#2196f3", markersize=10,
                   label="OmniShotCut: Hard_Cut"),
    ]
    if name == "test_03_sudden_jump":
        ax.legend(handles=handles, loc="upper right", fontsize=8, ncol=2)

fig.suptitle("Shot Boundary Detection — three-way comparison on synthetic test set",
             fontsize=13, fontweight="bold")

out_png = OUT / "comparison_timeline.png"
fig.savefig(out_png, dpi=140, bbox_inches="tight")
print(f"Saved: {out_png}")
