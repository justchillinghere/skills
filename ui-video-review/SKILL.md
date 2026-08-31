---
name: ui-video-review
description: Turn a narrated screen recording (screencast where the user talks through UI feedback) into an interactive lavish review report and an exportable feedback.md + screenshots package for a fixer agent. Use when the user provides a video walkthrough of interface feedback to process, e.g. "разбери видео с фидбеком", "process my UI review recording", "/ui-video-review <path>".
---

# UI Video Review

Pipeline: video → transcript with timestamps → discrete feedback items → screenshots → interactive lavish report → exported `feedback.md` + `shots/` package → source video deleted.

## Input contract

- **A video path is required.** Never guess or auto-pick a recording; if the path is missing, ask for it.
- Optional but valuable: the target project (path or repo) the feedback is about. It drives terminology in summaries and is the export destination. If unknown by the export step, ask.
- Formats: whatever OBS produces (mp4 / mkv / mov) — ffmpeg reads them all.

## Requirements

- `ffmpeg` / `ffprobe` and `uv` on PATH (verify with `which` before starting).
- The first transcription downloads the MLX whisper model (~1.5 GB) from HuggingFace. Warn the user about this one-time wait before running it.

## Workflow

Keep all intermediates (wav, segments.json, candidate frames) in the session scratchpad, never in the user's project.

### 0. Precheck

```
ffprobe -v error -show_entries format=duration -show_entries stream=codec_type,width,height -of json <video>
```

Confirm an audio stream exists — stop with a clear message if the recording is silent. Note duration and resolution.

### 1. Extract audio

```
ffmpeg -y -i <video> -vn -ac 1 -ar 16000 <scratch>/audio.wav
```

### 2. Transcribe

```
uv run <skill_dir>/scripts/transcribe.py <scratch>/audio.wav --output <scratch>/segments.json
```

- Default model: `mlx-community/whisper-large-v3-turbo`, language autodetected (expect Russian or mixed ru/en narration).
- If the project uses distinctive terms (feature names, anglicisms like «баттон», «хедер»), pass `--initial-prompt "<comma-separated terms>"` to bias decoding.
- No diarization — recordings are solo by design.

### 3–5: run in a subagent

Stages 3–5 are heavy on context (full transcript, dozens of frames). Do NOT run them in the main conversation: spawn ONE general-purpose subagent with the video path, `segments.json`, the scratch directory, and the stage 3–5 instructions below. It returns compact JSON only — the item list, each item carrying the path of its single approved frame. The main agent sanity-checks the returned items and goes straight to the report; it never reads the full transcript or the rejected candidate frames.

Recordings usually start and end with the recorder's own UI (OBS) and meta narration («так, запись пошла…», «всё, выключаю»). This does not affect speech recognition; for items it is noise: produce no items from meta narration, and never pick a frame showing the recorder UI unless the remark is genuinely about it.

### 3. Split into feedback items (subagent)

Read `segments.json` and cut the narration into a numbered list of discrete items. For each item record:

- `t_start` / `t_end` in seconds — the moment the user is pointing at the thing
- `quote` — cleaned verbatim quote in the original language (drop filler words, keep meaning and tone)
- `summary` — one sentence, **in English**
- `action` — what to change, **in English**, concrete enough to act on
- `category` — `bug` / `ux` / `copy` / `style`
- `screen` — page or screen name, inferred from narration and frames
- `severity` — `high` / `medium` / `low`

Skip praise and positive remarks entirely — they do not become items.

### 4. Candidate frames (subagent)

For each item extract 3 candidates — at `t_start`, the interval midpoint, and `t_start + 2s` (clamped to video duration). People often narrate what was on screen a moment earlier or later, so never trust a single frame:

```
ffmpeg -ss <t> -i <video> -frames:v 1 -vf "scale='min(1440,iw)':-2" <scratch>/item<NN>-<k>.png
```

### 5. Vision pick (subagent)

Read each item's candidates and pick the frame where the discussed element is actually visible — the cursor position is a strong hint. If none of the three match the narration, widen the window to ±5 s, extract two more frames, and re-pick. Exactly one approved frame per item.

The subagent's final answer is JSON: `[{id, t_start, t_end, quote, summary, action, category, screen, severity, frame_path}]` — no prose, no transcript dumps.

### 6. Interactive report (lavish) — default, skippable

If the user asked for a non-interactive run («сразу артефакт», `--no-review`) or the skill runs in a headless/autonomous session, skip this stage: go straight to export (stage 7) with the subagent's items as-is, and say in the final reply that the package was produced without review.

Otherwise invoke the `lavish` skill and build `.lavish/ui-review-<slug>.html`:

- One card per item: screenshot (copy approved frames next to the HTML; reference with relative paths), timecode, original quote, English summary and action, category and severity badges.
- Sort by severity.
- Per the lavish `input` playbook, give each card controls: drop the item, request a different frame («возьми кадр на 01:31»), plus free annotation for rewording.
- Poll and apply feedback until the user approves the report.

### 7. Export

Only after the user approves the report:

- Destination: `<project>/.ui-feedback/<YYYY-MM-DD>-<slug>/` — a dot-directory so review packages stay out of commits.
- Ensure `.ui-feedback/` is listed in the project's `.gitignore`: check first, append the line only if missing; skip when the project is not a git repository.
- Write `feedback.md` (English, template below) and `shots/<NN>-<slug>.png` — the approved frames, numbered in item order.
- The package must be self-contained: a fixer agent receives this one directory and reads the screenshots via the relative paths.

### 8. Cleanup

Ask for one confirmation, then delete the source video and all intermediates. Never delete anything before a successful export.

## feedback.md template

```markdown
---
source: UI video review, <YYYY-MM-DD>
app: <project name> (<url or run context>)
video: deleted after processing; duration <MM:SS>
items: <N>
---

## 1. [bug/high] Tooltip covers the Save button
- Screen: profile settings
- Timecode: 01:24
- Screenshot: ./shots/01-save-button.png
- Said: «когда наводишь, тултип закрывает саму кнопку, кликнуть невозможно»
- Action: move the tooltip above the button and add an offset from its edge

## 2. [ux/medium] ...
```

Quotes stay in the original language; everything else is English.

## Recording tips (share when the user asks how to record)

- Speak in full phrases with context: «здесь, на странице логина, кнопка входа…» — it makes item splitting far more accurate.
- Keep the cursor on the element being discussed — it is visible in frames and guides the vision pick.
- Pause briefly between items — cleaner item boundaries.
- 2–5 minutes per recording works best; longer videos are processed in ~10-minute transcript chunks but produce one combined report.
