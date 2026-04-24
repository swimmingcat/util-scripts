"""
Find photos containing a specific person using face recognition.

Setup:
  1. Create a 'references/' folder next to this script
  2. Add several reference photos of the person (different angles, with/without mask)
  3. Run: uv run find_person_photos.py

Matching photos are copied to OUTPUT_DIR.

Tuning:
  - Lower THRESHOLD (e.g. 0.3) → higher recall, more false positives
  - Higher THRESHOLD (e.g. 0.5) → higher precision, may miss masked/angled faces

Resumability:
  - A checkpoint file (CHECKPOINT_FILE) records every processed photo with its best
    similarity score. On re-run, photos already confirmed as matches are skipped.
    Photos that previously didn't match are re-evaluated against the current THRESHOLD
    without re-running face recognition — so you can tune the threshold cheaply.
  - Delete the checkpoint file to force a full re-scan.
"""

import csv
import os
import shutil

import cv2
import numpy as np
from insightface.app import FaceAnalysis

# ── Configure these ───────────────────────────────────────────────────────────

PHOTOS_DIR = "/Users/luyuzhao/Documents/photo_project/brightwheel_photos"
REFERENCE_DIR = "/Users/luyuzhao/Documents/photo_project/references"
OUTPUT_DIR = "/Users/luyuzhao/Documents/photo_project/brightwheel_photos_person"
CHECKPOINT_FILE = "/Users/luyuzhao/Documents/photo_project/brightwheel_photos_person_checkpoint.csv"
THRESHOLD = 0.4  # cosine similarity; lower = more matches (higher recall)

# ─────────────────────────────────────────────────────────────────────────────

PHOTO_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

# Checkpoint row schema: filename, status ("match"|"no_match"|"no_face"), ref, sim
_MATCH = "match"
_NO_MATCH = "no_match"
_NO_FACE = "no_face"


def load_checkpoint(path: str) -> dict[str, tuple[str, str, float]]:
    """Returns {filename: (status, ref, sim)}."""
    result: dict[str, tuple[str, str, float]] = {}
    if not os.path.exists(path):
        return result
    with open(path, newline="") as f:
        for row in csv.reader(f):
            if len(row) == 4:
                filename, status, ref, sim_str = row
                result[filename] = (status, ref, float(sim_str))
    return result


def append_checkpoint(path: str, filename: str, status: str, ref: str, sim: float) -> None:
    with open(path, "a", newline="") as f:
        csv.writer(f).writerow([filename, status, ref, f"{sim:.6f}"])


def load_app() -> FaceAnalysis:
    app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
    app.prepare(ctx_id=0, det_size=(640, 640))
    return app


def get_embeddings(app: FaceAnalysis, image_path: str) -> list[np.ndarray]:
    img = cv2.imread(image_path)
    if img is None:
        return []
    faces = app.get(img)
    return [face.normed_embedding for face in faces]


def matches_any(
    embeddings: list[np.ndarray],
    refs: list[tuple[str, np.ndarray]],
    threshold: float,
) -> tuple[bool, str, float]:
    best_sim = 0.0
    best_ref = ""
    for face_emb in embeddings:
        for ref_name, ref_emb in refs:
            # normed_embedding is L2-normalized, so dot product = cosine similarity
            sim = float(np.dot(face_emb, ref_emb))
            if sim >= threshold:
                return True, ref_name, sim
            if sim > best_sim:
                best_sim = sim
                best_ref = ref_name
    return False, best_ref, best_sim


def load_references(app: FaceAnalysis, ref_dir: str) -> list[tuple[str, np.ndarray]]:
    refs = []
    for filename in sorted(os.listdir(ref_dir)):
        if os.path.splitext(filename)[1].lower() not in PHOTO_EXTS:
            continue
        path = os.path.join(ref_dir, filename)
        embeddings = get_embeddings(app, path)
        if not embeddings:
            print(f"  WARNING: no face detected in reference: {filename}")
            continue
        if len(embeddings) > 1:
            print(f"  WARNING: multiple faces in {filename}, using the first/largest")
        refs.append((filename, embeddings[0]))
        print(f"  Loaded: {filename}")
    return refs


def main() -> None:
    if not os.path.isdir(REFERENCE_DIR):
        raise SystemExit(
            f"Reference directory '{REFERENCE_DIR}' not found.\n"
            "Create it and add reference photos of the person."
        )

    print("Loading face recognition model (first run downloads ~300MB)...")
    app = load_app()

    print(f"\nLoading references from '{REFERENCE_DIR}'...")
    refs = load_references(app, REFERENCE_DIR)
    if not refs:
        raise SystemExit("No valid reference photos found in references/.")
    print(f"  {len(refs)} reference(s) loaded.\n")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    checkpoint = load_checkpoint(CHECKPOINT_FILE)
    if checkpoint:
        print(f"Loaded checkpoint: {len(checkpoint)} previously processed photos.\n")

    photos = sorted(
        f for f in os.listdir(PHOTOS_DIR)
        if os.path.splitext(f)[1].lower() in PHOTO_EXTS
    )
    print(f"Scanning {len(photos)} photos (threshold={THRESHOLD})...\n")

    matched = 0
    no_face = 0
    skipped = 0

    for i, filename in enumerate(photos, 1):
        prior = checkpoint.get(filename)

        # Already confirmed match — skip inference and copy
        if prior and prior[0] == _MATCH:
            matched += 1
            skipped += 1
            dest = os.path.join(OUTPUT_DIR, filename)
            if not os.path.exists(dest):
                shutil.copy2(os.path.join(PHOTOS_DIR, filename), dest)
            print(f"  [{i}/{len(photos)}] skip(match) {prior[2]:.2f} (vs {prior[1]}): {filename}")
            continue

        # Previously had no face — skip inference entirely
        if prior and prior[0] == _NO_FACE:
            no_face += 1
            skipped += 1
            print(f"  [{i}/{len(photos)}] skip(no face): {filename}")
            continue

        # Previously a no-match — re-evaluate stored sim against current threshold
        if prior and prior[0] == _NO_MATCH:
            _, ref_name, sim = prior
            if sim >= THRESHOLD:
                matched += 1
                skipped += 1
                dest = os.path.join(OUTPUT_DIR, filename)
                shutil.copy2(os.path.join(PHOTOS_DIR, filename), dest)
                print(f"  [{i}/{len(photos)}] skip(re-eval MATCH) {sim:.2f} (vs {ref_name}): {filename}")
            else:
                skipped += 1
                print(f"  [{i}/{len(photos)}] skip(re-eval no match) {sim:.2f}: {filename}")
            continue

        # Not in checkpoint — run inference
        path = os.path.join(PHOTOS_DIR, filename)
        embeddings = get_embeddings(app, path)

        if not embeddings:
            no_face += 1
            append_checkpoint(CHECKPOINT_FILE, filename, _NO_FACE, "", 0.0)
            print(f"  [{i}/{len(photos)}] no face:  {filename}")
            continue

        found, ref_name, sim = matches_any(embeddings, refs, THRESHOLD)
        if found:
            matched += 1
            shutil.copy2(path, os.path.join(OUTPUT_DIR, filename))
            append_checkpoint(CHECKPOINT_FILE, filename, _MATCH, ref_name, sim)
            print(f"  [{i}/{len(photos)}] MATCH {sim:.2f} (vs {ref_name}): {filename}")
        else:
            append_checkpoint(CHECKPOINT_FILE, filename, _NO_MATCH, ref_name, sim)
            print(f"  [{i}/{len(photos)}] no match {sim:.2f}: {filename}")

    print(f"\nDone. {matched}/{len(photos)} matched → {OUTPUT_DIR}/")
    if skipped:
        print(f"  ({skipped} skipped via checkpoint)")
    if no_face:
        print(f"  ({no_face} photos had no detectable face — not copied)")


if __name__ == "__main__":
    main()
