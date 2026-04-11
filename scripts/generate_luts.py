"""
Generate 6 .cube LUT files for the DMT Video Editor color grading system.
Each LUT is a 17x17x17 3D LUT in the Iridas .cube format.
"""
import numpy as np
import os

LUT_SIZE = 17
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "luts")


def write_cube(path: str, title: str, data: np.ndarray):
    """Write a 3D LUT in .cube format."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(f"TITLE \"{title}\"\n")
        f.write(f"LUT_3D_SIZE {LUT_SIZE}\n")
        f.write("DOMAIN_MIN 0.0 0.0 0.0\n")
        f.write("DOMAIN_MAX 1.0 1.0 1.0\n\n")
        for b in range(LUT_SIZE):
            for g in range(LUT_SIZE):
                for r in range(LUT_SIZE):
                    ro, go, bo = data[r, g, b]
                    f.write(f"{ro:.6f} {go:.6f} {bo:.6f}\n")


def identity_lut():
    """Create a neutral identity LUT."""
    lut = np.zeros((LUT_SIZE, LUT_SIZE, LUT_SIZE, 3), dtype=np.float64)
    for r in range(LUT_SIZE):
        for g in range(LUT_SIZE):
            for b in range(LUT_SIZE):
                lut[r, g, b] = [r / (LUT_SIZE - 1), g / (LUT_SIZE - 1), b / (LUT_SIZE - 1)]
    return lut


def clamp(arr):
    return np.clip(arr, 0.0, 1.0)


def generate_orange_teal():
    """Orange + Teal: push shadows toward teal, highlights toward orange."""
    lut = identity_lut()
    for r in range(LUT_SIZE):
        for g in range(LUT_SIZE):
            for b in range(LUT_SIZE):
                ri, gi, bi = lut[r, g, b]
                lum = 0.2126 * ri + 0.7152 * gi + 0.0722 * bi
                # Shadows → teal (lower red, boost blue-green)
                shadow_w = max(0.0, 1.0 - lum * 2.5)
                # Highlights → warm orange (boost red, lower blue)
                high_w = max(0.0, lum * 2.0 - 1.0)
                ro = ri - shadow_w * 0.08 + high_w * 0.12
                go = gi + shadow_w * 0.06 - high_w * 0.02
                bo = bi + shadow_w * 0.10 - high_w * 0.10
                lut[r, g, b] = [ro, go, bo]
    return clamp(lut)


def generate_film_noir():
    """Film Noir: high contrast black & white with slight warm tone."""
    lut = identity_lut()
    for r in range(LUT_SIZE):
        for g in range(LUT_SIZE):
            for b in range(LUT_SIZE):
                ri, gi, bi = lut[r, g, b]
                lum = 0.2126 * ri + 0.7152 * gi + 0.0722 * bi
                # S-curve contrast
                lum = lum ** 0.9
                if lum < 0.5:
                    lum = 2.0 * lum * lum
                else:
                    lum = 1.0 - 2.0 * (1.0 - lum) * (1.0 - lum)
                # Slight sepia tint
                ro = lum * 1.05
                go = lum * 0.98
                bo = lum * 0.88
                lut[r, g, b] = [ro, go, bo]
    return clamp(lut)


def generate_faded_film():
    """Faded Film: lifted blacks, muted saturation, slight green cast."""
    lut = identity_lut()
    for r in range(LUT_SIZE):
        for g in range(LUT_SIZE):
            for b in range(LUT_SIZE):
                ri, gi, bi = lut[r, g, b]
                lum = 0.2126 * ri + 0.7152 * gi + 0.0722 * bi
                # Desaturate 40%
                sat = 0.6
                ro = lum + sat * (ri - lum)
                go = lum + sat * (gi - lum)
                bo = lum + sat * (bi - lum)
                # Lift blacks
                lift = 0.06
                ro = ro * 0.92 + lift
                go = go * 0.92 + lift + 0.01  # slight green
                bo = bo * 0.92 + lift
                lut[r, g, b] = [ro, go, bo]
    return clamp(lut)


def generate_warm_vlog():
    """Warm Vlog: golden warm tones, soft contrast, boosted oranges."""
    lut = identity_lut()
    for r in range(LUT_SIZE):
        for g in range(LUT_SIZE):
            for b in range(LUT_SIZE):
                ri, gi, bi = lut[r, g, b]
                # Warm push
                ro = ri * 1.08 + 0.02
                go = gi * 1.02
                bo = bi * 0.88
                # Soft contrast
                ro = 0.5 + (ro - 0.5) * 1.05
                go = 0.5 + (go - 0.5) * 1.02
                bo = 0.5 + (bo - 0.5) * 0.95
                lut[r, g, b] = [ro, go, bo]
    return clamp(lut)


def generate_cold_blue():
    """Cold Blue: desaturated with blue shadow push, cool highlights."""
    lut = identity_lut()
    for r in range(LUT_SIZE):
        for g in range(LUT_SIZE):
            for b in range(LUT_SIZE):
                ri, gi, bi = lut[r, g, b]
                lum = 0.2126 * ri + 0.7152 * gi + 0.0722 * bi
                # Desaturate 25%
                sat = 0.75
                ro = lum + sat * (ri - lum)
                go = lum + sat * (gi - lum)
                bo = lum + sat * (bi - lum)
                # Blue push in shadows
                shadow_w = max(0.0, 1.0 - lum * 2.0)
                ro -= shadow_w * 0.05
                go -= shadow_w * 0.02
                bo += shadow_w * 0.12
                # Cool highlights
                high_w = max(0.0, lum - 0.6)
                ro -= high_w * 0.03
                bo += high_w * 0.05
                lut[r, g, b] = [ro, go, bo]
    return clamp(lut)


def generate_matte_black():
    """Matte Black: crushed, lifted blacks, muted colors, flat look."""
    lut = identity_lut()
    for r in range(LUT_SIZE):
        for g in range(LUT_SIZE):
            for b in range(LUT_SIZE):
                ri, gi, bi = lut[r, g, b]
                lum = 0.2126 * ri + 0.7152 * gi + 0.0722 * bi
                # Desaturate 50%
                sat = 0.5
                ro = lum + sat * (ri - lum)
                go = lum + sat * (gi - lum)
                bo = lum + sat * (bi - lum)
                # Crush + lift blacks heavily
                ro = ro * 0.82 + 0.10
                go = go * 0.82 + 0.10
                bo = bo * 0.82 + 0.10
                # Compress highlights
                ro = min(ro, 0.92)
                go = min(go, 0.92)
                bo = min(bo, 0.92)
                lut[r, g, b] = [ro, go, bo]
    return clamp(lut)


def main():
    generators = [
        ("Orange+Teal", "orange_teal", generate_orange_teal),
        ("Film Noir", "film_noir", generate_film_noir),
        ("Faded Film", "faded_film", generate_faded_film),
        ("Warm Vlog", "warm_vlog", generate_warm_vlog),
        ("Cold Blue", "cold_blue", generate_cold_blue),
        ("Matte Black", "matte_black", generate_matte_black),
    ]
    for title, filename, gen_fn in generators:
        path = os.path.join(OUTPUT_DIR, f"{filename}.cube")
        print(f"Generating {title} -> {path}")
        data = gen_fn()
        write_cube(path, title, data)
    print("Done. 6 LUT files generated.")


if __name__ == "__main__":
    main()
