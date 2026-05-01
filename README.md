# mcp-cut

An MCP server that programmatically builds CapCut macOS drafts. Generates
the `draft_info.json` / `draft_meta_info.json` files CapCut reads, so you
can author timelines, captions, keyframes, and overlays from code (or from
an LLM via MCP) and open the result in CapCut for final tweaks/export.

Tested against CapCut macOS 8.5 (draft schema `new_version: 167.0.0`,
`version: 360000`).

## Why

CapCut has no scripting API. The two paths to automate it are GUI control
(brittle) and writing the project files directly (the path here). This
project mirrors the on-disk schema for the parts of the timeline that
matter for short-form / explainer / cartoon workflows.

## Install

```bash
git clone <this repo>
cd mcp-cut
uv sync
```

Requires:
- macOS with CapCut installed at `/Applications/CapCut.app`
- Python 3.10+ (uv will install it)

## Run

```bash
uv run mcp-cut
```

The server listens on `http://127.0.0.1:5656/mcp/` (Streamable HTTP
transport). Wire it into Claude Code, Cursor, or any MCP-compatible
client by adding to your MCP config:

```json
{
  "mcpServers": {
    "mcp-cut": {
      "type": "http",
      "url": "http://127.0.0.1:5656/mcp/"
    }
  }
}
```

## Quick start

A 4-line caption pipeline that takes an audio file + Whisper SRT and
produces an opened CapCut draft:

```python
create_draft(name="my-video", width=1920, height=1080, fps=30)
add_audio(draft="my-video", audio_path="/path/to/voiceover.mp3", duration_seconds=60)
add_captions_from_srt(draft="my-video", srt_path="/path/to/whisper.srt", style="karaoke_box")
open_in_capcut(draft="my-video")
```

## Tools (24)

CapCut drafts live at:
- macOS: `~/Movies/CapCut/User Data/Projects/com.lveditor.draft/<name>/`
- Windows: `%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft\<name>\`
- Linux (best effort): `~/.local/share/CapCut/drafts/<name>/`

Override via `CAPCUT_DRAFTS_DIR` env var if your install is elsewhere.

All media-accepting tools (`add_image`, `add_video`, `add_audio`,
`add_image_sequence`, `probe_media`) accept either a local path **or** an
`http(s)://` URL. URLs are downloaded into `~/.cache/mcp-cut/downloads/`
and reused across runs (cache key = SHA-256 of the URL).

When a media file is added to a draft, `mcp-cut` copies it into
`<draft>/mcp_cut_media/` and stores that staged path in the CapCut schema.
This avoids macOS sandbox/security-scoped access problems when CapCut opens a
programmatically generated draft that references arbitrary external files.

When `ffprobe` is available, missing dimensions/durations are auto-probed
— `add_video(video_path=..., duration_seconds=None)` uses the source's
full length; `add_image` auto-detects pixel dimensions.

### Draft lifecycle

| Tool | Purpose |
|---|---|
| `list_drafts()` | Every draft on disk with duration / canvas / fps |
| `inspect_draft(draft)` | Tracks + segment IDs + transforms for one draft |
| `create_draft(name, width=1080, height=1920, fps=30)` | Empty portrait draft by default |
| `delete_draft(draft)` | Recursively remove the draft folder |
| `probe_media(path)` | ffprobe wrapper: returns duration / dimensions / fps for a local path or URL |

### Visual content

| Tool | Purpose |
|---|---|
| `add_image(draft, image_path, duration_seconds, width=1920, height=1080, start_seconds=None, track_index=0)` | Place a still image |
| `add_video(draft, video_path, duration_seconds, width, height, source_start_seconds=0, has_audio=True, start_seconds=None, track_index=0)` | Place a video clip |
| `add_image_sequence(draft, image_paths, frame_seconds=0.1, start_seconds=None, track_index=0, width=1920, height=1080)` | Append a frame-by-frame flipbook (the cartoon technique) |

### Audio

| Tool | Purpose |
|---|---|
| `add_audio(draft, audio_path, duration_seconds, start_seconds=0, source_start_seconds=0, track_index=0)` | Place an audio clip; `track_index>0` for SFX/music layers |

### Text & captions

| Tool | Purpose |
|---|---|
| `add_text(draft, text, duration_seconds, start_seconds=0, font_size=15, color_hex="#FFFFFF", ...)` | One styled text overlay (titles, lower-thirds). Supports border, shadow, background pill, language fonts, per-range highlight |
| `add_captions_from_srt(draft, srt_path, style="youtube", ...)` | Bulk-add styled captions from an SRT. Auto-detects script (Arabic/CJK/Latin/etc.) and picks the matching CapCut system font |

### Editing

| Tool | Purpose |
|---|---|
| `set_clip_transform(draft, segment_id, x=None, y=None, scale_x=None, scale_y=None, rotation=None, alpha=None, ...)` | Static position / scale / rotation / opacity |
| `set_segment_volume(draft, segment_id, volume)` | Per-clip volume (1.0 = unchanged, 0.0 = mute) |
| `move_segment(draft, segment_id, start_seconds)` | Reposition on timeline |
| `trim_segment(draft, segment_id, duration_seconds=None, source_start_seconds=None)` | Adjust duration and/or source offset |
| `delete_segment(draft, segment_id)` | Remove one segment |
| `clear_track(draft, track_type, track_index=0)` | Empty one track + GC orphan materials |
| `clear_text_tracks(draft)` | Empty every text track + GC — use to re-run captions cleanly |
| `remove_time_ranges(draft, starts_seconds, ends_seconds)` | Cut multiple time ranges out of the timeline; survivors shift left to close the gaps. Splits segments that span a cut |

### Animation

| Tool | Purpose |
|---|---|
| `add_keyframe(draft, segment_id, time_seconds, property, value, curve="Line")` | Animate `x`, `y`, `scale_x`, `scale_y`, `rotation`, `alpha`, or `volume` over time. Two+ keyframes on the same property → CapCut interpolates |
| `add_keyframes(draft, segment_id, property, times_seconds, values, curve="Line")` | Batch version — set N keyframes on one property in a single call (parallel arrays of times + values) |

### Smart editing (talking-head workflows)

| Tool | Purpose |
|---|---|
| `get_auto_captions(draft)` | Read CapCut's auto-generated captions back out of a draft (text + per-word timings). Detects materials with `recognize_task_id` set by CapCut's "Text → Auto Captions" |
| `smart_cut_draft(draft, silence_threshold_seconds=1.0, duplicate_similarity_threshold=0.6, cut_silences=True, cut_duplicates=True, dry_run=False)` | Auto-edit using auto-captions: removes silences (gaps > threshold) and duplicate takes (keeps the last version of repeated phrases). Heuristic ported from [sun-guannan/capcut-ai-editor](https://github.com/sun-guannan/capcut-ai-editor) |

### System

| Tool | Purpose |
|---|---|
| `open_in_capcut(draft=None)` | Launch the CapCut app. Switch tabs in CapCut Home to refresh the Drafts list |

## Caption styles

`add_captions_from_srt(..., style=...)` selects a preset.

**Static** — one segment per SRT block:
| Style | Look |
|---|---|
| `youtube` | bold white + thick black outline + shadow (default) |
| `subtitle` | white on translucent dark pill |
| `tiktok` | bold yellow + outline + shadow |
| `minimal` | plain white + light shadow only |

**Per-word animated** — N segments per SRT block, one per word, timed
proportionally to character count within the caption duration:
| Style | Look |
|---|---|
| `karaoke` | full caption visible, current word's fill turns yellow as audio progresses |
| `karaoke_box` | full caption visible, current word stays white but gets a thick yellow stroke that reads as a highlight box behind it |
| `wordbox` | one word at a time displayed alone in a yellow pill |

Defaults are tuned for 1920×1080 lower-third placement. For portrait
(1080×1920), pass `y=0.30` and `font_size=16` — captions need more
vertical headroom.

## Iterating on the same draft

CapCut caches drafts in memory; it won't pick up disk changes while a
draft is open. The pattern:

```python
clear_text_tracks(draft="my-video")
add_captions_from_srt(draft="my-video", srt_path=..., style="karaoke_box")
# Then close + reopen the draft in CapCut to load the new captions.
```

`clear_track` / `clear_text_tracks` also garbage-collect orphan materials,
so iterating doesn't bloat the draft file.

## Coordinate system

- `x`, `y` — normalized; `(0, 0)` is canvas center, ~`[-1, 1]` covers the
  visible canvas.
- `scale_x`, `scale_y` — multipliers; `1.0` = native pixel size.
- `rotation` — degrees, clockwise.
- `alpha` — opacity, `0.0` to `1.0`.
- All time values exposed in tools are seconds; the on-disk format uses
  microseconds (the conversion is handled internally).

## Languages / fonts

Auto-detected from the text's Unicode range:

| Script | Font path |
|---|---|
| Latin (Bold) | `CapCutSansText-Bold.otf` |
| Latin (Regular) | `CapCutSansText-Regular.otf` |
| Arabic | `NotoSansArabic-Regular.ttf` |
| Hebrew | `NotoSansHebrew-Regular.ttf` |
| Bengali | `NotoSansBengali-Regular.ttf` |
| Japanese | `ja.ttf` |
| Korean | `ko.ttf` |
| Chinese (Simplified) | `zh-hans.ttf` |
| Chinese (Traditional) | `zh-hant.ttf` |
| Thai | `th.ttf` |

All shipped inside `CapCut.app`. Pass `language="ar"` etc. to override
auto-detection, or `font_path="/abs/path/to.ttf"` for a custom font.

## What's not (yet) supported

These need a captured reference draft (created manually in CapCut so we
can mirror the schema). PRs welcome.

- **CapCut Pro caption templates** (the trending highlight/box presets).
  `karaoke_box` approximates the look via a thick stroke; templates
  themselves use proprietary effect resource IDs that aren't generatable
  from scratch.
- **Built-in filters / effects / transitions.** Same reason — each effect
  has a hashed resource ID we'd need to harvest.
- **Per-letter or per-word animation timing** beyond the linear
  char-count weighting we already do.

## Architecture

```
src/mcp_cut/
├── server.py     FastMCP server, tools wired to draft.py
├── draft.py      Schema generators for draft_info.json + draft_meta_info.json
└── paths.py      CapCut macOS paths
```

The draft schema is mirrored from a real CapCut-created draft on the
author's machine. Time units are microseconds. UUIDs are uppercase. Every
text segment must reference one `sticker_animation` aux material. Every
video segment references six aux materials (speed, placeholder_info,
canvas, sound_channel_mapping, material_color, vocal_separation). Audio
segments reference five (speed, placeholder_info, beats,
sound_channel_mapping, vocal_separation).

`new_version: "167.0.0"` corresponds to CapCut 8.5; older versions of
CapCut may upgrade-on-open or refuse the file.

### Schema notes

A few non-obvious things confirmed against real CapCut drafts that may
matter if you extend the schema:

- Most time fields are **microseconds**, but `materials.texts[].words.{start_time, end_time}` are **milliseconds** relative to the segment start. `get_auto_captions` converts these to absolute seconds for you.
- Auto-generated subtitles have `recognize_task_id != ""` on the text material; manually-added text leaves it empty.
- Text segments use `render_index: 14000` and `track_render_index: <position in tracks[]>`. Video segments use `render_index: 0`.
- Each text segment must reference exactly one `material_animations` entry of `type: "sticker_animation"` (else CapCut silently drops the text).
- `font_path` is required and must point to an existing TTF/OTF — empty string makes the text invisible. CapCut's bundled fonts live in `/Applications/CapCut.app/Contents/Resources/Font/SystemFont/`.

## License

MIT — see [LICENSE](LICENSE).
