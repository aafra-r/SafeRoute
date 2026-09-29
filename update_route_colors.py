import re

with open('backend/templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace drawRoutePolylines function body to use the 4-tier color system
old_draw = r"const colors = \['#10B981', '#3B82F6', '#94A3B8'\];[\s\n]*const weights = \[6, 5, 4\];[\s\n]*const poly = L\.polyline\(latLngs, \{ color: colors\[idx\] \|\| '#94A3B8', weight: weights\[idx\] \|\| 4, opacity: 0\.88 \}\)\.addTo\(map\);"

new_draw = """
        // Find the safest route index
        const safestIdx = routes.reduce((maxIdx, currentRoute, currentIndex, arr) => 
            (currentRoute.safety_score || 0) > (arr[maxIdx].safety_score || 0) ? currentIndex : maxIdx
        , 0);

        const score = r.safety_score || 0;
        let routeColor = '#EF4444'; // Unsafe
        if (score >= 75) routeColor = '#22C55E'; // Safe
        else if (score >= 50) routeColor = '#FACC15'; // Moderate
        else if (score >= 25) routeColor = '#F97316'; // Risky

        const isSafest = (idx === safestIdx);
        const baseWeight = isSafest ? 7 : 4;
        const opacity = isSafest ? 0.95 : 0.6;
        const dashArray = isSafest ? null : '5, 5'; // Make alternative routes dashed

        const poly = L.polyline(latLngs, { color: routeColor, weight: baseWeight, opacity: opacity, dashArray: dashArray }).addTo(map);
"""

if "Find the safest route index" not in content:
    content = re.sub(old_draw, new_draw, content)

with open('backend/templates/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
