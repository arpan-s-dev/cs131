"""
Phase 4 - turn the Spark results into the poster figures.

  fig1_rotation_curve.png   the science answer: flat curve vs Keplerian
  fig2_scaling.png          Phase 3 speed-up: 1, 2, 4 machines
  fig3_sky_map.png          all-sky stellar density (HEALPix level 6)

Run:  python cs131/project/4_poster/make_plots.py
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "3_scaling", "results")
FIG = os.path.join(HERE, "figures")
os.makedirs(FIG, exist_ok=True)

NAVY, RED, GREEN, GREY = "#1a3a6b", "#b21f1f", "#2e8b57", "#888"

# ================================================================
# FIGURE 1 - the rotation curve (the dark-matter result)
# ================================================================
c = pd.read_csv(os.path.join(RES, "rotation_curve.csv")).sort_values("Rbin")
R = c.Rbin.values
v = c.v_phi_median.values
se = c.v_phi_scatter.values / np.sqrt(c.n.values)      # standard error of the median

# Keplerian "visible matter only" prediction, anchored at the Sun (R=8)
i8 = np.argmin(np.abs(R - 8.0))
v_kep = v[i8] * np.sqrt(R[i8] / R)

fig, ax = plt.subplots(figsize=(7, 5))
ax.errorbar(R, v, yerr=se, fmt="o-", color=NAVY, ms=5, lw=2,
            capsize=2, label="Measured (1.84M stars)", zorder=3)
ax.plot(R, v_kep, "--", color=RED, lw=2,
        label="Predicted if only visible matter")
ax.fill_between(R, v_kep, v, color=GREEN, alpha=0.15, label="the 'missing' gravity")
ax.axvline(8.122, color=GREY, ls=":", lw=1)
ax.text(8.25, 120, "Sun", color=GREY, fontsize=9)
ax.set_xlabel("Distance from Galactic centre  R  (kpc)")
ax.set_ylabel("Orbital speed  v$_\\phi$  (km/s)")
ax.set_title("The Milky Way rotation curve is FLAT, not falling")
ax.set_ylim(100, 240)
ax.legend(loc="lower right", fontsize=9)
ax.grid(alpha=0.25)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig1_rotation_curve.png"), dpi=150)
print("wrote fig1_rotation_curve.png")

# ================================================================
# FIGURE 2 - scaling (Phase 3)
# ================================================================
workers = np.array([1, 2, 4])
times = np.array([1471.2, 684.5, 363.5])
speedup = times[0] / times

fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 4))
a1.bar([str(w) for w in workers], times, color=NAVY)
for x, t in zip(range(3), times):
    a1.text(x, t + 20, f"{t:.0f}s", ha="center", fontsize=10)
a1.set_xlabel("Number of machines")
a1.set_ylabel("Job time (seconds)")
a1.set_title("More machines, less time")
a1.set_ylim(0, 1650)

a2.plot(workers, speedup, "o-", color=NAVY, lw=2, ms=7, label="Measured")
a2.plot(workers, workers, "--", color=GREY, label="Ideal (perfect scaling)")
for w, s in zip(workers, speedup):
    a2.text(w, s + 0.15, f"{s:.2f}x", ha="center", fontsize=10, color=NAVY)
a2.set_xlabel("Number of machines")
a2.set_ylabel("Speed-up vs 1 machine")
a2.set_title("Near-perfect linear scaling")
a2.set_xticks(workers)
a2.set_ylim(0, 4.6)
a2.legend(fontsize=9)
a2.grid(alpha=0.25)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig2_scaling.png"), dpi=150)
print("wrote fig2_scaling.png")

# ================================================================
# FIGURE 3 - all-sky stellar density (HEALPix level 6, NESTED)
# ================================================================
try:
    import astropy.units as u
    from astropy_healpix import HEALPix
    from astropy.coordinates import Galactic

    s = pd.read_csv(os.path.join(RES, "sky_density.csv"))
    hp = HEALPix(nside=64, order="nested", frame=Galactic())   # level 6 -> nside 64
    lon, lat = hp.healpix_to_lonlat(s.hpx6.values)
    l = lon.to(u.rad).value
    l = np.where(l > np.pi, l - 2 * np.pi, l)                   # wrap to [-pi, pi]
    b = lat.to(u.rad).value

    fig = plt.figure(figsize=(9, 5))
    ax = fig.add_subplot(111, projection="mollweide")
    sc = ax.scatter(-l, b, c=np.log10(s.n_stars.values), s=6,
                    cmap="inferno", marker="s")
    ax.set_title("Stellar density across our 242-file sample (129M stars)\n"
                 "each square = one 0.9 deg sky tile; densest tiles lie near the Galactic plane",
                 fontsize=10)
    ax.grid(alpha=0.3)
    cb = fig.colorbar(sc, ax=ax, orientation="horizontal", pad=0.07, shrink=0.7)
    cb.set_label("log10(stars per tile)")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig3_sky_map.png"), dpi=150)
    print("wrote fig3_sky_map.png")
except Exception as e:
    print(f"sky map skipped: {e}")

print("done ->", FIG)
