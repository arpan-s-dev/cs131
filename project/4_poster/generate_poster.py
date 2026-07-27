"""
Build a one-page, self-contained HTML poster for the Phase 1 + 2 draft.
Reads the two screenshots and embeds them as base64 so the HTML is a
single portable file. Open the result in a browser and File -> Print ->
Save as PDF (landscape) to get the submission PDF.

    python cs131/project/4_poster/generate_poster.py
"""

import base64
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(HERE, "..", "2_breaking", "screenshots")


def img(name):
    with open(os.path.join(SHOTS, name), "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()


excel = img("excel_fail.png")
pandas_shot = img("pandas_taskmanger_usage.png")

html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>CS 131 Poster - Gaia DR3</title>
<style>
  @page {{ size: 11in 8.5in; margin: 0; }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; font-family: "Segoe UI", Arial, sans-serif; color: #1a1a2e;
    background: #fff; width: 11in; height: 8.5in; padding: 0.35in;
  }}
  header {{
    border-bottom: 4px solid #2b5cb8; padding-bottom: 8px; margin-bottom: 12px;
  }}
  header h1 {{ margin: 0; font-size: 25px; color: #14213d; }}
  header .sub {{ font-size: 13px; color: #444; margin-top: 3px; }}
  header .repo {{ font-size: 12px; color: #2b5cb8; margin-top: 2px; }}
  .cols {{ display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }}
  h2 {{
    font-size: 17px; margin: 0 0 8px; color: #fff; background: #2b5cb8;
    padding: 5px 10px; border-radius: 4px;
  }}
  .facts {{
    font-size: 12px; background: #eef3fb; border: 1px solid #cdd9ee;
    border-radius: 5px; padding: 8px 10px; margin-bottom: 10px; line-height: 1.5;
  }}
  .facts b {{ color: #14213d; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 11px; margin-bottom: 8px; }}
  th, td {{ border: 1px solid #ccd3e0; padding: 4px 6px; text-align: left; }}
  th {{ background: #dbe4f5; }}
  code {{ font-family: Consolas, monospace; font-size: 10.5px; }}
  .callout {{
    font-size: 12px; background: #e6f6ec; border-left: 4px solid #1f9d55;
    padding: 7px 10px; border-radius: 4px; line-height: 1.45;
  }}
  .shot {{ width: 100%; border: 1px solid #999; border-radius: 4px; margin: 4px 0; }}
  .cap {{ font-size: 11px; color: #333; margin: 0 0 10px; line-height: 1.4; }}
  .cap b {{ color: #b21f1f; }}
  .ok {{ color: #1f9d55; font-weight: bold; }}
  .bad {{ color: #b21f1f; font-weight: bold; }}
  footer {{
    margin-top: 12px; font-size: 12.5px; text-align: center; color: #14213d;
    border-top: 2px solid #2b5cb8; padding-top: 8px; font-weight: 600;
  }}
</style>
</head>
<body>

<header>
  <h1>The Milky Way's Hidden Mass &mdash; Big Data Profiling of Gaia DR3</h1>
  <div class="sub">Arpanjeet Singh &nbsp;&middot;&nbsp; CS 131 Big Data &nbsp;&middot;&nbsp; Group 17 &nbsp;&middot;&nbsp; Phase 1 + 2 draft</div>
  <div class="repo">github.com/arpan-s-dev/cs131</div>
</header>

<div class="cols">

  <!-- ================= PROFILING ================= -->
  <section>
    <h2>Profiling</h2>
    <div class="facts">
      <b>Dataset:</b> ESA Gaia DR3 <code>gaia_source</code> &mdash; a full-sky
      catalogue of ~1.8 billion stars.<br>
      <b>Our slice:</b> 121 of 3,386 files (every 28th &rarr; even all-sky
      coverage).<br>
      <b>Size:</b> 26 GB compressed (~120 GB uncompressed) &nbsp;|&nbsp;
      <b>Rows:</b> 64,681,399 &nbsp;|&nbsp; <b>Columns:</b> 152
    </div>

    <table>
      <tr><th>Command (timed, streamed)</th><th>Result</th><th>Time</th></tr>
      <tr><td><code>du -sh data/</code></td><td>26 GB on disk</td><td>0.2 s</td></tr>
      <tr><td><code>zcat *.gz | grep -v '^#' | wc -l</code></td><td><b>64,681,399 rows</b></td><td>9 min</td></tr>
      <tr><td><code>... | awk</code> mean(parallax)</td><td>0.9428 mas</td><td>5 s</td></tr>
      <tr><td><code>... | awk | sort | uniq -c</code></td><td>mag peaks at 20</td><td>5 s</td></tr>
      <tr><td><code>... | grep -c VARIABLE</code></td><td>5,345 rows</td><td>5 s</td></tr>
    </table>

    <div class="callout">
      <b>Key result:</b> peak memory stayed at a <b>few MB</b> no matter the
      file size &mdash; even while streaming all 26 GB. These tools read the
      data line by line and never hold it. Requirements met:
      <b>64.7 M rows &gt; 50 M</b> and <b>26 GB &gt; 5 GB</b>.
    </div>
  </section>

  <!-- ================= BREAKING ================= -->
  <section>
    <h2>Breaking</h2>

    <img class="shot" src="{excel}" alt="Excel failing to open the file">
    <p class="cap">
      <b>Excel:</b> hangs opening a single raw file; can't parse the ECSV
      metadata. Hard cap is <b>1,048,576 rows</b> &mdash; the full dataset
      (64.7 M) is <b>61.7&times;</b> over the limit.
    </p>

    <img class="shot" src="{pandas_shot}" alt="Task Manager memory blowup">
    <p class="cap">
      <b>pandas <code>read_csv</code>:</b> loading just ~1/5 of the data drove
      <b>Committed memory to 29.3 / 40.3 GB</b> &mdash; nearly 2&times; the
      machine's 15.3 GB RAM (89% used, 1.7 GB free). Full load projects to
      ~120 GB: <b>impossible on this machine</b>.
    </p>

    <table>
      <tr><th>Same aggregation</th><th>Peak memory</th><th>Outcome</th></tr>
      <tr><td>CLI <code>zcat | awk</code></td><td>a few MB</td><td class="ok">0.9428 mas &#10003;</td></tr>
      <tr><td>pandas <code>read_csv</code></td><td>29.3 GB committed</td><td class="bad">out of memory &#10007;</td></tr>
    </table>
  </section>

</div>

<footer>
  Same machine, same data, same question &mdash; streaming used a few MB and finished;
  loading needed ~2&times; the machine's RAM just to hold one-fifth of the rows. That is the breaking point.
</footer>

</body>
</html>"""

out = os.path.join(HERE, "poster.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print(f"Wrote {out} ({len(html)//1024} KB)")
