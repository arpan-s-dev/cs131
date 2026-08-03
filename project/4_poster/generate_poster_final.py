"""
Build the FINAL one-page poster (all four phases) as a self-contained HTML
file with the figures embedded. Open it in a browser and File -> Print ->
Save as PDF (landscape) for the submission.

    python cs131/project/4_poster/generate_poster_final.py
"""
import base64, os

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figures")
SHOT = os.path.join(HERE, "..", "2_breaking", "screenshots")


def b64(path):
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()


fig1 = b64(os.path.join(FIG, "fig1_rotation_curve.png"))
fig2 = b64(os.path.join(FIG, "fig2_scaling.png"))
fig3 = b64(os.path.join(FIG, "fig3_sky_map.png"))
pandas_shot = b64(os.path.join(SHOT, "pandas_taskmanger_usage.png"))

html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>CS131 Final Poster - Gaia DR3</title>
<style>
  @page {{ size: 16in 10in; margin: 0; }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; font-family:"Segoe UI",Arial,sans-serif; color:#222; background:#fff;
         width:16in; height:10in; padding:0.3in; line-height:1.3; overflow:hidden; }}
  h1 {{ margin:0; font-size:30px; color:#14213d; }}
  .sub {{ font-size:15px; color:#555; margin-top:3px; }}
  .repo {{ font-size:14px; color:#2b5cb8; }}
  hr {{ border:0; border-top:4px solid #2b5cb8; margin:8px 0 12px; }}
  .cols {{ display:grid; grid-template-columns:1fr 1fr 1.15fr; gap:14px; }}
  .answer {{ display:grid; grid-template-columns:1.5fr 1fr 1.1fr; gap:16px; align-items:center; }}
  .answer img {{ max-height:2.85in; object-fit:contain; }}
  h2 {{ font-size:18px; color:#fff; background:#2b5cb8; margin:0 0 8px; padding:5px 10px; border-radius:4px; }}
  p, li {{ font-size:12.5px; margin:5px 0; }}
  .facts {{ font-size:12px; background:#eef3fb; border:1px solid #cdd9ee; border-radius:5px; padding:7px 9px; }}
  .facts b {{ color:#14213d; }}
  table {{ width:100%; border-collapse:collapse; font-size:11.5px; margin:6px 0; }}
  th,td {{ border:1px solid #ccd3e0; padding:3px 6px; text-align:left; }}
  th {{ background:#dbe4f5; }}
  code {{ font-family:Consolas,monospace; font-size:11px; }}
  img {{ width:100%; border:1px solid #bbb; border-radius:4px; }}
  .note {{ font-size:12px; background:#e6f6ec; border-left:4px solid #1f9d55; padding:6px 9px; border-radius:4px; }}
  .bad {{ color:#b21f1f; font-weight:bold; }} .ok {{ color:#1f9d55; font-weight:bold; }}
  .bottom {{ display:grid; grid-template-columns:1.3fr 1fr; gap:16px; margin-top:12px; }}
  .concl {{ font-size:13.5px; background:#fff7e6; border:1px solid #f0d8a8; border-radius:5px; padding:10px 12px; }}
  .concl b {{ color:#854f0b; }}
</style></head><body>

<h1>The Milky Way's Hidden Mass: Measuring Galactic Rotation with 129 Million Stars</h1>
<div class="sub">Arpanjeet Singh &nbsp;|&nbsp; CS 131 Big Data &nbsp;|&nbsp; Group 17 &nbsp;|&nbsp;
  Dataset: ESA Gaia DR3 (1.8 billion stars) &nbsp;|&nbsp; <span class="repo">github.com/arpan-s-dev/cs131</span></div>
<hr>

<p style="font-size:13px;margin:0 0 10px;"><b>The question:</b> planets far from the Sun orbit slower than near ones.
Do stars far from the Galaxy's centre do the same? If they don't, there must be unseen mass holding them, that is dark matter.
We test this with Gaia DR3, which is far too big for Excel or pandas, so we profile it on the command line, break the in-memory tools, then compute the answer with PySpark on a cluster.</p>

<div class="cols">

  <section>
    <h2>Profiling</h2>
    <div class="facts"><b>Our slice:</b> 242 of 3,386 files (every 28th, all-sky),
      53.7 GB, <b>129,016,649 rows</b>, 152 columns.</div>
    <table>
      <tr><th>Command (streamed, timed)</th><th>Result</th></tr>
      <tr><td><code>du -sh</code></td><td>26 GB (121-file draft)</td></tr>
      <tr><td><code>zcat|grep -v'^#'|wc -l</code></td><td>64.7M rows (draft)</td></tr>
      <tr><td><code>awk</code> mean parallax</td><td>0.943 mas</td></tr>
      <tr><td><code>grep -c VARIABLE</code></td><td>5,345</td></tr>
    </table>
    <div class="note">Memory stayed at a <b>few MB</b> no matter the file size. These tools stream, they never load.</div>
  </section>

  <section>
    <h2>Breaking</h2>
    <p><b>Excel:</b> hangs opening one raw file; hard cap 1,048,576 rows. Full data is <b>~120x</b> that.</p>
    <p><b>pandas:</b> loading the data drove committed memory to <b>29.3 GB</b> on a 15.3 GB laptop:</p>
    <img src="{pandas_shot}" alt="pandas memory blowup">
    <table>
      <tr><th>Mean parallax</th><th>Result</th></tr>
      <tr><td>CLI <code>awk</code> (streams)</td><td class="ok">0.943, done</td></tr>
      <tr><td>pandas (loads)</td><td class="bad">out of memory</td></tr>
    </table>
  </section>

  <section>
    <h2>Scaling</h2>
    <p>Same PySpark job on Dataproc, reading 53.7 GB straight from Google Cloud Storage. Only the machine count changes.</p>
    <img src="{fig2}" alt="scaling chart">
    <table>
      <tr><th>Machines</th><th>Time</th><th>Speed-up</th></tr>
      <tr><td>1</td><td>1471 s</td><td>1.00x</td></tr>
      <tr><td>2</td><td>685 s</td><td>2.15x</td></tr>
      <tr><td>4</td><td>364 s</td><td>4.05x</td></tr>
    </table>
    <div class="note">Near-linear: 242 files = 242 tasks, always more than the cores, so every machine stayed busy.</div>
  </section>

</div>

<h2 style="margin-top:8px;">The Answer: the Milky Way is full of Dark Matter</h2>
<div class="answer">
  <img src="{fig1}" alt="rotation curve">
  <div class="concl">
    <b>The result:</b> from 1.84M quality stars, the orbital speed stays <b>flat at ~215 km/s
    out to 15 kpc</b>. Visible matter alone predicts the red curve, a fall to ~159 km/s. The green
    gap is gravity from mass we cannot see, that is <b>dark matter</b>. Roughly two-thirds of the
    mass inside 15 kpc emits no light.<br><br>
    <b>Validation:</b> with no tuning, the pipeline returns v&#966; = 220.9 km/s at the Sun's
    radius, matching the known value (astropy agrees to 0.06 km/s); inward and vertical motions
    average zero.<br><br>
    <b>Scope:</b> the parallax quality cut keeps nearby stars, so we reach ~15 kpc. The flat trend
    over that range already rejects the visible-matter-only prediction.
  </div>
  <div>
    <img src="{fig3}" alt="sky density map">
    <p style="font-size:10.5px;color:#555;margin:2px 0 0;text-align:center;">
      All-sky stellar density from 129M stars (HEALPix tiles); the same <code>source_id</code>
      bit-shift that maps the sky also serves as our data key.</p>
  </div>
</div>

</body></html>"""

out = os.path.join(HERE, "poster_final.html")
open(out, "w", encoding="utf-8").write(html)
print(f"wrote {out} ({len(html)//1024} KB)")
