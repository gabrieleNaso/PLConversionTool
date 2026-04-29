#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const PROJECT_ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const GENERATED_ROOT = path.join(PROJECT_ROOT, "data", "output", "generated");

function listDirs(root) {
  return fs
    .readdirSync(root, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => path.join(root, d.name));
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function findIrJson(bundleDir) {
  const files = fs.readdirSync(bundleDir);
  const ir = files.find((f) => f.toLowerCase().endsWith("_ir.json"));
  return ir ? path.join(bundleDir, ir) : null;
}

function findAnalysisJson(bundleDir) {
  const files = fs.readdirSync(bundleDir);
  const analysis = files.find((f) => f.toLowerCase().endsWith("_analysis.json"));
  return analysis ? path.join(bundleDir, analysis) : null;
}

function findSupportLogicRowsFromAnalysis(analysisJson) {
  // In analysis JSON, support logic rows are embedded inside `ir.support_logic`.
  const ir = analysisJson?.ir;
  const items = Array.isArray(ir?.support_logic) ? ir.support_logic : [];
  return items.filter((item) => item && typeof item === "object" && "category" in item && "result_member" in item);
}

const STEP_TOKEN_RE = /\bS\d+(?:\.X)?\b/gi;
const BAD_BOOL_RE = /\b(AND|OR)\s*\)|\(\s*(AND|OR)\b|(\bAND\b\s+\bAND\b)|(\bOR\b\s+\bOR\b)/i;

function scanBundle(bundleDir) {
  const irPath = findIrJson(bundleDir);
  if (!irPath) return null;
  const analysisPath = findAnalysisJson(bundleDir);
  const ir = readJson(irPath);
  const analysisJson = analysisPath ? readJson(analysisPath) : null;

  const steps = Array.isArray(ir.steps) ? ir.steps : [];
  const transitions = Array.isArray(ir.transitions) ? ir.transitions : [];
  const rows = analysisJson ? findSupportLogicRowsFromAnalysis(analysisJson) : [];

  const issues = [];

  for (const tr of transitions) {
    const expr = String(tr.guard_expression ?? "").trim();
    const stepTokens = Array.from(expr.matchAll(STEP_TOKEN_RE)).map((m) => m[0].toUpperCase());
    if (stepTokens.length) {
      issues.push({
        kind: "transition_guard_contains_steps",
        transition_id: tr.transition_id,
        source_step: tr.source_step,
        target_step: tr.target_step,
        guard_expression: expr,
        steps: [...new Set(stepTokens)].join(", "),
      });
    }
    if (BAD_BOOL_RE.test(expr)) {
      issues.push({
        kind: "transition_guard_malformed_boolean",
        transition_id: tr.transition_id,
        guard_expression: expr,
      });
    }
  }

  for (const row of rows) {
    const expr = String(row.condition_expression ?? "").trim();
    if (!expr) continue;
    if (BAD_BOOL_RE.test(expr)) {
      issues.push({
        kind: "support_fc_expression_malformed_boolean",
        category: row.category,
        result_member: row.result_member,
        network_index: row.network_index,
        expr,
      });
    }
  }

  return {
    bundle: path.basename(bundleDir),
    irPath: path.relative(PROJECT_ROOT, irPath),
    analysisPath: analysisPath ? path.relative(PROJECT_ROOT, analysisPath) : null,
    steps: steps.length,
    transitions: transitions.length,
    supportRows: rows.length,
    issues,
  };
}

const wanted = new Set(["auto_awl_romania", "auto_awl_romania_2", "auto_awl_romania_3", "auto_awl_romania_4"]);
const bundles = listDirs(GENERATED_ROOT).filter((d) => wanted.has(path.basename(d)));

const reports = bundles.map(scanBundle).filter(Boolean);

for (const r of reports) {
  console.log(`\n== ${r.bundle} ==`);
  console.log(`IR: ${r.irPath}`);
  if (r.analysisPath) console.log(`analysis: ${r.analysisPath}`);
  console.log(`steps=${r.steps} transitions=${r.transitions} supportRows=${r.supportRows}`);
  const counts = r.issues.reduce((acc, item) => {
    acc[item.kind] = (acc[item.kind] || 0) + 1;
    return acc;
  }, {});
  const kinds = Object.keys(counts).sort();
  if (!kinds.length) {
    console.log("issues: none");
    continue;
  }
  console.log("issues:");
  for (const k of kinds) console.log(`- ${k}: ${counts[k]}`);
  const sample = r.issues.slice(0, 6);
  for (const item of sample) console.log("  sample:", JSON.stringify(item));
}
