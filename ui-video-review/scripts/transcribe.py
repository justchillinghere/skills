#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["mlx-whisper"]
# ///
"""Transcribe an audio or video file to JSON segments with word-level timestamps.

Part of the ui-video-review skill: the JSON output feeds the LLM pass that
splits the narration into discrete UI feedback items.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DEFAULT_MODEL = "mlx-community/whisper-large-v3-turbo"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="audio or video file (decoded via ffmpeg)")
    parser.add_argument("--output", type=Path, default=None, help="write JSON here instead of stdout")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"HF repo of the MLX whisper model (default: {DEFAULT_MODEL})")
    parser.add_argument("--language", default=None, help="ISO 639-1 language code; omit to autodetect")
    parser.add_argument("--initial-prompt", default=None, help="glossary/context to bias decoding (project terms, feature names)")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not args.input.exists():
        print(f"input not found: {args.input}", file=sys.stderr)
        return 2

    # Deferred import: mlx-whisper pulls in mlx and takes seconds to load;
    # keep --help and the missing-input error instant.
    import mlx_whisper

    result = mlx_whisper.transcribe(
        str(args.input),
        path_or_hf_repo=args.model,
        word_timestamps=True,
        language=args.language,
        initial_prompt=args.initial_prompt,
    )

    payload = {
        "language": result.get("language"),
        "segments": [
            {
                "start": round(float(segment["start"]), 2),
                "end": round(float(segment["end"]), 2),
                "text": segment["text"].strip(),
                "words": [
                    {
                        "word": word["word"].strip(),
                        "start": round(float(word["start"]), 2),
                        "end": round(float(word["end"]), 2),
                    }
                    for word in segment.get("words", [])
                ],
            }
            for segment in result["segments"]
        ],
    }

    text = json.dumps(payload, ensure_ascii=False, indent=1)
    if args.output is None:
        print(text)
    else:
        args.output.write_text(text, encoding="utf-8")
        print(f"wrote {args.output} ({len(payload['segments'])} segments)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
