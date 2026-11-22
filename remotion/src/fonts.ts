import { continueRender, delayRender, staticFile } from "remotion";

// Schrift lokal laden (kein Zugriff auf Google Fonts noetig)
if (typeof document !== "undefined") {
  const handle = delayRender("Schriften laden");
  Promise.all(
    [
      ["InterBlack", "assets/fonts/Inter-Black.otf"],
      ["InterExtraBold", "assets/fonts/Inter-ExtraBold.otf"],
    ].map(([name, file]) => new FontFace(name, `url(${staticFile(file)})`).load()),
  )
    .then((faces) => {
      faces.forEach((f) => document.fonts.add(f));
      continueRender(handle);
    })
    .catch(() => continueRender(handle));
}

export const FONT_BLACK = "InterBlack, Inter, Arial Black, sans-serif";
export const FONT_BOLD = "InterExtraBold, Inter, Arial, sans-serif";
