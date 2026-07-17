/**
 * Canonical content loaders. The taxonomy, form, and policy live in JSON; the
 * form, policy page, and per-axis response templates all render from these files,
 * so they cannot drift from the canonical taxonomy. This module just types +
 * re-exports them; it invents nothing.
 */

import taxonomyJson from "../content/taxonomy.json";
import formFieldsJson from "../content/form-fields.json";
import policyJson from "../content/policy.json";

export type Visibility = "pre-moderated" | "immediate-pending-badge";

export interface Axis {
  id: string;
  name: string;
  trigger: string;
  required_evidence: string;
  remedy: string;
  target_response: string;
  visibility: Visibility;
}

export interface FormField {
  id: string;
  label: string;
  type: string;
  required: boolean;
  maxLength?: number;
  maxWords?: number;
  options?: string[];
}

export interface PolicyPoint {
  n: number;
  title: string;
  text: string;
}

export const taxonomy = taxonomyJson as unknown as {
  visibility_rule: string;
  axes: Axis[];
};
export const formFields = formFieldsJson as unknown as {
  title: string;
  intro: string;
  fields: FormField[];
};
export const policy = policyJson as unknown as {
  title: string;
  framing: string;
  points: PolicyPoint[];
};

/** Axis ids that publish immediately with a badge, vs those pre-moderated. */
export const IMMEDIATE_AXES = new Set(["A3", "A4", "A5"]);
export const PRE_MODERATED_AXES = new Set(["A1", "A2", "A6", "A7", "A8"]);

export function axisById(id: string): Axis | undefined {
  return taxonomy.axes.find((a) => a.id === id);
}
