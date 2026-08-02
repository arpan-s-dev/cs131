"""
CS 131 - Phase 3: the Milky Way rotation curve, computed with PySpark.

WHAT THIS DOES
  Reads the raw Gaia files, turns each star's measurements into its orbital
  speed v_phi (using the transform verified in prototype_transform.py), and
  averages v_phi in rings of radius R to produce the rotation curve.

WHY SPARK (the professor's question)
  The answer is only ~55 numbers, but PRODUCING it is the big-data work:
    - the quality cuts must be evaluated on every one of the ~130 million rows,
    - the 6-step coordinate transform runs on every surviving row,
  and only then does the tiny average appear. Spark does the SELECTION and the
  TRANSFORM across all rows in parallel. Everything below is native Spark SQL
  (sin/cos/atan2/sqrt as column expressions) - no astropy, and no .toPandas()
  on the big data. Only the final ~55-row result is pulled to the driver.

RUBRIC PIECES USED
  explicit typed columns, filter/transform, groupBy aggregation, a WINDOW
  function, a broadcast JOIN, and .cache().

RUN
  local smoke test : python rotation_curve.py "data/*.csv.gz" out_local
  on Dataproc      : ... rotation_curve.py gs://BUCKET/raw/*.csv.gz gs://BUCKET/out/
"""

import sys
import time
from pyspark.sql import SparkSession, functions as F, Window

# ---------- constants (same as the verified prototype) ----------
R_SUN, Z_SUN, V_CIRC = 8.122, 0.0208, 229.0
U_SUN, V_SUN, W_SUN = 11.1, 12.24, 7.25
K = 4.74047
RA_NGP, DEC_NGP = 192.85948, 27.12825      # galactic north pole, degrees

INPUT = sys.argv[1] if len(sys.argv) > 1 else "data/*.csv.gz"
OUTPUT = sys.argv[2] if len(sys.argv) > 2 else "out_local"

spark = SparkSession.builder.appName("gaia-rotation-curve").getOrCreate()
spark.sparkContext.setLogLevel("WARN")
t0 = time.time()

# ---------- 1. READ ----------
# The files are "enhanced CSV": 1000 '#' comment lines, then a header, then data.
# We read every column as text (no expensive schema inference), then keep and
# cast only the 11 columns we actually use.
raw = (spark.read
       .option("header", True)
       .option("comment", "#")
       .option("nullValue", "null")     # Gaia writes missing values as the text "null"
       .csv(INPUT))

# try_cast returns NULL on any unparseable value instead of crashing the job
df = raw.select(
    F.expr("try_cast(source_id as long)").alias("source_id"),
    *[F.expr(f"try_cast({c} as double)").alias(c) for c in
      ["ra", "dec", "l", "b", "parallax", "parallax_over_error",
       "pmra", "pmdec", "radial_velocity", "ruwe"]],
)

total_rows = df.count()          # forces a full read; also our funnel stage 1

# ---------- all-sky density map (every row, NO cuts) ----------
# source_id's top bits ARE the HEALPix tile number. Shifting right by 47 bits
# gives the level-6 tile (49,152 tiles over the whole sky). Pure big-data
# aggregation touching every row.
skymap = (df.withColumn("hpx6", F.shiftright(F.col("source_id"), 47))
            .groupBy("hpx6").agg(F.count("*").alias("n_stars"),
                                 F.avg("parallax").alias("avg_parallax")))

# ---------- 2. QUALITY CUTS (the sample is created here) ----------
good = df.filter(
    (F.col("parallax") > 0)
    & (F.col("parallax_over_error") > 5)     # distance good to ~20%
    & (F.col("ruwe") < 1.4)                   # clean astrometry
    & F.col("radial_velocity").isNotNull()    # need all 3 velocity pieces
)

# ---------- 3. THE TRANSFORM (verified formulas, as SQL columns) ----------
ra, dec = F.radians("ra"), F.radians("dec")
l, b = F.radians("l"), F.radians("b")
ra_g, dec_g = F.radians(F.lit(RA_NGP)), F.radians(F.lit(DEC_NGP))
d = 1.0 / F.col("parallax")                                   # distance (kpc)

# step 2: rotate proper motion equatorial -> galactic (per-star angle phi)
sin_phi = F.cos(dec_g) * F.sin(ra - ra_g) / F.cos(b)
cos_phi = (F.sin(dec_g) - F.sin(dec) * F.sin(b)) / (F.cos(dec) * F.cos(b))
pm_l = cos_phi * F.col("pmra") + sin_phi * F.col("pmdec")
pm_b = -sin_phi * F.col("pmra") + cos_phi * F.col("pmdec")

# step 3: angular motion -> km/s
v_l = K * pm_l * d
v_b = K * pm_b * d
vr = F.col("radial_velocity")

# step 4: heliocentric galactic velocity (U toward centre, V spin, W up)
U = vr * F.cos(b) * F.cos(l) - v_l * F.sin(l) - v_b * F.sin(b) * F.cos(l)
V = vr * F.cos(b) * F.sin(l) + v_l * F.cos(l) - v_b * F.sin(b) * F.sin(l)
W = vr * F.sin(b) + v_b * F.cos(b)

# step 5: shift to galactic centre + add the Sun's motion
x = d * F.cos(b) * F.cos(l) - R_SUN
y = d * F.cos(b) * F.sin(l)
vx = U + U_SUN
vy = V + V_SUN + V_CIRC
vz = W + W_SUN
R = F.sqrt(x * x + y * y)

# step 6: cylindrical decomposition
stars = good.select(
    R.alias("R"),
    (F.abs((x * vy - y * vx) / R)).alias("v_phi"),   # rotation speed (|.| = sign is convention)
    ((x * vx + y * vy) / R).alias("v_R"),            # inward/outward, should be ~0
    vz.alias("v_z"),                                  # vertical, should be ~0
).filter((F.col("R") > 4) & (F.col("R") < 16))

stars = stars.withColumn("Rbin", (F.floor(F.col("R") / 0.5) * 0.5))
stars.cache()                                        # reused by every step below
usable = stars.count()

# ---------- 4. THE ROTATION CURVE (groupBy aggregation) ----------
curve = (stars.groupBy("Rbin").agg(
            F.expr("percentile_approx(v_phi, 0.5)").alias("v_phi_median"),
            F.count("*").alias("n"),
            F.stddev("v_phi").alias("v_phi_scatter"))
         .orderBy("Rbin"))

# ---------- 5. WINDOW FUNCTION: each star's residual from its bin's mean ----------
w = Window.partitionBy("Rbin")
resid = stars.withColumn("bin_mean", F.avg("v_phi").over(w)) \
             .withColumn("residual", F.col("v_phi") - F.col("bin_mean"))

# ---------- 6. BROADCAST JOIN: velocity dispersion sigma(R) per bin ----------
# join the small curve table back onto the star table, then measure spread
sigma = (resid.join(F.broadcast(curve.select("Rbin", "v_phi_median")), "Rbin")
              .withColumn("dev", F.col("v_phi") - F.col("v_phi_median"))
              .groupBy("Rbin").agg(F.stddev("dev").alias("sigma_vphi"))
              .orderBy("Rbin"))

# ---------- 7. SUN CHECK (validation) ----------
sun = stars.filter((F.col("R") > 7.5) & (F.col("R") < 8.5)) \
           .agg(F.expr("percentile_approx(v_phi, 0.5)").alias("v_phi"),
                F.expr("percentile_approx(v_R, 0.5)").alias("v_R"),
                F.expr("percentile_approx(v_z, 0.5)").alias("v_z")).collect()[0]

elapsed = time.time() - t0

# ---------- REPORT ----------
print("\n" + "=" * 60)
print(f"  raw rows read ......... {total_rows:,}")
print(f"  usable after cuts ..... {usable:,}")
print(f"  SUN CHECK  v_phi = {sun['v_phi']:.1f} km/s (expect ~220-229),"
      f"  v_R = {sun['v_R']:.1f},  v_z = {sun['v_z']:.1f}")
print(f"  wall-clock ............ {elapsed:.1f} s")
print("=" * 60)
print("  ROTATION CURVE:")
for r in curve.collect():
    print(f"    R = {r['Rbin']:5.1f} kpc   v_phi = {r['v_phi_median']:6.1f} km/s   ({r['n']:,} stars)")

# ---------- WRITE the small results ----------
def save(sdf, name):
    if OUTPUT.startswith("gs://"):
        sdf.coalesce(1).write.mode("overwrite").option("header", True).csv(OUTPUT + "/" + name)
    else:                                    # local: tiny result, pandas is fine here
        import os
        os.makedirs(OUTPUT, exist_ok=True)
        sdf.toPandas().to_csv(os.path.join(OUTPUT, name + ".csv"), index=False)

save(curve, "rotation_curve")
save(sigma, "velocity_dispersion")
save(skymap, "sky_density")
print(f"\n  results written to {OUTPUT}")
spark.stop()
