import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import MarkdownRenderer from '@/components/chat/MarkdownRenderer.vue'

describe('MarkdownRenderer.vue', () => {
  it('renders plain text correctly', () => {
    const wrapper = mount(MarkdownRenderer, {
      props: {
        content: 'Hello, World!'
      }
    })
    expect(wrapper.text()).toContain('Hello, World!')
  })

  it('renders headings correctly', () => {
    const wrapper = mount(MarkdownRenderer, {
      props: {
        content: '# Heading 1\n## Heading 2'
      }
    })
    const headings = wrapper.findAll('h1, h2')
    expect(headings.length).toBe(2)
  })

  it('renders code blocks with syntax highlighting', () => {
    const wrapper = mount(MarkdownRenderer, {
      props: {
        content: '```javascript\nconst x = 1;\n```'
      }
    })
    const preBlocks = wrapper.findAll('pre')
    expect(preBlocks.length).toBeGreaterThan(0)
  })

  it('renders lists correctly', () => {
    const wrapper = mount(MarkdownRenderer, {
      props: {
        content: '- Item 1\n- Item 2\n- Item 3'
      }
    })
    const listItems = wrapper.findAll('li')
    expect(listItems.length).toBe(3)
  })

  it('renders links with target blank', () => {
    const wrapper = mount(MarkdownRenderer, {
      props: {
        content: '[Example](https://example.com)'
      }
    })
    const link = wrapper.find('a')
    expect(link.attributes('target')).toBe('_blank')
    expect(link.attributes('rel')).toContain('noopener')
  })

  it('renders tables correctly', () => {
    const content = `| Header 1 | Header 2 |
| --- | --- |
| Cell 1 | Cell 2 |`
    const wrapper = mount(MarkdownRenderer, {
      props: { content }
    })
    const table = wrapper.find('table')
    expect(table.exists()).toBe(true)
  })

  it('handles empty content gracefully', () => {
    const wrapper = mount(MarkdownRenderer, {
      props: {
        content: ''
      }
    })
    expect(wrapper.exists()).toBe(true)
  })

  it('renders blockquotes correctly', () => {
    const wrapper = mount(MarkdownRenderer, {
      props: {
        content: '> This is a quote'
      }
    })
    const blockquote = wrapper.find('blockquote')
    expect(blockquote.exists()).toBe(true)
  })

  it('handles mixed markdown content', () => {
    const content = `# Title

This is a paragraph with **bold** and *italic* text.

- List item 1
- List item 2

\`\`\`
code block
\`\`\`

[Link](https://example.com)`

    const wrapper = mount(MarkdownRenderer, {
      props: { content }
    })
    expect(wrapper.text()).toContain('Title')
    expect(wrapper.find('h1').exists()).toBe(true)
    expect(wrapper.find('ul').exists()).toBe(true)
    expect(wrapper.find('a').exists()).toBe(true)
  })
})
