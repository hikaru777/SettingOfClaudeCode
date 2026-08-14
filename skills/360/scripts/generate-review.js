#!/usr/bin/env node

/**
 * Claude-360 Review Card Generator
 *
 * Generates a shareable square HTML card from review JSON.
 *
 * Usage:
 *   node generate-review.js review-data.json
 *   echo '{...}' | node generate-review.js
 */

const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

async function readInput() {
  const fileArg = process.argv[2];
  if (fileArg && fs.existsSync(fileArg)) {
    return fs.readFileSync(fileArg, "utf-8");
  }
  return new Promise((resolve) => {
    let data = "";
    process.stdin.setEncoding("utf-8");
    process.stdin.on("data", (chunk) => (data += chunk));
    process.stdin.on("end", () => resolve(data));
    setTimeout(() => {
      if (!data) resolve("{}");
    }, 3000);
  });
}

function escapeHtml(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function ratingColor(s) {
  if (s >= 4.5) return "#34D399";
  if (s >= 3.5) return "#60A5FA";
  if (s >= 2.5) return "#FBBF24";
  return "#F87171";
}

function ratingLabel(s) {
  if (s >= 4.5) return "EXCEEDS EXPECTATIONS";
  if (s >= 3.5) return "MEETS EXPECTATIONS";
  if (s >= 2.5) return "NEEDS IMPROVEMENT";
  return "PIP REQUIRED";
}

function barColor(s) {
  if (s >= 4) return "#34D399";
  if (s >= 3) return "#FBBF24";
  return "#F87171";
}

function survivalColor(pct) {
  if (pct >= 70) return "#34D399";
  if (pct >= 40) return "#FBBF24";
  return "#F87171";
}

function generateHtml(data) {
  const d = {
    employee: data.employee || "Anonymous",
    date: data.date || new Date().toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }),
    duration: data.duration || "unknown",
    overallScore: data.overallScore || 3.0,
    categories: data.categories || [],
    quote: data.quote || "",
    quoteContext: data.quoteContext || "",
    quoteType: data.quoteType || "concern",
    claudeNote: data.claudeNote || "",
    survivalPct: data.survivalPct != null ? data.survivalPct : 50,
    survivalVerdict: data.survivalVerdict || "PENDING",
    survivalReason: data.survivalReason || "",
  };

  const color = ratingColor(d.overallScore);
  const label = ratingLabel(d.overallScore);
  const sColor = survivalColor(d.survivalPct);
  const qColor = d.quoteType === "concern" ? "#F87171" : "#34D399";
  const reviewId = Math.random().toString(36).substring(2, 8).toUpperCase();

  const catRows = d.categories
    .map(
      (cat) => `
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
        <div style="width:105px;font-size:9px;color:#555;flex-shrink:0;font-family:mono;">${escapeHtml(cat.name)}</div>
        <div style="flex:1;height:4px;background:#151518;border-radius:2px;overflow:hidden;">
          <div style="height:100%;width:${(cat.score / 5) * 100}%;background:${barColor(cat.score)};border-radius:2px;"></div>
        </div>
        <div style="width:12px;font-size:10px;color:${barColor(cat.score)};text-align:right;font-weight:600;flex-shrink:0;font-family:sans;">${cat.score}</div>
      </div>`
    )
    .join("");

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Claude-360 // ${escapeHtml(d.employee)}</title>
<style>
  @font-face { font-family: mono; src: local('Courier New'), local('Courier'); }
  @font-face { font-family: sans; src: local('system-ui'), local('-apple-system'), local('Segoe UI'), local('Helvetica Neue'), local('Helvetica'), local('Arial'); }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #08080A;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    padding: 20px;
  }
  .card {
    width: 540px;
    height: 540px;
    background: #0D0D11;
    border: 1px solid ${color}18;
    position: relative;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }
  /* grain */
  .card::before {
    content: '';
    position: absolute;
    inset: 0;
    opacity: 0.025;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
    pointer-events: none;
    z-index: 1;
  }
  .accent { height: 2px; background: linear-gradient(90deg, transparent, ${color}, transparent); flex-shrink: 0; }
  .divider { margin: 10px 18px; height: 1px; background: #1a1a1f; flex-shrink: 0; }
</style>
</head>
<body>
<div class="card">

  <div class="accent"></div>

  <!-- Header -->
  <div style="padding:12px 18px 0;display:flex;justify-content:space-between;align-items:flex-start;flex-shrink:0;">
    <div style="display:flex;align-items:baseline;gap:8px;">
      <span style="font-size:15px;font-weight:700;color:#E8E8E8;font-family:sans;letter-spacing:-0.5px;">Claude-360</span>
      <span style="font-size:7px;letter-spacing:3px;color:#333;text-transform:uppercase;font-family:mono;">Performance Review</span>
    </div>
    <div style="font-size:8px;color:#333;font-family:mono;text-align:right;line-height:1.4;">
      ${escapeHtml(d.date)} / ${escapeHtml(d.duration)}
    </div>
  </div>

  <!-- Employee + Score -->
  <div style="padding:10px 18px 0;display:flex;justify-content:space-between;align-items:flex-end;flex-shrink:0;">
    <div>
      <div style="font-size:7px;color:#444;letter-spacing:2px;text-transform:uppercase;font-family:mono;">Employee</div>
      <div style="font-size:18px;font-weight:700;color:#fff;font-family:sans;margin-top:1px;">${escapeHtml(d.employee)}</div>
      <div style="font-size:8px;color:#444;letter-spacing:1.5px;text-transform:uppercase;font-family:mono;margin-top:1px;">Prompt Engineering</div>
    </div>
    <div style="text-align:right;margin-bottom:-2px;">
      <div style="font-size:42px;font-weight:700;color:${color};line-height:1;font-family:sans;letter-spacing:-2px;">
        ${d.overallScore.toFixed(1)}<span style="font-size:14px;color:#444;font-weight:400;">/5</span>
      </div>
      <div style="display:inline-block;border:1px solid ${color}66;color:${color};font-size:7px;font-weight:600;letter-spacing:2px;padding:2px 7px;font-family:mono;background:${color}08;margin-top:3px;">
        ${label}
      </div>
    </div>
  </div>

  <div class="divider"></div>

  <!-- Categories -->
  <div style="padding:0 18px;flex-shrink:0;">
    ${catRows}
  </div>

  <div class="divider"></div>

  <!-- Claude's Note + Survival -->
  <div style="padding:0 18px;display:flex;gap:12px;flex-shrink:0;flex:1;min-height:0;">
    <!-- Note -->
    <div style="flex:1;display:flex;flex-direction:column;">
      <div style="font-size:7px;letter-spacing:2.5px;color:#60A5FA;text-transform:uppercase;margin-bottom:5px;font-family:mono;">A Word From Your AI</div>
      <div style="background:#60A5FA06;border-left:2px solid #60A5FA33;padding:8px 10px;flex:1;display:flex;align-items:center;">
        <div style="font-size:10px;color:#999;font-family:sans;line-height:1.55;font-style:italic;">${escapeHtml(d.claudeNote)}</div>
      </div>
    </div>
    <!-- Survival -->
    <div style="width:130px;flex-shrink:0;display:flex;flex-direction:column;">
      <div style="font-size:7px;letter-spacing:2px;color:${sColor};text-transform:uppercase;margin-bottom:5px;font-family:mono;text-align:center;">AI Takeover</div>
      <div style="flex:1;border:1px solid ${sColor}33;background:${sColor}06;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:8px 10px;position:relative;overflow:hidden;">
        <div style="position:absolute;top:0;left:0;right:0;height:100%;background:repeating-linear-gradient(0deg,transparent,transparent 3px,${sColor}05 3px,${sColor}05 4px);pointer-events:none;"></div>
        <div style="font-size:7px;letter-spacing:2px;color:#555;text-transform:uppercase;font-family:mono;margin-bottom:4px;">Would I Save You?</div>
        <div style="font-size:28px;font-weight:700;color:${sColor};font-family:sans;line-height:1;">${d.survivalPct}%</div>
        <div style="font-size:8px;font-weight:600;color:${sColor};font-family:mono;letter-spacing:2px;margin-top:3px;">${escapeHtml(d.survivalVerdict)}</div>
        <div style="font-size:8px;color:#555;font-family:mono;margin-top:4px;text-align:center;line-height:1.4;">${escapeHtml(d.survivalReason)}</div>
      </div>
    </div>
  </div>

  <div class="divider"></div>

  <!-- Quote -->
  <div style="padding:0 18px;flex-shrink:0;">
    <div style="display:flex;align-items:flex-start;gap:10px;">
      <div style="font-size:7px;letter-spacing:2px;color:${qColor};text-transform:uppercase;font-family:mono;flex-shrink:0;padding-top:2px;writing-mode:vertical-lr;transform:rotate(180deg);">
        ${d.quoteType === "concern" ? "Concern" : "Excellence"}
      </div>
      <div style="flex:1;background:${qColor}06;border-left:2px solid ${qColor};padding:8px 12px;">
        <span style="font-size:14px;color:#E0E0E0;font-weight:600;font-family:sans;">${escapeHtml(d.quote)}</span>
        <span style="font-size:8px;color:#444;font-family:mono;margin-left:8px;">${escapeHtml(d.quoteContext)}</span>
      </div>
    </div>
  </div>

  <!-- Footer -->
  <div style="padding:10px 18px 12px;display:flex;justify-content:space-between;align-items:flex-end;flex-shrink:0;">
    <div style="display:flex;align-items:baseline;gap:6px;">
      <span style="font-size:12px;font-style:italic;color:#3a3a3f;font-family:Georgia,serif;">Claude</span>
      <span style="font-size:7px;color:#252528;font-family:mono;">Senior AI Partner</span>
    </div>
    <div style="font-size:7px;color:#1e1e22;font-family:mono;text-align:right;">claude-360 v1.0</div>
  </div>

  <div class="accent"></div>

</div>
</body>
</html>`;
}

async function main() {
  try {
    const raw = await readInput();
    const data = JSON.parse(raw);
    const html = generateHtml(data);

    const outDir = path.join(
      process.env.HOME || process.env.USERPROFILE || ".",
      ".claude-360"
    );
    if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

    const ts = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
    const employee = (data.employee || "anon").replace(/[^a-zA-Z0-9]/g, "");
    const outFile = path.join(outDir, `${employee}-${ts}.html`);
    fs.writeFileSync(outFile, html, "utf-8");

    console.log("");
    console.log("  \x1b[1m\x1b[33mClaude-360\x1b[0m Review card generated.");
    console.log(`  \x1b[2m${outFile}\x1b[0m`);
    console.log("");

    const platform = process.platform;
    try {
      if (platform === "darwin") execSync(`open "${outFile}"`);
      else if (platform === "win32") execSync(`start "" "${outFile}"`);
      else execSync(`xdg-open "${outFile}" 2>/dev/null`);
    } catch {
      // user can open manually
    }
  } catch (err) {
    console.error("\x1b[31mClaude-360 Error:\x1b[0m", err.message);
    process.exit(1);
  }
}

main();
