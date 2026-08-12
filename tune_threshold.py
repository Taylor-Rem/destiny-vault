"""tune_threshold.py — record a dismantle, LOOK at the waveform, pick the threshold.

The old way (--audio-test) is a live console meter: by the time you glance at
it the spike is gone, and you can't compare a quiet exotic shatter against the
idle noise floor. This records the speaker loopback (same WASAPI device logic
as auto_dismantle) while you dismantle a few items in-game, then writes an
interactive HTML plot and opens it in your browser:

  - fine 5ms envelope (the shape) + the 30ms chunk peaks the detector actually
    sees, on the same time axis
  - click/drag on the plot to place the threshold line; the event count and
    timestamps update live using auto_dismantle's rising-edge rule
  - the current saved threshold is drawn as a dashed reference line

Record BOTH a normal legendary shatter and an exotic (with its confirm dialog)
— the threshold must clear the QUIETEST real shatter while staying above idle.
When you're done looking, this script prompts for the value and saves it to
dashboard_settings.json, where the dashboard and dismantle_all.py read their
defaults.

    ./venv/Scripts/python.exe tune_threshold.py                # 30s recording
    ./venv/Scripts/python.exe tune_threshold.py --seconds 60
    ./venv/Scripts/python.exe tune_threshold.py --device Speakers

Outputs land in scratch/ (gitignored) as threshold_tuner_<timestamp>.html +
the raw .wav — timestamped, so successive runs (e.g. a legendary shatter vs an
exotic's) never overwrite each other and can be compared side by side.
"""
import argparse
import array
import json
import os
import sys
import time
import wave
import webbrowser

import pyaudiowpatch as pyaudio

from auto_dismantle import find_loopback

HERE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = os.path.join(HERE, "scratch")
SETTINGS_PATH = os.path.join(HERE, "dashboard_settings.json")

FINE_MS = 5      # envelope resolution for the plot (shape)
CHUNK_MS = 30    # what SpeakerMonitor actually measures (detection)


def load_settings():
    try:
        with open(SETTINGS_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_threshold(value):
    s = load_settings()
    s["threshold"] = value
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(s, f, indent=2)
    print("Saved threshold %.4f to %s" % (value, os.path.basename(SETTINGS_PATH)))


def record(seconds, device_query):
    """Record loopback audio; returns (fine_peaks, rate, channels, frames).
    fine_peaks = one normalized peak per FINE_MS window. Ctrl+C stops early
    and keeps what was captured."""
    p = pyaudio.PyAudio()
    dev = find_loopback(p, device_query)
    rate, ch = int(dev["defaultSampleRate"]), dev["maxInputChannels"]
    chunk = int(rate * FINE_MS / 1000.0)
    stream = p.open(format=pyaudio.paInt16, channels=ch, rate=rate,
                    input=True, input_device_index=dev["index"],
                    frames_per_buffer=chunk)
    print("Recording %ds from: %s" % (seconds, dev["name"]))
    print("Go dismantle — include a normal legendary AND an exotic "
          "(its confirm dialog + shatter). Ctrl+C ends the recording early.\n")
    peaks, frames = [], []
    total = int(seconds * 1000 / FINE_MS)
    try:
        for i in range(total):
            data = stream.read(chunk, exception_on_overflow=False)
            frames.append(data)
            samples = array.array("h", data)
            peak = (max(abs(v) for v in samples) / 32768.0) if len(samples) else 0.0
            peaks.append(peak)
            if i % 20 == 0:                       # ~10Hz console meter
                bar = "#" * int(peak * 60)
                left = (total - i) * FINE_MS / 1000.0
                print("\r  %5.1fs left  %.3f %-60s" % (left, peak, bar), end="")
    except KeyboardInterrupt:
        print("\n  stopped early — keeping %.1fs" % (len(peaks) * FINE_MS / 1000.0))
    finally:
        stream.close()
        p.terminate()
    print()
    return peaks, rate, ch, frames


def detector_peaks(fine_peaks):
    """Collapse the fine envelope to CHUNK_MS windows — approximates the 30ms
    chunk peaks SpeakerMonitor computes (window boundaries may differ by a few
    ms from a live run, but the levels are what detection keys off)."""
    n = CHUNK_MS // FINE_MS
    return [max(fine_peaks[i:i + n]) for i in range(0, len(fine_peaks), n)]


def suggest(chunks):
    """Sweep candidate thresholds and count rising-edge events at each (the
    detector's own rule). A shatter's decay tail passes through every level on
    the way down, so there is no simple 'gap' in the values — but tails never
    make a NEW rising edge, so the event count is flat across the whole band
    between the noise ceiling and the quietest spike peak. Suggestion = the
    geometric middle of the widest flat nonzero band (spanning at least 2x).
    Purely advisory — the whole point of the tool is that the human looks."""
    import math
    peak = max(chunks)
    if peak < 0.01:
        return None
    lo, hi = math.log10(0.002), math.log10(peak)
    cands = [10 ** (lo + i * (hi - lo) / 120) for i in range(121)]

    def count(t):
        prev, n = 0.0, 0
        for c in chunks:
            if c >= t and prev < t:
                n += 1
            prev = c
        return n

    counts = [count(t) for t in cands]
    best = None                    # (log-width, geometric middle)
    i = 0
    while i < len(cands):
        j = i
        while j + 1 < len(cands) and counts[j + 1] == counts[i]:
            j += 1
        if counts[i] > 0:
            width = math.log10(cands[j] / cands[i])
            if best is None or width > best[0]:
                best = (width, (cands[i] * cands[j]) ** 0.5)
        i = j + 1
    if best is None or best[0] < math.log10(2):
        return None
    return best[1]


def write_wav(path, frames, rate, ch):
    with wave.open(path, "wb") as w:
        w.setnchannels(ch)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"".join(frames))


HTML = """<!doctype html>
<meta charset="utf-8">
<title>Dismantle threshold tuner</title>
<style>
  body { font: 14px system-ui, sans-serif; background:#14161a; color:#dde;
         margin: 24px; }
  h1 { font-size: 18px; }
  #wrap { position: relative; }
  canvas { background:#1b1e24; border:1px solid #333; border-radius:6px;
           display:block; width:100%%; height:420px; cursor: crosshair; }
  .row { display:flex; gap:24px; align-items:baseline; margin:12px 0;
         flex-wrap:wrap; }
  .big { font-size: 26px; font-weight: 600; color:#7fd4ff; }
  input[type=number] { width: 110px; font-size:16px; background:#22262e;
         color:#dde; border:1px solid #444; border-radius:4px; padding:4px; }
  #events { color:#aab; }
  .hint { color:#889; font-size:13px; }
  kbd { background:#2a2e38; padding:1px 6px; border-radius:4px; }
</style>
<h1>Dismantle threshold tuner &mdash; %(stamp)s</h1>
<div class="row">
  <div>threshold <span class="big" id="thv"></span></div>
  <input type="number" id="thbox" step="0.001" min="0.001" max="1">
  <div>rising-edge events at this threshold: <span class="big" id="evn"></span></div>
</div>
<div id="wrap"><canvas id="c"></canvas></div>
<div class="row hint">
  Click or drag on the plot to set the threshold. Scroll to zoom time,
  drag with <kbd>Shift</kbd> to pan, double-click to reset.
  Blue = 5ms envelope (shape) &middot; orange steps = 30ms detector peaks
  (what auto_dismantle sees) &middot; solid line = your threshold &middot;
  dashed = saved threshold (%(current).3f)%(sugtxt)s.
  Pick a value between the idle noise ceiling and the QUIETEST real shatter.
</div>
<div class="row"><div id="events"></div></div>
<script>
const fine = %(fine)s;          // 5ms peaks
const chunks = %(chunks)s;      // 30ms detector peaks
const FINE_MS = %(fine_ms)d, CHUNK_MS = %(chunk_ms)d;
const saved = %(current)f, suggested = %(suggested)s;
let th = suggested || saved;
let t0 = 0, t1 = fine.length * FINE_MS / 1000;   // visible time window (s)
const dur = t1;
const cv = document.getElementById("c"), thv = document.getElementById("thv"),
      thbox = document.getElementById("thbox"), evn = document.getElementById("evn"),
      evd = document.getElementById("events");
const PAD = {l:56, r:12, t:10, b:26};

function events(t) {
  const out = []; let prev = 0;
  for (let i = 0; i < chunks.length; i++) {
    if (chunks[i] >= t && prev < t) out.push({time: i*CHUNK_MS/1000, peak: chunks[i]});
    prev = chunks[i];
  }
  return out;
}
function yMax() {
  let m = 0;
  for (let i = 0; i < fine.length; i++) {
    const t = i*FINE_MS/1000;
    if (t >= t0 && t <= t1 && fine[i] > m) m = fine[i];
  }
  return Math.max(m * 1.15, th * 1.3, 0.02);
}
function draw() {
  const W = cv.clientWidth, H = cv.clientHeight;
  if (cv.width !== W*devicePixelRatio) { cv.width = W*devicePixelRatio; cv.height = H*devicePixelRatio; }
  const g = cv.getContext("2d");
  g.setTransform(devicePixelRatio,0,0,devicePixelRatio,0,0);
  g.clearRect(0,0,W,H);
  const ym = yMax();
  const px = t => PAD.l + (t - t0) / (t1 - t0) * (W - PAD.l - PAD.r);
  const py = v => H - PAD.b - (v / ym) * (H - PAD.t - PAD.b);
  // grid + axes
  g.strokeStyle = "#2a2e36"; g.fillStyle = "#778"; g.font = "11px system-ui";
  g.textAlign = "right";
  for (let i = 0; i <= 5; i++) {
    const v = ym * i / 5, y = py(v);
    g.beginPath(); g.moveTo(PAD.l, y); g.lineTo(W-PAD.r, y); g.stroke();
    g.fillText(v.toFixed(3), PAD.l-6, y+4);
  }
  g.textAlign = "center";
  const step = (t1-t0) > 20 ? 5 : ((t1-t0) > 6 ? 1 : 0.5);
  for (let t = Math.ceil(t0/step)*step; t <= t1; t += step) {
    const x = px(t);
    g.beginPath(); g.moveTo(x, PAD.t); g.lineTo(x, H-PAD.b); g.stroke();
    g.fillText(t.toFixed(step<1?1:0)+"s", x, H-8);
  }
  // fine envelope (filled)
  g.beginPath(); g.moveTo(px(t0), py(0));
  for (let i = 0; i < fine.length; i++) {
    const t = i*FINE_MS/1000;
    if (t < t0 - 0.1 || t > t1 + 0.1) continue;
    g.lineTo(px(t), py(fine[i]));
  }
  g.lineTo(px(t1), py(0)); g.closePath();
  g.fillStyle = "rgba(90,150,255,0.35)"; g.fill();
  // detector chunk peaks (step line)
  g.beginPath();
  for (let i = 0; i < chunks.length; i++) {
    const ta = i*CHUNK_MS/1000, tb = ta + CHUNK_MS/1000;
    if (tb < t0 || ta > t1) continue;
    g.moveTo(px(ta), py(chunks[i])); g.lineTo(px(tb), py(chunks[i]));
  }
  g.strokeStyle = "#ffb14e"; g.lineWidth = 2; g.stroke(); g.lineWidth = 1;
  // saved threshold (dashed)
  g.setLineDash([6,4]); g.strokeStyle = "#8f8";
  g.beginPath(); g.moveTo(PAD.l, py(saved)); g.lineTo(W-PAD.r, py(saved)); g.stroke();
  g.setLineDash([]);
  // live threshold
  g.strokeStyle = "#7fd4ff"; g.lineWidth = 2;
  g.beginPath(); g.moveTo(PAD.l, py(th)); g.lineTo(W-PAD.r, py(th)); g.stroke();
  g.lineWidth = 1;
  // event markers
  const ev = events(th);
  g.fillStyle = "#ff5d5d";
  for (const e of ev) {
    if (e.time < t0 || e.time > t1) continue;
    const x = px(e.time + CHUNK_MS/2000);
    g.beginPath(); g.moveTo(x, py(e.peak)-14); g.lineTo(x-5, py(e.peak)-24);
    g.lineTo(x+5, py(e.peak)-24); g.closePath(); g.fill();
  }
  thv.textContent = th.toFixed(3);
  if (document.activeElement !== thbox) thbox.value = th.toFixed(3);
  evn.textContent = ev.length;
  evd.textContent = ev.length
    ? "events: " + ev.map(e => e.time.toFixed(2)+"s (peak "+e.peak.toFixed(3)+")").join("  ·  ")
    : "no chunk crosses this threshold";
}
function setFromMouse(e) {
  const r = cv.getBoundingClientRect();
  const ym = yMax();
  const v = (1 - (e.clientY - r.top - PAD.t) / (cv.clientHeight - PAD.t - PAD.b)) * ym;
  th = Math.min(1, Math.max(0.001, v));
  draw();
}
let dragging = false, panning = false, panX = 0;
cv.addEventListener("mousedown", e => {
  if (e.shiftKey) { panning = true; panX = e.clientX; }
  else { dragging = true; setFromMouse(e); }
});
window.addEventListener("mousemove", e => {
  if (dragging) setFromMouse(e);
  if (panning) {
    const r = cv.getBoundingClientRect();
    const dt = (e.clientX - panX) / (r.width - PAD.l - PAD.r) * (t1 - t0);
    panX = e.clientX;
    const nt0 = Math.max(0, Math.min(t0 - dt, dur - (t1-t0)));
    t1 = nt0 + (t1 - t0); t0 = nt0; draw();
  }
});
window.addEventListener("mouseup", () => { dragging = panning = false; });
cv.addEventListener("wheel", e => {
  e.preventDefault();
  const r = cv.getBoundingClientRect();
  const frac = (e.clientX - r.left - PAD.l) / (r.width - PAD.l - PAD.r);
  const tAt = t0 + frac * (t1 - t0);
  const z = e.deltaY > 0 ? 1.25 : 0.8;
  let span = Math.min(dur, Math.max(0.3, (t1 - t0) * z));
  t0 = Math.max(0, tAt - frac * span);
  t1 = Math.min(dur, t0 + span); t0 = t1 - span;
  draw();
}, {passive: false});
cv.addEventListener("dblclick", () => { t0 = 0; t1 = dur; draw(); });
thbox.addEventListener("input", () => {
  const v = parseFloat(thbox.value);
  if (v > 0 && v <= 1) { th = v; draw(); }
});
new ResizeObserver(draw).observe(cv);
draw();
</script>
"""


def main():
    ap = argparse.ArgumentParser(
        description="Record a dismantle and pick --threshold from the waveform.")
    ap.add_argument("--seconds", type=float, default=30,
                    help="recording length (default 30; Ctrl+C ends early)")
    ap.add_argument("--device", default=None,
                    help="output device to monitor, by name substring "
                         "(default: dashboard_settings.json, else default output)")
    ap.add_argument("--no-open", action="store_true",
                    help="don't auto-open the report in the browser")
    args = ap.parse_args()

    settings = load_settings()
    device = args.device if args.device is not None else settings.get("device")
    current = float(settings.get("threshold", 0.03))

    fine, rate, ch, frames = record(args.seconds, device)
    if not fine:
        sys.exit("Nothing recorded.")
    chunks = detector_peaks(fine)
    sug = suggest(chunks)

    os.makedirs(SCRATCH, exist_ok=True)
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    # timestamped names: comparing runs (legendary vs exotic shatter) needs
    # earlier recordings to survive later ones
    tag = time.strftime("%Y%m%d-%H%M%S")
    wav_path = os.path.join(SCRATCH, "threshold_tuner_%s.wav" % tag)
    html_path = os.path.join(SCRATCH, "threshold_tuner_%s.html" % tag)
    write_wav(wav_path, frames, rate, ch)
    html = HTML % {
        "stamp": stamp,
        "fine": json.dumps([round(v, 4) for v in fine]),
        "chunks": json.dumps([round(v, 4) for v in chunks]),
        "fine_ms": FINE_MS, "chunk_ms": CHUNK_MS,
        "current": current,
        "suggested": ("%.4f" % sug) if sug else "null",
        "sugtxt": (" &middot; auto-suggestion %.3f (pre-loaded)" % sug) if sug else "",
    }
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    idle = sorted(chunks)[int(len(chunks) * 0.5)]
    print("Recorded %.1fs — peak %.3f, median 30ms level %.3f."
          % (len(fine) * FINE_MS / 1000.0, max(chunks), idle))
    if sug:
        print("Auto-suggestion: %.4f (largest quiet/loud gap; verify on the plot" % sug
              + " — it can't tell a shatter from a Discord ping).")
    else:
        print("No clear quiet/loud gap found — was anything dismantled? "
              "Look at the plot before trusting any number.")
    print("Report: %s\nAudio:  %s" % (html_path, wav_path))
    if not args.no_open:
        webbrowser.open("file:///" + html_path.replace("\\", "/"))

    print("\nCurrent saved threshold: %.4f" % current)
    try:
        # strip a BOM too — piped/redirected stdin on Windows can carry one
        raw = input("New threshold to save (blank = keep current): ").strip("﻿ \t\r\n")
    except EOFError:
        raw = ""
    if raw:
        try:
            val = float(raw)
        except ValueError:
            sys.exit("Not a number: %r — nothing saved." % raw)
        if not 0.001 <= val <= 1:
            sys.exit("%.4f is outside 0.001-1 — nothing saved." % val)
        save_threshold(val)
    else:
        print("Kept %.4f." % current)


if __name__ == "__main__":
    main()
