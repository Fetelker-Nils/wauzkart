from ..runtime import *
import copy

# 
# Highlight-Recorder
# 
class HighlightRecorder:
    FPS = 30
    RECORD_EVERY = 2
    RECORD_SECONDS = 8 * 60
    HIGHLIGHT_SECONDS = 120
    MAX_FRAMES = RECORD_SECONDS * FPS
    MAX_HIGHLIGHT_FRAMES = HIGHLIGHT_SECONDS * FPS
    HIGHLIGHT_WINDOW = 8 * FPS

    def __init__(self, map_name=None):
        self.frames = []
        self.frame_numbers = []
        self.events = []
        self.map_name = map_name
        self.recording = False
        self.highlight_start = 0
        self.last_event_frame = -999
        self.crash_frames = []
        self.overtake_frames = []
        self.finish_frames = []
        self.close_call_frames = []

    def start(self):
        self.frames = []
        self.frame_numbers = []
        self.events = []
        self.crash_frames = []
        self.overtake_frames = []
        self.finish_frames = []
        self.close_call_frames = []
        self.recording = True

    def record(self, players, frame_idx, world=None):
        if not self.recording: return
        if frame_idx % self.RECORD_EVERY != 0:
            return
        cars = []
        now = time.time()
        for pl in players:
            cars.append((pl.pos[0], pl.pos[1], pl.pos[2],
                         pl.rot, pl.color, pl.crash_timer > now, pl.style, pl.character))
        snap = {"cars": cars, "world": world or {}}
        self.frames.append(snap)
        self.frame_numbers.append(frame_idx)
        if len(self.frames) > self.MAX_FRAMES:
            self.frames.pop(0)
            self.frame_numbers.pop(0)

    def record_explosion(self, pos, frame_idx):
        if not self.recording: return
        self.events.append((frame_idx, 'crash', pos[:]))
        self.crash_frames.append(frame_idx)
        self.last_event_frame = frame_idx

    def record_overtake(self, frame_idx):
        if not self.recording: return
        self.overtake_frames.append(frame_idx)

    def record_finish(self, frame_idx):
        if not self.recording: return
        self.finish_frames.append(frame_idx)

    def record_close_call(self, frame_idx):
        if not self.recording: return
        self.close_call_frames.append(frame_idx)

    def get_highlight(self, best_index=0, last_index=None, map_name=None):
        if not self.frames:
            return [], []
        mode_name = map_name or getattr(self, "map_name", None)
        frames, indices = build_cinematic_highlight(
            self.frames,
            self.frame_numbers,
            crash_frames=self.crash_frames,
            overtake_frames=self.overtake_frames,
            finish_frames=self.finish_frames,
            close_call_frames=self.close_call_frames,
            fps=self.FPS,
            best_index=best_index,
            last_index=last_index,
            map_name=mode_name,
            events=self.events,
        )
        if frames:
            return frames, remap_events(self.events, self.frame_numbers, indices)

        indices = build_highlight_indices(
            len(self.frames),
            self.frame_numbers,
            crash_frames=self.crash_frames,
            overtake_frames=self.overtake_frames,
            finish_frames=self.finish_frames,
            close_call_frames=self.close_call_frames,
            fps=self.FPS,
            max_frames=self.MAX_HIGHLIGHT_FRAMES,
            map_name=mode_name,
            events=self.events,
        )
        final_frames = [self.frames[i] for i in indices]
        return final_frames, remap_events(self.events, self.frame_numbers, indices)


def _frame_cars(frame):
    if isinstance(frame, dict):
        return frame.get("cars", []) or []
    return frame or []


def _clone_frame_with_camera(frame, focus=0, mode="follow", fade=0.0):
    cloned = copy.deepcopy(frame)
    if isinstance(cloned, dict):
        world = cloned.setdefault("world", {})
        cars = cloned.setdefault("cars", [])
    else:
        cars = cloned
        world = {}
        cloned = {"cars": cars, "world": world}
    world["camera"] = {
        "focus": int(max(0, focus)),
        "mode": mode,
        "fade": float(max(0.0, min(1.0, fade))),
    }
    return cloned


def _nearest_car_index_for_pos(frame, pos):
    cars = _frame_cars(frame)
    if not cars or pos is None:
        return 0
    try:
        px, pz = float(pos[0]), float(pos[2])
    except Exception:
        return 0
    best_i = 0
    best_d = float("inf")
    for i, car in enumerate(cars):
        try:
            dx = float(car[0]) - px
            dz = float(car[2]) - pz
        except Exception:
            continue
        d = dx * dx + dz * dz
        if d < best_d:
            best_i = i
            best_d = d
    return best_i


def _fade_for_pos(pos, count, fade_frames, fade_in, fade_out):
    if count <= 0 or fade_frames <= 0:
        return 0.0
    fade = 0.0
    if fade_in:
        fade = max(fade, 1.0 - min(1.0, pos / float(fade_frames)))
    if fade_out:
        fade = max(fade, min(1.0, max(0, pos - (count - fade_frames)) / float(fade_frames)))
    return fade


def _append_cinematic_segment(out_frames, out_indices, frames, indices, focus, mode, fps, fade_in=True, fade_out=True):
    clean_indices = [i for i in indices if 0 <= i < len(frames)]
    if not clean_indices:
        return
    fade_frames = max(6, int(fps * 0.45))
    count = len(clean_indices)
    for pos, idx in enumerate(clean_indices):
        fade = _fade_for_pos(pos, count, fade_frames, fade_in, fade_out)
        out_frames.append(_clone_frame_with_camera(frames[idx], focus=focus, mode=mode, fade=fade))
        out_indices.append(idx)


def _event_frame_numbers(events, event_type):
    found = []
    for event in events or []:
        if isinstance(event, dict):
            if event.get("type") == event_type:
                frame_no = event.get("frame", event.get("frame_idx"))
                if frame_no is not None:
                    found.append(frame_no)
            continue
        try:
            frame_no, typ = event[:2]
        except Exception:
            continue
        if typ == event_type:
            found.append(frame_no)
    return found


def _event_focus_index(events, event_type, default=0):
    for event in events or []:
        if not isinstance(event, dict) or event.get("type") != event_type:
            continue
        for key in ("player", "target", "attacker"):
            try:
                value = event.get(key)
                if value is not None:
                    return int(value)
            except Exception:
                continue
    return default


def _window_indices(center, before, after, total):
    if total <= 0:
        return []
    center = max(0, min(total - 1, int(center)))
    return list(range(max(0, center - before), min(total, center + after + 1)))


def build_cinematic_highlight(frames, frame_numbers=None, *, crash_frames=None, overtake_frames=None,
                              finish_frames=None, close_call_frames=None, fps=30,
                              best_index=0, last_index=None, map_name=None, events=None):
    total = len(frames or [])
    if total <= 0:
        return [], []
    if not frame_numbers or len(frame_numbers) != total:
        frame_numbers = list(range(total))

    cars_count = len(_frame_cars(frames[0]))
    best_index = int(max(0, min(max(0, cars_count - 1), best_index or 0)))
    if last_index is None:
        last_index = max(0, cars_count - 1)
    last_index = int(max(0, min(max(0, cars_count - 1), last_index)))

    out_frames = []
    out_indices = []

    if map_name == "Raeuber & Bulle":
        return build_rb_cinematic_highlight(
            frames,
            frame_numbers,
            crash_frames=crash_frames,
            finish_frames=finish_frames,
            fps=fps,
            best_index=best_index,
            events=events,
        )

    if map_name == "Insignien-Diebstahl":
        return build_insignia_cinematic_highlight(
            frames,
            frame_numbers,
            crash_frames=crash_frames,
            fps=fps,
            best_index=best_index,
            events=events,
        )

    # 1) First 3 seconds from the best player.
    intro_len = min(total, max(1, int(3 * fps)))
    _append_cinematic_segment(out_frames, out_indices, frames, range(0, intro_len), best_index, "follow", fps, fade_in=False, fade_out=True)

    # 2) First crash / abknall highlight.
    crash_source = list(crash_frames or close_call_frames or [])
    if crash_source:
        crash_center = _nearest_recorded_index(frame_numbers, crash_source[0], fps * 4)
        if crash_center is not None:
            focus = best_index
            _append_cinematic_segment(
                out_frames,
                out_indices,
                frames,
                _window_indices(crash_center, int(2.0 * fps), int(3.0 * fps), total),
                focus,
                "follow",
                fps,
                fade_in=True,
                fade_out=True,
            )

    # 3) Catch-up / overtake highlight.
    overtake_source = list(overtake_frames or [])
    if overtake_source:
        center = _nearest_recorded_index(frame_numbers, overtake_source[0], fps * 5)
        if center is not None:
            _append_cinematic_segment(
                out_frames,
                out_indices,
                frames,
                _window_indices(center, int(2.0 * fps), int(3.5 * fps), total),
                best_index,
                "follow",
                fps,
                fade_in=True,
                fade_out=True,
            )

    # 4) Show the last player for 3 seconds.
    first_finish_center = _nearest_recorded_index(frame_numbers, finish_frames[0], fps * 6) if finish_frames else total - 1
    finish_center = first_finish_center
    back_center = max(0, min(total - 1, int(finish_center or total - 1) - int(6 * fps)))
    _append_cinematic_segment(
        out_frames,
        out_indices,
        frames,
        _window_indices(back_center, int(1.5 * fps), int(1.5 * fps), total),
        last_index,
        "follow",
        fps,
        fade_in=True,
        fade_out=True,
    )

    # 5) Final 5 seconds until the finish line, plus 1 second after it.
    final_center = int(first_finish_center or total - 1)
    final_start = max(0, final_center - int(5 * fps))
    final_end = min(total, final_center + int(1 * fps) + 1)
    _append_cinematic_segment(
        out_frames,
        out_indices,
        frames,
        range(final_start, final_end),
        best_index,
        "finish_line",
        fps,
        fade_in=True,
        fade_out=False,
    )

    return out_frames, out_indices


def build_rb_cinematic_highlight(frames, frame_numbers=None, *, crash_frames=None,
                                 finish_frames=None, fps=30, best_index=0, events=None):
    total = len(frames or [])
    if total <= 0:
        return [], []
    if not frame_numbers or len(frame_numbers) != total:
        frame_numbers = list(range(total))

    capture_frames = _event_frame_numbers(events, "rb_capture") or list(crash_frames or [])
    free_frames = _event_frame_numbers(events, "rb_free")
    capture_focus = _event_focus_index(events, "rb_capture", best_index)
    free_focus = _event_focus_index(events, "rb_free", best_index)

    out_frames = []
    out_indices = []

    intro_len = min(total, max(1, int(3.0 * fps)))
    _append_cinematic_segment(out_frames, out_indices, frames, range(0, intro_len), best_index, "wide", fps, fade_in=False, fade_out=True)

    if capture_frames:
        center = _nearest_recorded_index(frame_numbers, capture_frames[0], fps * 5)
        if center is not None:
            _append_cinematic_segment(out_frames, out_indices, frames, _window_indices(center, int(2.0 * fps), int(2.6 * fps), total), capture_focus, "follow", fps, fade_in=True, fade_out=True)

    if free_frames:
        center = _nearest_recorded_index(frame_numbers, free_frames[0], fps * 5)
        if center is not None:
            _append_cinematic_segment(out_frames, out_indices, frames, _window_indices(center, int(1.8 * fps), int(2.8 * fps), total), free_focus, "wide", fps, fade_in=True, fade_out=True)

    last_capture = capture_frames[-1] if capture_frames else None
    if last_capture is not None and (not free_frames or last_capture != capture_frames[0]):
        center = _nearest_recorded_index(frame_numbers, last_capture, fps * 5)
        if center is not None:
            _append_cinematic_segment(out_frames, out_indices, frames, _window_indices(center, int(1.4 * fps), int(2.4 * fps), total), capture_focus, "follow", fps, fade_in=True, fade_out=True)

    final_center = _nearest_recorded_index(frame_numbers, finish_frames[0], fps * 6) if finish_frames else total - 1
    final_center = total - 1 if final_center is None else final_center
    _append_cinematic_segment(out_frames, out_indices, frames, range(max(0, final_center - int(4.0 * fps)), min(total, final_center + int(1.0 * fps) + 1)), best_index, "wide", fps, fade_in=True, fade_out=False)
    return out_frames, out_indices


def build_insignia_cinematic_highlight(frames, frame_numbers=None, *, crash_frames=None,
                                       fps=30, best_index=0, events=None):
    total = len(frames or [])
    if total <= 0:
        return [], []
    if not frame_numbers or len(frame_numbers) != total:
        frame_numbers = list(range(total))

    steal_frames = _event_frame_numbers(events, "insignia_steal")
    steal_focus = _event_focus_index(events, "insignia_steal", best_index)

    out_frames = []
    out_indices = []
    intro_len = min(total, max(1, int(3.0 * fps)))
    _append_cinematic_segment(out_frames, out_indices, frames, range(0, intro_len), best_index, "wide", fps, fade_in=False, fade_out=True)

    for pos, frame_no in enumerate(steal_frames[:3]):
        center = _nearest_recorded_index(frame_numbers, frame_no, fps * 5)
        if center is None:
            continue
        mode = "follow" if pos % 2 == 0 else "wide"
        _append_cinematic_segment(out_frames, out_indices, frames, _window_indices(center, int(1.6 * fps), int(2.6 * fps), total), steal_focus, mode, fps, fade_in=True, fade_out=True)

    if crash_frames:
        center = _nearest_recorded_index(frame_numbers, crash_frames[0], fps * 5)
        if center is not None:
            _append_cinematic_segment(out_frames, out_indices, frames, _window_indices(center, int(1.4 * fps), int(2.2 * fps), total), best_index, "follow", fps, fade_in=True, fade_out=True)

    final_start = max(0, total - int(5.0 * fps))
    _append_cinematic_segment(out_frames, out_indices, frames, range(final_start, total), best_index, "wide", fps, fade_in=True, fade_out=False)
    return out_frames, out_indices


def _nearest_recorded_index(frame_numbers, frame_no, max_distance=None):
    if not frame_numbers:
        return None
    lo, hi = 0, len(frame_numbers) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if frame_numbers[mid] < frame_no:
            lo = mid + 1
        else:
            hi = mid
    best = lo
    if lo > 0 and abs(frame_numbers[lo - 1] - frame_no) <= abs(frame_numbers[lo] - frame_no):
        best = lo - 1
    if max_distance is not None and abs(frame_numbers[best] - frame_no) > max_distance:
        return None
    return best


def _add_window(out, center, before, after, total):
    if center is None:
        return
    for i in range(max(0, center - before), min(total, center + after + 1)):
        out.add(i)


def _spread_indices(total, count):
    if total <= 0 or count <= 0:
        return []
    if count == 1:
        return [total // 2]
    return [max(0, min(total - 1, int(round((total - 1) * i / (count - 1))))) for i in range(count)]


def build_highlight_indices(total, frame_numbers=None, *, crash_frames=None, overtake_frames=None,
                            finish_frames=None, close_call_frames=None, fps=30, max_frames=3600,
                            map_name=None, events=None):
    if total <= 0:
        return []
    if not frame_numbers or len(frame_numbers) != total:
        frame_numbers = list(range(total))
    selected = set()
    max_event_distance = max(2, fps * 3)

    # Always show a little of the race opening so highlights feel like a story, not only the end.
    _add_window(selected, 0, 0, 5 * fps, total)

    for abs_idx in crash_frames or []:
        center = _nearest_recorded_index(frame_numbers, abs_idx, max_event_distance)
        _add_window(selected, center, 5 * fps, 7 * fps, total)
    for abs_idx in overtake_frames or []:
        center = _nearest_recorded_index(frame_numbers, abs_idx, max_event_distance)
        _add_window(selected, center, 4 * fps, 6 * fps, total)
    for abs_idx in close_call_frames or []:
        center = _nearest_recorded_index(frame_numbers, abs_idx, max_event_distance)
        _add_window(selected, center, 3 * fps, 5 * fps, total)
    if map_name == "Raeuber & Bulle":
        for abs_idx in _event_frame_numbers(events, "rb_capture"):
            center = _nearest_recorded_index(frame_numbers, abs_idx, max_event_distance)
            _add_window(selected, center, 4 * fps, 5 * fps, total)
        for abs_idx in _event_frame_numbers(events, "rb_free"):
            center = _nearest_recorded_index(frame_numbers, abs_idx, max_event_distance)
            _add_window(selected, center, 4 * fps, 5 * fps, total)
    elif map_name == "Insignien-Diebstahl":
        for abs_idx in _event_frame_numbers(events, "insignia_steal"):
            center = _nearest_recorded_index(frame_numbers, abs_idx, max_event_distance)
            _add_window(selected, center, 4 * fps, 5 * fps, total)
    for abs_idx in finish_frames or []:
        center = _nearest_recorded_index(frame_numbers, abs_idx, max_event_distance)
        _add_window(selected, center, 8 * fps, 4 * fps, total)

    # Add race-wide samples so longer races are represented even without many events.
    for idx in _spread_indices(total, min(18, max(4, total // (12 * fps)))):
        _add_window(selected, idx, 2 * fps, 2 * fps, total)

    if not selected:
        return list(range(total))

    ordered = sorted(selected)
    if len(ordered) <= max_frames:
        return ordered

    # Compress very long highlight sets evenly while preserving race order.
    compressed = []
    for i in range(max_frames):
        src = int(i * len(ordered) / max_frames)
        compressed.append(ordered[src])
    return compressed


def remap_events(events, frame_numbers, selected_indices):
    if not events or not selected_indices:
        return []
    selected_lookup = {old_idx: new_idx for new_idx, old_idx in enumerate(selected_indices)}
    remapped = []
    max_event_distance = max(2, HighlightRecorder.FPS * 3)
    for event in events:
        if isinstance(event, dict):
            frame_no = event.get("frame", event.get("frame_idx"))
            old_idx = _nearest_recorded_index(frame_numbers, frame_no, max_event_distance) if frame_no is not None else None
            if old_idx in selected_lookup:
                copied = copy.deepcopy(event)
                copied["frame"] = selected_lookup[old_idx]
                remapped.append(copied)
            continue
        try:
            frame_no, typ, pos = event[:3]
        except Exception:
            continue
        old_idx = _nearest_recorded_index(frame_numbers, frame_no, max_event_distance)
        if old_idx in selected_lookup:
            remapped.append((selected_lookup[old_idx], typ, pos))
    return remapped
