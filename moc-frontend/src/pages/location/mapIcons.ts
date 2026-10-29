import L from "leaflet";

function svgIcon(color: string, glyph: "pin" | "dot") {
  const html =
    glyph === "pin"
      ? `<svg width="34" height="42" viewBox="0 0 34 42" xmlns="http://www.w3.org/2000/svg">
           <path d="M17 0C7.6 0 0 7.6 0 17c0 12.2 17 25 17 25s17-12.8 17-25C34 7.6 26.4 0 17 0z" fill="${color}"/>
           <circle cx="17" cy="17" r="6.5" fill="white"/>
         </svg>`
      : `<svg width="22" height="22" viewBox="0 0 22 22" xmlns="http://www.w3.org/2000/svg">
           <circle cx="11" cy="11" r="9" fill="${color}" fill-opacity="0.25"/>
           <circle cx="11" cy="11" r="6" fill="${color}" stroke="white" stroke-width="2.5"/>
         </svg>`;

  return L.divIcon({
    html,
    className: "moc-map-marker",
    iconSize: glyph === "pin" ? [34, 42] : [22, 22],
    iconAnchor: glyph === "pin" ? [17, 42] : [11, 11],
  });
}

export const branchIcon = svgIcon("#B85C38", "pin");
export const branchIconActive = svgIcon("#171717", "pin");
export const userIcon = svgIcon("#2563eb", "dot");
