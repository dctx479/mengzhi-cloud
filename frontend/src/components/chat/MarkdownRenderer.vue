<template>
  <!-- S-P0-001修复: 使用 DOMPurify 清理 HTML 防止 XSS -->
  <div class="markdown-renderer" v-html="sanitizedHTML"></div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import DOMPurify from 'dompurify'
import 'highlight.js/styles/atom-one-light.css'

interface Props {
  content: string
}

const props = withDefaults(defineProps<Props>(), {})

// 配置 DOMPurify 安全策略
DOMPurify.setConfig({
  ALLOWED_TAGS: [
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'p', 'br', 'hr',
    'ul', 'ol', 'li',
    'blockquote', 'pre', 'code',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'a', 'strong', 'em', 'del', 'img', 'span', 'div'
  ],
  ALLOWED_ATTR: [
    'href', 'target', 'rel', 'class', 'src', 'alt', 'title',
    'colspan', 'rowspan'
  ],
  ALLOW_DATA_ATTR: false,
  ADD_ATTR: ['target', 'rel'],
})

// 初始化 Markdown 渲染器
const md: MarkdownIt = new MarkdownIt({
  html: false, // S-P0-001: 禁用原始 HTML 以增强安全性
  linkify: true,
  typographer: true,
  highlight: (str: string, lang: string) => {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return `<pre class="hljs"><code>${hljs.highlight(str, { language: lang, ignoreIllegals: true }).value}</code></pre>`
      } catch (e) {
        console.error('Highlight error:', e)
      }
    }
    return `<pre class="hljs"><code>${md.utils.escapeHtml(str)}</code></pre>`
  },
})

// 自定义渲染规则
const defaultLinkOpenRender = md.renderer.rules.link_open || function (tokens: any, idx: number, options: any, _env: any, self: any) {
  return self.renderToken(tokens, idx, options)
}

md.renderer.rules.link_open = function (tokens: any, idx: number, options: any, env: any, self: any) {
  const token = tokens[idx]
  token.attrSet('target', '_blank')
  token.attrSet('rel', 'noopener noreferrer')
  return defaultLinkOpenRender(tokens, idx, options, env, self)
}

// 自定义表格样式
const defaultTableOpenRender = md.renderer.rules.table_open || function (_tokens: any, _idx: any) {
  return '<table class="md-table">'
}

md.renderer.rules.table_open = defaultTableOpenRender

// 渲染并清理 HTML
const sanitizedHTML = computed(() => {
  try {
    const rawHTML = md.render(props.content)
    // S-P0-001: 使用 DOMPurify 清理潜在的 XSS 攻击代码
    return DOMPurify.sanitize(rawHTML)
  } catch (e) {
    console.error('Markdown render error:', e)
    return DOMPurify.sanitize(`<p>${props.content}</p>`)
  }
})
</script>

<style scoped lang="scss">
.markdown-renderer {
  width: 100%;
  word-break: break-word;
  overflow-x: auto;

  :deep(h1) {
    font-size: 24px;
    font-weight: 600;
    margin: 16px 0 12px 0;
    line-height: 1.4;
    border-bottom: 1px solid #e4e7eb;
    padding-bottom: 8px;

    &:first-child {
      margin-top: 0;
    }
  }

  :deep(h2) {
    font-size: 20px;
    font-weight: 600;
    margin: 14px 0 10px 0;
    line-height: 1.4;

    &:first-child {
      margin-top: 0;
    }
  }

  :deep(h3) {
    font-size: 18px;
    font-weight: 600;
    margin: 12px 0 8px 0;
    line-height: 1.4;

    &:first-child {
      margin-top: 0;
    }
  }

  :deep(h4),
  :deep(h5),
  :deep(h6) {
    font-size: 16px;
    font-weight: 600;
    margin: 10px 0 6px 0;
    line-height: 1.4;

    &:first-child {
      margin-top: 0;
    }
  }

  :deep(p) {
    margin: 8px 0;
    line-height: 1.6;
  }

  :deep(a) {
    color: #409eff;
    text-decoration: none;
    transition: color 0.3s;

    &:hover {
      color: #66b1ff;
      text-decoration: underline;
    }
  }

  :deep(code) {
    background: #f5f7fa;
    color: #d63384;
    padding: 2px 6px;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
    font-size: 12px;
  }

  :deep(pre) {
    background: #f5f7fa;
    border: 1px solid #dcdfe6;
    border-radius: 4px;
    padding: 12px;
    margin: 8px 0;
    overflow-x: auto;
    line-height: 1.5;

    code {
      background: transparent;
      color: inherit;
      padding: 0;
      border-radius: 0;
      font-size: 13px;
    }
  }

  :deep(blockquote) {
    border-left: 4px solid #409eff;
    background: #f5f7fa;
    padding: 8px 12px;
    margin: 8px 0;
    border-radius: 0 4px 4px 0;

    p {
      margin: 0;
    }
  }

  :deep(ul),
  :deep(ol) {
    margin: 8px 0;
    padding-left: 24px;
    line-height: 1.8;

    li {
      margin: 4px 0;

      p {
        margin: 0;
      }
    }
  }

  :deep(ul) {
    list-style-type: disc;
  }

  :deep(ol) {
    list-style-type: decimal;
  }

  :deep(.md-table) {
    width: 100%;
    border-collapse: collapse;
    margin: 8px 0;

    th,
    td {
      border: 1px solid #dcdfe6;
      padding: 8px 12px;
      text-align: left;
    }

    th {
      background: #f5f7fa;
      font-weight: 600;
    }

    tr:nth-child(even) {
      background: #fafafa;
    }
  }

  :deep(img) {
    max-width: 100%;
    height: auto;
    border-radius: 4px;
    margin: 8px 0;
  }

  :deep(hr) {
    border: none;
    border-top: 1px solid #dcdfe6;
    margin: 16px 0;
  }

  :deep(.hljs) {
    background: transparent;
    padding: 0;
    border-radius: 0;

    code {
      color: #333;
    }
  }

  // 代码高亮样式
  :deep(.hljs-attr),
  :deep(.hljs-attribute) {
    color: #e6db74;
  }

  :deep(.hljs-literal) {
    color: #ae81ff;
  }

  :deep(.hljs-meta),
  :deep(.hljs-meta-string) {
    color: #a1efe4;
  }

  :deep(.hljs-number) {
    color: #ae81ff;
  }

  :deep(.hljs-operator) {
    color: #f92672;
  }

  :deep(.hljs-selector-attr),
  :deep(.hljs-selector-class),
  :deep(.hljs-selector-id),
  :deep(.hljs-selector-pseudo),
  :deep(.hljs-selector-tag) {
    color: #a6e22e;
  }

  :deep(.hljs-string) {
    color: #e6db74;
  }

  :deep(.hljs-symbol) {
    color: #ae81ff;
  }

  :deep(.hljs-template-tag),
  :deep(.hljs-template-variable),
  :deep(.hljs-type),
  :deep(.hljs-variable) {
    color: #a6e22e;
  }
}

@media (max-width: 768px) {
  .markdown-renderer {
    :deep(h1) {
      font-size: 20px;
    }

    :deep(h2) {
      font-size: 18px;
    }

    :deep(h3) {
      font-size: 16px;
    }

    :deep(pre) {
      padding: 8px;
      font-size: 12px;
    }
  }
}
</style>
