// ESLint flat config — Premium governance for the preview layer.
// Hard rule: no inline pixel values in JSX style props.
// All sizes must come from CSS custom properties (var(--*)) or the slotPos() API.

import js from "@eslint/js";
import tseslint from "@typescript-eslint/eslint-plugin";
import tsparser from "@typescript-eslint/parser";
import react from "eslint-plugin-react";
import reactHooks from "eslint-plugin-react-hooks";

const NUMERIC_PX_SELECTOR =
  "JSXAttribute[name.name='style'] Property[key.name=/^(fontSize|padding|paddingTop|paddingRight|paddingBottom|paddingLeft|margin|marginTop|marginRight|marginBottom|marginLeft|gap|rowGap|columnGap|width|height|minWidth|minHeight|maxWidth|maxHeight|top|right|bottom|left|borderRadius|borderWidth)$/] > Literal[value=/^[0-9]+$/]";

const PX_STRING_SELECTOR =
  "JSXAttribute[name.name='style'] Property[key.name=/^(fontSize|padding|paddingTop|paddingRight|paddingBottom|paddingLeft|margin|marginTop|marginRight|marginBottom|marginLeft|gap|rowGap|columnGap|width|height|minWidth|minHeight|maxWidth|maxHeight|top|right|bottom|left|borderRadius|borderWidth)$/] > Literal[value=/^[0-9]+(\\.[0-9]+)?px$/]";

export default [
  js.configs.recommended,
  {
    files: ["src/**/*.{ts,tsx}", "tooling/**/*.ts"],
    languageOptions: {
      parser: tsparser,
      parserOptions: {
        ecmaVersion: 2022,
        sourceType: "module",
        ecmaFeatures: { jsx: true },
      },
      globals: {
        window: "readonly",
        document: "readonly",
        console: "readonly",
        HTMLElement: "readonly",
        CSSStyleDeclaration: "readonly",
        HTMLDivElement: "readonly",
        JSX: "readonly",
        React: "readonly",
        process: "readonly",
      },
    },
    plugins: {
      "@typescript-eslint": tseslint,
      react,
      "react-hooks": reactHooks,
    },
    settings: { react: { version: "18.3" } },
    rules: {
      ...tseslint.configs.recommended.rules,
      ...react.configs.recommended.rules,
      ...reactHooks.configs.recommended.rules,
      "react/react-in-jsx-scope": "off",
      "react/prop-types": "off",
      "no-restricted-syntax": [
        "error",
        {
          selector: PX_STRING_SELECTOR,
          message:
            "Inline pixel string values are forbidden in style props. Use CSS custom properties (var(--sp-*), var(--fs-*)) or slotPos() instead.",
        },
        {
          selector: NUMERIC_PX_SELECTOR,
          message:
            "Inline numeric pixel values are forbidden in style props. Use CSS custom properties or slotPos() instead.",
        },
      ],
    },
  },
  {
    ignores: ["dist/**", "node_modules/**", "**/*.config.{js,ts}"],
  },
];
