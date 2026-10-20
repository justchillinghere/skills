---
name: call-analysis
description: Transcribe a recorded call (OBS video or audio file) with the user's local taskConverter utility, then analyze it — key ideas, decisions, action items, open questions — and save the analysis next to the transcript for later work. Use when the user wants to process, transcribe, or discuss a recorded conversation, e.g. "разбери новый созвон", "сделай транскрипцию последнего звонка", "что мы решили на звонке 18 сентября", "/call-analysis [path]".
---

# Call Analysis

Pipeline: recording → taskConverter (ffmpeg → AssemblyAI with speaker labels) → raw transcript → analysis by you → `analysis.md` saved next to the transcript.

The transcription itself lives in the user's own utility, not in this skill. The user changes that utility over time, so always call it — never reimplement its steps here.

## Utility

- Project: `~/Projects/pet/taskConverter` (uv project, API keys in its `.env`).
- Calls with 2+ people: `main.py <file> --language ru`. Output folder: `~/Projects/pet/taskConverter/files/<stem>/`, transcript `<stem>_transcript_raw.txt` (lines `Speaker A: ...`). It also writes a short gpt-4o-mini `<stem>_summary.md` — ignore it, your analysis replaces it.
- Solo voice note (one speaker, e.g. `.ogg` from a messenger): `transcribe_ogg.py <file>`. Transcript: `files/<stem>/<stem>_transcript.txt`, no speaker labels.
- Run from any directory: `uv run --directory ~/Projects/pet/taskConverter main.py "<file>" --language ru`.
- Steps are cached: a rerun on the same file skips finished steps. `--force` redoes everything.
- If the utility's CLI looks different from this, run it with `--help` and follow the current flags.

## Workflow

### 1. Pick the recording

- An explicit path always wins.
- A date or description ("звонок 18 сентября") → match by filename in `~/Movies` (OBS names files `YYYY-MM-DD HH-MM-SS.mov`).
- No hint → the newest video/audio file in `~/Movies`.
- Announce the pick (filename, size, duration via `ffprobe`) before any paid step, so a wrong pick surfaces at once.

### 2. Reuse or transcribe

If `files/<stem>/` already has a transcript, skip to step 3 — the call was processed before. If it also has `analysis.md`, read that first; the user probably wants to discuss or extend it, not redo it.

Otherwise run the utility. AssemblyAI takes a few minutes for a long call: run the command in the background and wait for it to finish. If the call is not in Russian, pass the right `--language` code. On failure, show the utility's error output to the user — do not try a different transcription path.

### 3. Analyze

Read the whole transcript. Speakers are anonymous (`Speaker A`, `Speaker B`); infer who is who from context (names, roles, "I" statements) and say how sure you are. If the user is in the call, they are usually the one who recorded it.

Write `files/<stem>/analysis.md` in the language of the call:

```markdown
# <short topic> — <date from filename>

**Participants:** Speaker A = <name/role or "unknown">, Speaker B = ...

## Overview
2–4 sentences: what the call was about and how it ended.

## Key ideas
The substantial points, each with enough context to stand on its own months later.

## Decisions
What was agreed. Only real agreements, not proposals.

## Action items
- [ ] <who> — <what> — <deadline if mentioned>

## Open questions
Unresolved points, disagreements, things to check.

## Notable quotes
A few short verbatim quotes that capture positions or numbers precisely.
```

Skip a section if the call has nothing for it. Transcription errors are common with names and technical terms — fix obvious ones from context, and do not invent facts the transcript does not support.

### 4. Hand back

Give the user the overview and action items in chat, plus links to `analysis.md` and the transcript. Then continue in the direction the user takes: questions about the call, tasks, a follow-up message — use the transcript as the source of truth.
