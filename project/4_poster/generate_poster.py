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
    margin: 0; font-family: "Segoe UI", Arial, sans-serif; color: #222;
    background: #fff; width: 11in; height: 8.2in; padding: 0.3in 0.3in 0 0.3in;
    line-height: 1.3; overflow: hidden;
  }}
  h1 {{ margin: 0; font-size: 21px; color: #1a3a6b; }}
  .sub {{ font-size: 12px; color: #555; margin: 2px 0 0; }}
  .repo {{ font-size: 11px; color: #1a3a6b; margin: 1px 0 0; }}
  hr {{ border: 0; border-top: 3px solid #1a3a6b; margin: 6px 0 9px; }}

  h2 {{
    font-size: 15px; color: #1a3a6b; margin: 0 0 5px;
    border-bottom: 2px solid #1a3a6b; padding-bottom: 2px;
  }}
  h3 {{ font-size: 11.5px; margin: 0 0 3px; color: #1a3a6b; }}

  .strip {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 10px; }}
  .box {{ background: #f4f6fa; border: 1px solid #d6ddea; border-radius: 5px; padding: 6px 8px; font-size: 10.5px; }}

  .cols {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}

  .facts {{ font-size: 11px; margin-bottom: 6px; }}
  .facts b {{ color: #1a3a6b; }}

  table {{ width: 100%; border-collapse: collapse; font-size: 10px; margin-bottom: 6px; }}
  th, td {{ border: 1px solid #ccc; padding: 3px 5px; text-align: left; }}
  th {{ background: #eef1f7; }}
  code {{ font-family: Consolas, monospace; font-size: 10px; }}

  .note {{ font-size: 11px; background: #eaf6ee; border-left: 4px solid #2e8b57; padding: 6px 9px; border-radius: 4px; }}
  .shot {{ width: 100%; max-height: 1.45in; object-fit: contain; object-position: left;
           border: 1px solid #999; border-radius: 4px; margin: 2px 0; background: #111; }}
  .cap {{ font-size: 10.5px; color: #333; margin: 0 0 7px; }}
  .cap b {{ color: #a11; }}
  .ok {{ color: #2e8b57; font-weight: bold; }}
  .bad {{ color: #a11; font-weight: bold; }}
  footer {{ margin-top: 8px; font-size: 11.5px; text-align: center; color: #1a3a6b; border-top: 2px solid #1a3a6b; padding-top: 6px; }}
</style>
</head>
<body>

<h1>The Milky Way's Hidden Mass: Profiling Gaia DR3</h1>
<div class="sub">Arpanjeet Singh &nbsp;|&nbsp; CS 131 Big Data &nbsp;|&nbsp; Group 17 &nbsp;|&nbsp; Phases 1 and 2</div>
<div class="repo">github.com/arpan-s-dev/cs131</div>
<hr>

<!-- ABOUT THE DATA: the three things worth explaining -->
<div class="strip">
  <div class="box">
    <h3>How the sky is split (HEALPix)</h3>
    Gaia divides the whole sky into 786,432 tiles using a method called HEALPix
    (Hierarchical Equal Area isoLatitude Pixelization). Every tile covers the same
    amount of sky and has a number. Equal areas keep the star counts fair.
  </div>
  <div class="box">
    <h3>How the files are named</h3>
    Each file holds all the stars in a range of tile numbers, and the file name is
    that range. Example: <code>GaiaSource_000000-003111</code> holds tiles 0 to 3111.
    Files are cut to about the same size (roughly 200 MB), not the same sky area, so
    a crowded file near the Milky Way needs only a few tiles while an empty file needs
    thousands. Either way each file holds about 500,000 stars.
  </div>
  <div class="box">
    <h3>Why we took every 28th file</h3>
    We only need part of the catalogue (over 50 million rows). We chose 121 of the
    3,386 files. We took every 28th file, not the first 121, because files are ordered
    by sky position. The first 121 would all sit in one small patch of sky. Every 28th
    spreads our sample evenly across the whole sky.
  </div>
</div>

<div class="cols">

  <!-- ================= PROFILING ================= -->
  <section>
    <h2>Profiling</h2>
    <div class="facts">
      <b>Dataset:</b> ESA Gaia DR3, a full-sky catalogue of about 1.8 billion stars.<br>
      <b>Our slice:</b> 121 files, 26 GB compressed (about 120 GB uncompressed),
      <b>64,681,399 rows</b>, 152 columns.
    </div>

    <p style="font-size:11.5px; margin:0 0 6px;">
      We measured the data with command-line tools that read it line by line, so
      the file never has to fit in memory. Each command was timed.
    </p>

    <table>
      <tr><th>Command (streamed, timed)</th><th>Result</th><th>Time</th></tr>
      <tr><td><code>du -sh data/</code></td><td>26 GB on disk</td><td>0.2 s</td></tr>
      <tr><td><code>zcat *.gz | grep -v '^#' | wc -l</code></td><td><b>64,681,399 rows</b></td><td>9 min</td></tr>
      <tr><td><code>... | awk</code> average of parallax</td><td>0.9428 mas</td><td>5 s</td></tr>
      <tr><td><code>... | awk | sort | uniq -c</code></td><td>most stars are faint</td><td>5 s</td></tr>
      <tr><td><code>... | grep -c VARIABLE</code></td><td>5,345 rows</td><td>5 s</td></tr>
    </table>

    <div class="note">
      <b>Result:</b> memory stayed at a few MB no matter how big the file was, even
      while reading all 26 GB. The tools stream the data, they never load it. This
      meets both rules: 64.7 million rows is over 50 million, and 26 GB is over 5 GB.
    </div>
  </section>

  <!-- ================= BREAKING ================= -->
  <section>
    <h2>Breaking</h2>

    <img class="shot" src="{excel}" alt="Excel stuck opening the file">
    <p class="cap">
      <b>Excel:</b> gets stuck just opening one raw file. Its limit is 1,048,576 rows.
      Our full data has 64.7 million rows, about <b>62 times more</b> than Excel can hold.
    </p>

    <img class="shot" src="{pandas_shot}" alt="Task Manager memory full">
    <p class="cap">
      <b>pandas:</b> tries to load everything into memory. Loading only one fifth of the
      data pushed memory use to <b>29.3 GB</b>, almost double the 15.3 GB this laptop has
      (89 percent full, 1.7 GB free). Loading all of it would need about 120 GB, which is
      <b>impossible on this laptop</b>.
    </p>

    <table>
      <tr><th>Same task: average of parallax</th><th>Memory used</th><th>Outcome</th></tr>
      <tr><td>Command line (<code>zcat | awk</code>)</td><td>a few MB</td><td class="ok">0.9428 mas, done</td></tr>
      <tr><td>pandas (<code>read_csv</code>)</td><td>29.3 GB</td><td class="bad">ran out of memory</td></tr>
    </table>
  </section>

</div>

<footer>
  Same laptop, same data, same question. Streaming used a few MB and finished.
  Loading needed about twice the laptop's memory just to hold one fifth of the rows. That is the breaking point.
</footer>

</body>
</html>"""

out = os.path.join(HERE, "poster.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print(f"Wrote {out} ({len(html)//1024} KB)")
