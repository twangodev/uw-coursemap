import DefaultTheme from "vitepress/theme";

import "virtual:group-icons.css";
import "./custom.css";

import type { Theme } from "vitepress";

export default {
  extends: DefaultTheme,
} satisfies Theme;
