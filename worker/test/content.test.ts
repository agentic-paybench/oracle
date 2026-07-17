import { readFileSync, readdirSync } from "node:fs";
import { describe, expect, it } from "vitest";
import {
  taxonomy,
  formFields,
  policy,
  IMMEDIATE_AXES,
  PRE_MODERATED_AXES,
} from "../src/content.js";

const templatesDir = new URL("../content/templates/", import.meta.url);

function readTemplate(id: string): string {
  return readFileSync(new URL(`${id}.md`, templatesDir), "utf-8");
}

/** Parse the simple front-matter block at the top of a template. */
function frontMatter(md: string): Record<string, string> {
  const m = md.match(/^---\n([\s\S]*?)\n---/);
  const out: Record<string, string> = {};
  const block = m?.[1];
  if (!block) return out;
  for (const line of block.split("\n")) {
    const i = line.indexOf(":");
    if (i > 0) out[line.slice(0, i).trim()] = line.slice(i + 1).trim();
  }
  return out;
}

describe("F4 taxonomy transcription", () => {
  it("has exactly 8 axes A1..A8", () => {
    expect(taxonomy.axes).toHaveLength(8);
    expect(taxonomy.axes.map((a) => a.id)).toEqual([
      "A1",
      "A2",
      "A3",
      "A4",
      "A5",
      "A6",
      "A7",
      "A8",
    ]);
  });

  it("has exactly 12 form fields including a single-choice axis field", () => {
    expect(formFields.fields).toHaveLength(12);
    const axisField = formFields.fields.find((f) => f.id === "axis");
    expect(axisField?.type).toBe("axis-select");
    expect(axisField?.options).toEqual(["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8"]);
  });

  it("has exactly 10 policy points numbered 1..10", () => {
    expect(policy.points).toHaveLength(10);
    expect(policy.points.map((p) => p.n)).toEqual([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);
  });

  it("ships exactly 8 per-axis templates A1..A8", () => {
    const files = readdirSync(templatesDir).filter((f) => f.endsWith(".md")).sort();
    expect(files).toEqual([
      "A1.md",
      "A2.md",
      "A3.md",
      "A4.md",
      "A5.md",
      "A6.md",
      "A7.md",
      "A8.md",
    ]);
  });

  it("encodes the locked moderation split (A1/A2/A6/A7/A8 pre-moderated; A3/A4/A5 immediate)", () => {
    for (const a of taxonomy.axes) {
      if (IMMEDIATE_AXES.has(a.id)) {
        expect(a.visibility).toBe("immediate-pending-badge");
      } else {
        expect(PRE_MODERATED_AXES.has(a.id)).toBe(true);
        expect(a.visibility).toBe("pre-moderated");
      }
    }
    // The two sets partition A1..A8 with no overlap.
    expect(IMMEDIATE_AXES.size + PRE_MODERATED_AXES.size).toBe(8);
  });

  it("keeps each template consistent with its taxonomy axis (no drift)", () => {
    for (const a of taxonomy.axes) {
      const fm = frontMatter(readTemplate(a.id));
      expect(fm.axis).toBe(a.id);
      expect(fm.visibility).toBe(a.visibility);
      expect(fm.target_response).toBe(a.target_response);
      // The remedy text appears in the rendered template body.
      expect(readTemplate(a.id)).toContain(a.remedy);
    }
  });

  it("uses only canonical names: no reserved token on any content surface", () => {
    const surfaces = [
      JSON.stringify(taxonomy),
      JSON.stringify(formFields),
      JSON.stringify(policy),
      ...taxonomy.axes.map((a) => readTemplate(a.id)),
    ].join("\n");
    expect(surfaces).not.toMatch(/agent\s*pay/i);
  });
});
