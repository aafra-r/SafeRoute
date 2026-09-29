const SAFETY_COLORS_STANDARD = {
  very_safe: { min: 80, max: 100, label: "Very Safe", hex: "#1B9E4B" },
  safe:      { min: 60, max: 79,  label: "Safe",      hex: "#7ACB5A" },
  moderate:  { min: 40, max: 59,  label: "Moderate",  hex: "#F5D33F" },
  risky:     { min: 20, max: 39,  label: "Risky",     hex: "#F28C28" },
  unsafe:    { min: 0,  max: 19,  label: "Unsafe",    hex: "#D62828" },
  nodata:    { label: "Low data confidence", hex: "#9AA0A6" }
};

const SAFETY_COLORS_COLORBLIND = {
  very_safe: { min: 80, max: 100, label: "Very Safe", hex: "#0072B2" },
  safe:      { min: 60, max: 79,  label: "Safe",      hex: "#56B4E9" },
  moderate:  { min: 40, max: 59,  label: "Moderate",  hex: "#E69F00" },
  risky:     { min: 20, max: 39,  label: "Risky",     hex: "#D55E00" },
  unsafe:    { min: 0,  max: 19,  label: "Unsafe",    hex: "#CC79A7" },
  nodata:    { label: "Low data confidence", hex: "#9AA0A6" }
};

let currentColorPalette = SAFETY_COLORS_STANDARD;

function getSafetyColorInfo(score, isLowConfidence = false) {
  if (isLowConfidence || score === null || score === undefined) {
    return currentColorPalette.nodata;
  }
  if (score >= 80) return currentColorPalette.very_safe;
  if (score >= 60) return currentColorPalette.safe;
  if (score >= 40) return currentColorPalette.moderate;
  if (score >= 20) return currentColorPalette.risky;
  return currentColorPalette.unsafe;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { SAFETY_COLORS_STANDARD, SAFETY_COLORS_COLORBLIND, getSafetyColorInfo };
}
