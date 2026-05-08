"""MCP server exposing CapCut draft authoring over Streamable HTTP.

Run:
    uv run mcp-cut          # listens on http://127.0.0.1:5656/mcp/
"""

from __future__ import annotations

import subprocess
from typing import Any

from mcp.server.fastmcp import FastMCP

from . import draft as D
from .paths import CAPCUT_PROJECTS_ROOT, draft_dir

HOST = "127.0.0.1"
PORT = 5656

mcp = FastMCP("mcp-cut", host=HOST, port=PORT)


# ---- discovery / lifecycle -------------------------------------------------

@mcp.tool()
def list_drafts() -> list[dict[str, Any]]:
    """List every CapCut draft in the projects folder with basic metadata."""
    return D.list_drafts()


@mcp.tool()
def inspect_draft(draft: str) -> dict[str, Any]:
    """Return the tracks/segments of a draft (id, start, duration, transform)."""
    return D.inspect_draft(draft)


@mcp.tool()
def create_draft(
    name: str,
    width: int = 1080,
    height: int = 1920,
    fps: float = 30.0,
) -> dict[str, Any]:
    """Create an empty CapCut draft folder.

    Args:
        name: folder name shown in the CapCut Drafts list.
        width / height: canvas size (default 1080x1920 portrait).
        fps: project frame rate (default 30).
    """
    folder = D.create_draft(name=name, width=width, height=height, fps=fps)
    return {"draft": name, "path": str(folder)}


@mcp.tool()
def delete_draft(draft: str) -> dict[str, Any]:
    """Delete a draft folder and all its contents. Irreversible."""
    return D.delete_draft(draft)


@mcp.tool()
def probe_media(path: str) -> dict[str, Any]:
    """Probe a media file with ffprobe; report duration / width / height /
    fps / streams. Accepts a local path OR an http(s):// URL (which gets
    downloaded into the cache first).

    Useful for callers that want to inspect a clip before adding it, or to
    pass exact dimensions / duration into add_image / add_video / add_audio.
    Requires ffprobe (install with `brew install ffmpeg` on macOS).
    """
    return D.probe_media(path)


# ---- visual content --------------------------------------------------------

@mcp.tool()
def add_image(
    draft: str,
    image_path: str,
    duration_seconds: float,
    width: int | None = None,
    height: int | None = None,
    start_seconds: float | None = None,
    track_index: int = 0,
) -> dict[str, Any]:
    """Place an image on a video track.

    Args:
        draft: draft name.
        image_path: local path OR http(s):// URL (auto-downloaded into the
            cache at ~/.cache/mcp-cut/downloads/).
        duration_seconds: how long the image displays (required for stills).
        width / height: source pixel dimensions; auto-probed via ffprobe
            when None (falls back to 1920×1080 if ffprobe missing).
        start_seconds: timeline placement; None = append after last segment.
        track_index: 0 = base video track, 1+ = overlay tracks.
    """
    return D.add_image(
        name=draft, image_path=image_path,
        duration_seconds=duration_seconds,
        width=width, height=height,
        start_seconds=start_seconds, track_index=track_index,
    )


@mcp.tool()
def add_video(
    draft: str,
    video_path: str,
    duration_seconds: float | None = None,
    width: int | None = None,
    height: int | None = None,
    source_start_seconds: float = 0.0,
    has_audio: bool = True,
    start_seconds: float | None = None,
    track_index: int = 0,
) -> dict[str, Any]:
    """Place a video clip on a video track.

    Args:
        draft: draft name.
        video_path: local path OR http(s):// URL (auto-downloaded).
        duration_seconds: timeline duration; None = full source length
            (auto-probed via ffprobe).
        width / height: source dimensions; None = auto-probed.
        source_start_seconds: trim head — offset into the source.
        has_audio: set False to mute the embedded audio.
        start_seconds: timeline placement; None = append on this track.
        track_index: 0 = base video track, 1+ = overlays.
    """
    return D.add_video(
        name=draft, video_path=video_path,
        duration_seconds=duration_seconds,
        width=width, height=height,
        source_start_seconds=source_start_seconds,
        has_audio=has_audio,
        start_seconds=start_seconds, track_index=track_index,
    )


@mcp.tool()
def add_image_sequence(
    draft: str,
    image_paths: list[str],
    frame_seconds: float = 0.1,
    start_seconds: float | None = None,
    track_index: int = 0,
    width: int = 1920,
    height: int = 1080,
) -> dict[str, Any]:
    """Append a sequence of images one after another at `frame_seconds` each.

    Use this for the frame-by-frame cartoon/whiteboard technique: pass a list
    of frame PNGs in order. Default 0.1s per frame = 10fps. After import you
    can group them into a CapCut compound clip manually if desired.
    """
    return D.add_image_sequence(
        name=draft, image_paths=image_paths,
        frame_seconds=frame_seconds,
        start_seconds=start_seconds, track_index=track_index,
        width=width, height=height,
    )


# ---- audio -----------------------------------------------------------------

@mcp.tool()
def add_audio(
    draft: str,
    audio_path: str,
    duration_seconds: float | None = None,
    start_seconds: float = 0.0,
    source_start_seconds: float = 0.0,
    track_index: int = 0,
) -> dict[str, Any]:
    """Place an audio clip on an audio track.

    Args:
        draft: draft name.
        audio_path: local path OR http(s):// URL (auto-downloaded).
        duration_seconds: portion of the source to use; None = full
            source length (auto-probed via ffprobe).
        start_seconds: timeline placement (default 0).
        source_start_seconds: trim head — offset into the source.
        track_index: 0 = base audio track, 1+ = additional audio layers.
    """
    return D.add_audio(
        name=draft, audio_path=audio_path,
        duration_seconds=duration_seconds,
        start_seconds=start_seconds,
        source_start_seconds=source_start_seconds,
        track_index=track_index,
    )


# ---- segment editing -------------------------------------------------------

@mcp.tool()
def set_clip_transform(
    draft: str,
    segment_id: str,
    x: float | None = None,
    y: float | None = None,
    scale_x: float | None = None,
    scale_y: float | None = None,
    rotation: float | None = None,
    alpha: float | None = None,
    flip_horizontal: bool | None = None,
    flip_vertical: bool | None = None,
) -> dict[str, Any]:
    """Set the static transform on a video/image segment.

    Coordinate space:
        x, y      — normalized; (0, 0) = canvas center, ~[-1, 1] range.
        scale_x/y — multiplier; 1.0 = native, 1.5 = 150% bigger.
        rotation  — degrees, clockwise.
        alpha     — opacity, 0.0 to 1.0.
    Pass only the props you want to change; others keep their current values.
    Look up segment_id via inspect_draft.
    """
    return D.set_clip_transform(
        name=draft, segment_id=segment_id,
        x=x, y=y, scale_x=scale_x, scale_y=scale_y,
        rotation=rotation, alpha=alpha,
        flip_horizontal=flip_horizontal, flip_vertical=flip_vertical,
    )


@mcp.tool()
def set_chroma_key(
    draft: str,
    segment_id: str,
    color: str = "#00d800ff",
    intensity: float = 0.2,
    shadow: float = 0.0,
    edge_smooth: float = 0.0,
    spill: float = 0.0,
) -> dict[str, Any]:
    """Apply CapCut chroma key to a video/image segment.

    Use for green-screen character MP4s. The default color matches the green
    sampled by CapCut from the generated Omar test clip.
    """
    return D.set_chroma_key(
        name=draft, segment_id=segment_id, color=color,
        intensity=intensity, shadow=shadow, edge_smooth=edge_smooth,
        spill=spill,
    )


@mcp.tool()
def set_segment_volume(draft: str, segment_id: str, volume: float) -> dict[str, Any]:
    """Set volume on any segment (audio or video). 1.0 = unchanged, 0.0 = mute."""
    return D.set_segment_volume(name=draft, segment_id=segment_id, volume=volume)


@mcp.tool()
def move_segment(draft: str, segment_id: str, start_seconds: float) -> dict[str, Any]:
    """Move a segment to a new timeline start position."""
    return D.move_segment(name=draft, segment_id=segment_id, start_seconds=start_seconds)


@mcp.tool()
def trim_segment(
    draft: str,
    segment_id: str,
    duration_seconds: float | None = None,
    source_start_seconds: float | None = None,
) -> dict[str, Any]:
    """Change a segment's timeline duration and/or its source-trim offset.

    Pass only the fields you want to change; others are left as-is.
    """
    return D.trim_segment(
        name=draft, segment_id=segment_id,
        duration_seconds=duration_seconds,
        source_start_seconds=source_start_seconds,
    )


@mcp.tool()
def delete_segment(draft: str, segment_id: str) -> dict[str, Any]:
    """Remove a single segment from its track. Auxiliary materials it
    referenced are left in place (CapCut tolerates orphaned aux materials).
    """
    return D.delete_segment(name=draft, segment_id=segment_id)


@mcp.tool()
def clear_track(draft: str, track_type: str, track_index: int = 0) -> dict[str, Any]:
    """Empty out one track (keeps the track itself).

    `track_type` is "video" / "audio" / "text". Use this to iterate captions
    in the same draft: clear_track("text") then re-run add_captions_from_srt
    with different style/font/position.
    """
    return D.clear_track(name=draft, track_type=track_type, track_index=track_index)


@mcp.tool()
def clear_text_tracks(draft: str) -> dict[str, Any]:
    """Empty every text track in the draft. Convenience for re-running
    captions with a different style on the same project.
    """
    return D.clear_text_tracks(name=draft)


# ---- animation -------------------------------------------------------------

@mcp.tool()
def add_keyframe(
    draft: str,
    segment_id: str,
    time_seconds: float,
    property: str,
    value: float,
    curve: str = "Line",
) -> dict[str, Any]:
    """Add a keyframe to animate a segment property over time.

    Args:
        segment_id: from inspect_draft.
        time_seconds: ABSOLUTE timeline time (we convert to segment-relative).
            Must lie within the segment's start..start+duration window.
        property: one of x, y, scale_x, scale_y, rotation, alpha, volume.
        value: target value at this time. Same coordinate space as
            set_clip_transform (x/y normalized, scale multiplier, rotation
            degrees, alpha 0-1, volume 0-1+).
        curve: "Line" for linear, "Bezier" for ease curves.

    Two or more keyframes on the same property animate between them.
    A single keyframe pins the property to that value.
    """
    return D.add_keyframe(
        name=draft, segment_id=segment_id,
        time_seconds=time_seconds,
        property=property, value=value, curve=curve,
    )


@mcp.tool()
def add_keyframes(
    draft: str,
    segment_id: str,
    property: str,
    times_seconds: list[float],
    values: list[float],
    curve: str = "Line",
) -> dict[str, Any]:
    """Batch version of add_keyframe — set multiple keyframes on one
    property in a single call.

    `times_seconds` and `values` must be the same length; each pair becomes
    one keyframe. `property` is one of x, y, scale_x, scale_y, rotation,
    alpha, volume.

    Example — slide-in then exit on x:
        add_keyframes(segment_id=..., property="x",
                      times_seconds=[0.0, 0.5, 2.0, 2.5],
                      values=[1.5, 0.0, 0.0, -1.5])
    """
    return D.add_keyframes(
        name=draft, segment_id=segment_id, property=property,
        times_seconds=times_seconds, values=values, curve=curve,
    )


# ---- text (experimental) ---------------------------------------------------

@mcp.tool()
def add_text(
    draft: str,
    text: str,
    duration_seconds: float,
    start_seconds: float = 0.0,
    font_size: float = 15.0,
    color_hex: str = "#FFFFFF",
    alpha: float = 1.0,
    x: float = 0.0,
    y: float = 0.0,
    scale: float = 1.0,
    rotation: float = 0.0,
    track_index: int = 0,
    language: str | None = None,
    font_path: str | None = None,
    border_color_hex: str | None = None,
    border_width: float = 0.08,
    border_alpha: float = 1.0,
    has_shadow: bool = False,
    shadow_color_hex: str = "#000000",
    shadow_alpha: float = 0.9,
    shadow_distance: float = 5.0,
    background_color_hex: str | None = None,
    background_alpha: float = 0.9,
    highlight_color_hex: str | None = None,
    line_max_width: float = 0.82,
    bold: bool = False,
) -> dict[str, Any]:
    """Add a styled text overlay (titles, captions, lower-thirds).

    Font: pass `language` (en/ar/ja/ko/zh/zh-hant/th/he/bn) to use a CapCut
    system font, OR `font_path` for a specific TTF. Auto-detected from the
    text's script if neither is given.

    For a caption look, pass:
        border_color_hex="#000000" + has_shadow=True + font_size=20 + y=0.55
    For pill-style subtitles:
        background_color_hex="#000000" + background_alpha=0.55
    """
    return D.add_text(
        name=draft, text=text,
        duration_seconds=duration_seconds, start_seconds=start_seconds,
        font_size=font_size, color_hex=color_hex, alpha=alpha,
        x=x, y=y, scale=scale, rotation=rotation,
        track_index=track_index,
        language=language, font_path=font_path,
        border_color_hex=border_color_hex,
        border_width=border_width, border_alpha=border_alpha,
        has_shadow=has_shadow, shadow_color_hex=shadow_color_hex,
        shadow_alpha=shadow_alpha, shadow_distance=shadow_distance,
        background_color_hex=background_color_hex,
        background_alpha=background_alpha,
        highlight_color_hex=highlight_color_hex,
        line_max_width=line_max_width,
        bold=bold,
    )


@mcp.tool()
def add_captions_from_srt(
    draft: str,
    srt_path: str,
    style: str = "youtube",
    time_offset_seconds: float = 0.0,
    max_captions: int | None = None,
    font_size: float = 13.0,
    y: float = 0.42,
    x: float = 0.0,
    scale: float = 1.0,
    track_index: int = 0,
    language: str | None = None,
    line_max_width: float = 0.72,
) -> dict[str, Any]:
    """Bulk-add styled captions to a draft from an SRT file.

    Reads each caption block, places styled text segments at the matching
    timeline range. Font is auto-detected from text script
    (Arabic / Hebrew / CJK / Thai / Latin → CapCutSansText-Bold).

    Static styles (one segment per SRT block):
        - "youtube"  — bold white + thick black outline + shadow [default]
        - "subtitle" — white on translucent dark pill
        - "tiktok"   — bold yellow + outline + shadow
        - "minimal"  — plain white + light shadow only

    Per-word animated styles (N segments per SRT block, one per word, timed
    proportionally to char count within the caption duration):
        - "karaoke"     — full caption visible, current word's fill turns
                          yellow as the audio progresses
        - "karaoke_box" — full caption visible, current word gets a thick
                          yellow stroke that reads as a highlight box
        - "wordbox"     — one word at a time in a yellow pill (no context)

    Defaults are tuned for 1920×1080 lower-third placement
    (y=0.42, font_size=13, line_max_width=0.72). For portrait (1080×1920),
    pass y=0.30 and font_size=16 — captions need more vertical headroom.

    Recipe — captions in 4 lines for an existing draft:
        clear_text_tracks(draft="my-video")
        add_captions_from_srt(
            draft="my-video",
            srt_path="/path/to/whisper-output.srt",
            style="karaoke_box",
        )

    Then close + reopen the draft in CapCut. CapCut caches drafts in memory
    and won't pick up disk changes while open.

    Use `time_offset_seconds` if your video doesn't start at 0 in the
    timeline. Use `max_captions` to test with a handful first.
    """
    return D.add_captions_from_srt(
        name=draft, srt_path=srt_path, style=style,
        time_offset_seconds=time_offset_seconds,
        max_captions=max_captions,
        font_size=font_size, y=y, x=x, scale=scale,
        track_index=track_index, language=language,
        line_max_width=line_max_width,
    )


# ---- system ----------------------------------------------------------------

@mcp.tool()
def remove_time_ranges(
    draft: str,
    starts_seconds: list[float],
    ends_seconds: list[float],
) -> dict[str, Any]:
    """Cut multiple time ranges out of the timeline across every track.

    `starts_seconds` and `ends_seconds` are parallel arrays — each pair
    `(starts_seconds[i], ends_seconds[i])` is one range to remove.
    Overlapping ranges are merged. Segments crossing a cut are split.
    Survivors shift left to close the gaps.

    Use this to trim intros/outros, remove dead air, or splice out a
    section the LLM identified.
    """
    if len(starts_seconds) != len(ends_seconds):
        return {"error": "starts_seconds and ends_seconds must have the same length"}
    ranges = list(zip(starts_seconds, ends_seconds))
    return D.remove_time_ranges(name=draft, ranges_seconds=ranges)


@mcp.tool()
def get_auto_captions(draft: str) -> dict[str, Any]:
    """Read CapCut's auto-generated captions out of a draft.

    Detects text materials with `recognize_task_id` (set by CapCut when the
    user runs "Text → Auto Captions"). Returns timeline-sorted captions
    with per-word timings already converted to absolute seconds.

    Returns `{captions: []}` if the draft has no auto-captions yet.
    """
    captions = D.get_auto_captions(name=draft)
    return {"count": len(captions), "captions": captions}


@mcp.tool()
def smart_cut_draft(
    draft: str,
    silence_threshold_seconds: float = 1.0,
    duplicate_similarity_threshold: float = 0.6,
    cut_silences: bool = True,
    cut_duplicates: bool = True,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Heuristic auto-edit for talking-head drafts.

    Reads CapCut auto-captions and removes:
      * silences (subtitle gaps > `silence_threshold_seconds`)
      * duplicate takes (when the speaker re-recorded a phrase, the
        latest version is kept — earlier attempts are cut)

    Pass `dry_run=True` to preview the cuts without modifying the draft.

    Prerequisite: the draft must have auto-captions. Open it in CapCut,
    run "Text → Auto Captions", save, close, then call this. CapCut
    caches the draft when open, so close+reopen after the cut.
    """
    return D.smart_cut_draft(
        name=draft,
        silence_threshold_seconds=silence_threshold_seconds,
        duplicate_similarity_threshold=duplicate_similarity_threshold,
        cut_silences=cut_silences,
        cut_duplicates=cut_duplicates,
        dry_run=dry_run,
    )


@mcp.tool()
def open_in_capcut(draft: str | None = None) -> dict[str, Any]:
    """Launch the CapCut macOS app. Drafts in the projects folder will appear
    in the Drafts list (you may need to switch tabs to refresh).
    """
    if draft is not None:
        folder = draft_dir(draft)
        if not folder.exists():
            return {"ok": False, "error": f"Draft not found: {folder}"}
    subprocess.Popen(["open", "-a", "CapCut"])
    return {
        "ok": True, "draft": draft,
        "projects_root": str(CAPCUT_PROJECTS_ROOT),
        "hint": "Switch tabs in CapCut Home to refresh the Drafts list.",
    }


def main() -> None:
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
