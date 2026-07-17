import js from "@eslint/js";
import tseslint from "@typescript-eslint/eslint-plugin";
import tsparser from "@typescript-eslint/parser";

export default [
  {
    // scripts/** are standalone Node ops utilities (draft-reply, send-notice,
    // posture-guard), run directly with `node`, not part of the typed Worker
    // surface. dist/** is build output.
    ignores: [
      "dist/**",
      ".wrangler/**",
      "node_modules/**",
      "coverage/**",
      "scripts/**",
    ],
  },
  js.configs.recommended,
  {
    files: ["**/*.ts"],
    languageOptions: {
      parser: tsparser,
      parserOptions: {
        ecmaVersion: 2022,
        sourceType: "module",
      },
      globals: {
        // Worker + test globals; TypeScript resolves the real types.
        console: "readonly",
        crypto: "readonly",
        fetch: "readonly",
        URL: "readonly",
        Response: "readonly",
        Request: "readonly",
        Headers: "readonly",
        TextEncoder: "readonly",
        TextDecoder: "readonly",
        process: "readonly",
      },
    },
    plugins: {
      "@typescript-eslint": tseslint,
    },
    rules: {
      ...tseslint.configs.recommended.rules,
      // TypeScript itself resolves identifiers (incl. Worker/DOM types), so the
      // core rule only produces false positives here.
      "no-undef": "off",
      "@typescript-eslint/no-explicit-any": "warn",
      "@typescript-eslint/no-unused-vars": [
        "error",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],
    },
  },
];
