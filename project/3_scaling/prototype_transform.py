"""
Phase 3, Step 0 - verify the physics locally BEFORE paying for a cluster.

We turn each star's raw Gaia measurements into v_phi (its orbital speed
around the Galaxy). We do it two ways and check they agree:

  (A) BY HAND  - the exact formulas we will put into the Spark job
                 (plain arithmetic: sin, cos, atan2, sqrt).
  (B) astropy  - a trusted astronomy library, used here only as a
                 ground-truth check. The real Spark job will NOT use it.

The test that matters (the "Sun check"): stars near the Sun's radius
(R = 8.122 kpc) must come out at v_phi = ~229 km/s, the Sun's own known
orbital speed, which we never tell the pipeline. If that holds and
v_R, v_z average ~0, the whole transform is correct.

Run:  python cs131/project/3_scaling/prototype_transform.py
"""

import glob
import numpy as np
import pandas as pd

# ---------- constants (cited on the poster) ----------
R_SUN = 8.122          # kpc   Sun -> Galactic centre distance   (GRAVITY 2018)
Z_SUN = 0.0208         # kpc   Sun's height above the disk plane  (Bennett & Bovy 2019)
V_CIRC = 229.0         # km/s  circular speed at the Sun          (Eilers+ 2019)
U_SUN, V_SUN, W_SUN = 11.1, 12.24, 7.25   # km/s  Sun's peculiar motion (Schonrich+ 2010)
K = 4.74047            # converts (mas/yr) x (kpc) into km/s

# Galactic north pole in ICRS coordinates (defines the equatorial->galactic tilt)
RA_NGP = np.radians(192.85948)
DEC_NGP = np.radians(27.12825)

# ---------- load a few local files (Set A is already downloaded) ----------
files = sorted(glob.glob("data/*.csv.gz"))[:3]
cols = ["ra", "dec", "l", "b", "parallax", "parallax_over_error",
        "pmra", "pmdec", "radial_velocity", "ruwe"]
print(f"Reading {len(files)} files...")
df = pd.concat(
    (pd.read_csv(f, comment="#", usecols=cols, low_memory=False) for f in files),
    ignore_index=True,
)
print(f"  {len(df):,} rows read")

# ---------- quality cuts (this is where the sample shrinks) ----------
good = (
    (df.parallax > 0)
    & (df.parallax_over_error > 5)      # distance good to ~20%
    & (df.ruwe < 1.4)                    # clean astrometry (rejects binaries)
    & df.radial_velocity.notna()         # need all 3 velocity pieces
)
df = df[good].copy()
print(f"  {len(df):,} rows pass quality cuts")

# ================================================================
#  (A) BY-HAND transform  (the formulas that go into Spark SQL)
# ================================================================
ra = np.radians(df.ra.values)
dec = np.radians(df.dec.values)
l = np.radians(df.l.values)
b = np.radians(df.b.values)
d = 1.0 / df.parallax.values                       # step 1: distance (kpc)
vr = df.radial_velocity.values
pmra = df.pmra.values                              # already includes cos(dec)
pmdec = df.pmdec.values

# step 2: rotate proper motion from equatorial into galactic (angle phi per star)
sin_phi = np.cos(DEC_NGP) * np.sin(ra - RA_NGP) / np.cos(b)
cos_phi = (np.sin(DEC_NGP) - np.sin(dec) * np.sin(b)) / (np.cos(dec) * np.cos(b))
pm_l = cos_phi * pmra + sin_phi * pmdec            # pm in galactic longitude
pm_b = -sin_phi * pmra + cos_phi * pmdec           # pm in galactic latitude

# step 3: angular motion -> real sky speed (km/s)
v_l = K * pm_l * d
v_b = K * pm_b * d

# step 4: assemble heliocentric galactic velocity (U toward centre, V toward
# rotation, W toward north pole)
U = vr * np.cos(b) * np.cos(l) - v_l * np.sin(l) - v_b * np.sin(b) * np.cos(l)
V = vr * np.cos(b) * np.sin(l) + v_l * np.cos(l) - v_b * np.sin(b) * np.sin(l)
W = vr * np.sin(b) + v_b * np.cos(b)

# heliocentric position
xh = d * np.cos(b) * np.cos(l)
yh = d * np.cos(b) * np.sin(l)
zh = d * np.sin(b)

# step 5: shift origin to the Galactic centre and add the Sun's own motion
x = xh - R_SUN
y = yh
z = zh + Z_SUN
vx = U + U_SUN
vy = V + V_SUN + V_CIRC
vz = W + W_SUN

# step 6: cylindrical decomposition -> v_R (in/out) and v_phi (rotation)
R = np.sqrt(x * x + y * y)
v_R = (x * vx + y * vy) / R
v_phi = (x * vy - y * vx) / R
v_z = vz

df["R"] = R
df["v_phi_hand"] = v_phi
df["v_R_hand"] = v_R
df["v_z_hand"] = v_z

# ================================================================
#  (B) astropy ground-truth check (same constants)
# ================================================================
try:
    import astropy.units as u
    from astropy.coordinates import ICRS, Galactocentric, CartesianDifferential

    gc = Galactocentric(
        galcen_distance=R_SUN * u.kpc,
        z_sun=Z_SUN * 1000 * u.pc,
        galcen_v_sun=CartesianDifferential(
            [U_SUN, V_SUN + V_CIRC, W_SUN] * (u.km / u.s)),
    )
    c = ICRS(
        ra=df.ra.values * u.deg, dec=df.dec.values * u.deg,
        distance=(1.0 / df.parallax.values) * u.kpc,
        pm_ra_cosdec=df.pmra.values * (u.mas / u.yr),
        pm_dec=df.pmdec.values * (u.mas / u.yr),
        radial_velocity=df.radial_velocity.values * (u.km / u.s),
    ).transform_to(gc)
    xa, ya = c.x.to(u.kpc).value, c.y.to(u.kpc).value
    vxa = c.v_x.to(u.km / u.s).value
    vya = c.v_y.to(u.km / u.s).value
    Ra = np.sqrt(xa**2 + ya**2)
    df["v_phi_astropy"] = (xa * vya - ya * vxa) / Ra
    have_astropy = True
except Exception as e:
    print(f"  (astropy check skipped: {e})")
    have_astropy = False

# ================================================================
#  THE SUN CHECK
# ================================================================
near_sun = df[(df.R > 7.5) & (df.R < 8.5)]
print("\n================ SUN CHECK (R = 7.5 to 8.5 kpc) ================")
print(f"  stars in the Sun's radius bin : {len(near_sun):,}")
print(f"  median |v_phi| (by hand)      : {near_sun.v_phi_hand.abs().median():7.1f} km/s   (expect ~229)")
if have_astropy:
    print(f"  median |v_phi| (astropy)      : {near_sun.v_phi_astropy.abs().median():7.1f} km/s   (expect ~229)")
    diff = (df.v_phi_hand.abs() - df.v_phi_astropy.abs()).abs()
    print(f"  max |hand - astropy|          : {diff.max():7.2f} km/s   (expect ~0 -> hand formulas correct)")
print(f"  median v_R  (should be ~0)    : {near_sun.v_R_hand.median():7.1f} km/s")
print(f"  median v_z  (should be ~0)    : {near_sun.v_z_hand.median():7.1f} km/s")

# quick preview of the rotation curve
print("\n================ ROTATION CURVE PREVIEW (median |v_phi| per kpc) ================")
df["Rbin"] = df.R.round(0)
curve = df[(df.R > 4) & (df.R < 14)].groupby("Rbin").v_phi_hand.agg(
    lambda s: s.abs().median()).round(1)
counts = df[(df.R > 4) & (df.R < 14)].groupby("Rbin").size()
for rb in curve.index:
    print(f"  R = {rb:4.0f} kpc   v_phi = {curve[rb]:6.1f} km/s   ({counts[rb]:,} stars)")
