import DefaultTheme from 'vitepress/theme'

import 'virtual:group-icons.css'
import './custom.css'

import type { Theme } from 'vitepress'
import {theme} from "vitepress-openapi/client";
import 'vitepress-openapi/dist/style.css'

export default {
    extends: DefaultTheme,
    async enhanceApp({ app }) {
        theme.enhanceApp({ app })
    }
} satisfies Theme