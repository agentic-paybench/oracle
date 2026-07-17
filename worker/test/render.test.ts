import { describe, expect, it } from "vitest";
import { renderFormPage, renderPolicyPage, bannerHtml, esc } from "../src/render.js";
import { formFields, policy, taxonomy } from "../src/content.js";
import type { Decision } from "../src/posture.js";

const denied: Decision = { mechanic: "published-rankings", allowed: false, rationale: "x" };
const allowed: Decision = { mechanic: "published-rankings", allowed: true, rationale: "x" };

describe("form + policy rendering", () => {
  it("renders all 12 fields onto the form", () => {
    const page = renderFormPage({ rankingsGate: denied, turnstileSitekey: "test" });
    for (const f of formFields.fields) {
      // Every field's label text appears on the page.
      expect(page).toContain(esc(f.label).slice(0, 20));
    }
    // Axis radios for all 8 axes.
    for (const a of taxonomy.axes) {
      expect(page).toContain(`value="${a.id}"`);
    }
  });

  it("includes the honeypot field and a Turnstile widget", () => {
    const page = renderFormPage({ rankingsGate: denied, turnstileSitekey: "sk-test" });
    expect(page).toContain('name="website"'); // honeypot
    expect(page).toContain("cf-turnstile");
    expect(page).toContain('data-sitekey="sk-test"');
  });

  it("shows the armed-idle banner when G_S21 is closed, active banner when open", () => {
    expect(bannerHtml(denied)).toContain("armed");
    expect(bannerHtml(denied)).toContain("No named results are published yet");
    expect(bannerHtml(allowed)).toContain("Named results are published");
  });

  it("renders all 10 policy points and the 8-axis table", () => {
    const page = renderPolicyPage();
    for (const p of policy.points) {
      expect(page).toContain(esc(p.title));
    }
    for (const a of taxonomy.axes) {
      expect(page).toContain(esc(a.name));
    }
  });

  it("escapes interpolated text", () => {
    expect(esc('<b>"&')).toBe("&lt;b&gt;&quot;&amp;");
  });

  it("uses only canonical names on both rendered pages", () => {
    const both =
      renderFormPage({ rankingsGate: denied, turnstileSitekey: "t" }) + renderPolicyPage();
    expect(both).not.toMatch(/agent\s*pay/i);
  });
});
