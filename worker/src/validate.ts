/**
 * Submission validation, derived from the canonical form-fields.json so it cannot
 * drift from the shipped form. Required text/textarea must be non-empty and within
 * their word/char caps; required checkboxes must be ticked; the axis must be one of
 * A1..A8. Pure and synchronous; no network.
 */

import { z } from "zod";
import { formFields, type FormField } from "./content.js";

const AXES = ["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8"] as const;

/** Raw form values: checkboxes arrive as presence (true) or absence (false/""). */
export type RawFields = Record<string, string | boolean | undefined>;

export interface ValidSubmission {
  rail_name: string;
  submitter: string;
  authorised_signatory: boolean;
  publication_url: string;
  challenged_passage: string;
  axis: (typeof AXES)[number];
  grounds: string;
  evidence: string;
  requested_remedy: string;
  public_reply: string;
  good_faith: boolean;
  consent: boolean;
}

export type ValidateResult =
  | { ok: true; value: ValidSubmission }
  | { ok: false; errors: string[] };

function wordCount(s: string): number {
  const t = s.trim();
  return t.length === 0 ? 0 : t.split(/\s+/).length;
}

function textSchema(f: FormField) {
  let s = z.string();
  if (f.required) s = s.min(1, `${f.id} is required`);
  if (f.maxLength) s = s.max(f.maxLength, `${f.id} exceeds ${f.maxLength} characters`);
  let out: z.ZodType<string> = s;
  if (f.maxWords) {
    out = s.refine((v) => wordCount(v) <= f.maxWords!, {
      message: `${f.id} exceeds ${f.maxWords} words`,
    });
  }
  return out;
}

/** Build the object schema once from the canonical field defs. */
function buildSchema() {
  const shape: Record<string, z.ZodTypeAny> = {};
  for (const f of formFields.fields) {
    if (f.type === "checkbox") {
      // A required checkbox must be explicitly true (ticked).
      shape[f.id] = f.required
        ? z.literal(true, { errorMap: () => ({ message: `${f.id} must be confirmed` }) })
        : z.boolean().optional();
    } else if (f.type === "axis-select") {
      shape[f.id] = z.enum(AXES, { errorMap: () => ({ message: "axis must be one of A1..A8" }) });
    } else {
      shape[f.id] = textSchema(f);
    }
  }
  return z.object(shape).strict();
}

const SCHEMA = buildSchema();

/** Coerce raw form values (strings + presence) into the shape the schema expects. */
function coerce(raw: RawFields): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const f of formFields.fields) {
    const v = raw[f.id];
    if (f.type === "checkbox") {
      // Ticked checkbox => truthy string ("on") or boolean true; else false.
      out[f.id] = v === true || (typeof v === "string" && v.length > 0);
    } else {
      out[f.id] = typeof v === "string" ? v : "";
    }
  }
  return out;
}

export function validateSubmission(raw: RawFields): ValidateResult {
  const parsed = SCHEMA.safeParse(coerce(raw));
  if (parsed.success) {
    return { ok: true, value: parsed.data as ValidSubmission };
  }
  return { ok: false, errors: parsed.error.issues.map((i) => i.message) };
}
