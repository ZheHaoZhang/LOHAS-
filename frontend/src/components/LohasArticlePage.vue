<script setup lang="ts">
import { lohasChannelArticle } from '../content/lohasChannelArticle'

defineProps<{
  theme: 'light' | 'dark'
  onToggleTheme: () => void
}>()
</script>

<template>
  <main class="article-shell">
    <section class="article-card article-hero-card">
      <button
        class="theme-toggle article-theme-toggle"
        type="button"
        :aria-label="theme === 'dark' ? '切換為日間模式' : '切換為夜間模式'"
        @click="onToggleTheme"
      >
        <svg
          v-if="theme === 'dark'"
          xmlns="http://www.w3.org/2000/svg"
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <circle cx="12" cy="12" r="5" />
          <line x1="12" y1="1" x2="12" y2="3" />
          <line x1="12" y1="21" x2="12" y2="23" />
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
          <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
          <line x1="1" y1="12" x2="3" y2="12" />
          <line x1="21" y1="12" x2="23" y2="12" />
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
          <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
        </svg>
        <svg
          v-else
          xmlns="http://www.w3.org/2000/svg"
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
        </svg>
      </button>

      <p class="eyebrow">研究原文頁</p>
      <h1>{{ lohasChannelArticle.title }}</h1>
      <p class="article-lead">{{ lohasChannelArticle.lead }}</p>

      <div class="hero-actions">
        <a class="secondary-button" href="#">返回首頁圖表</a>
      </div>
    </section>

    <section class="summary-grid article-summary-grid">
      <article
        v-for="highlight in lohasChannelArticle.highlights"
        :key="highlight.label"
        class="summary-card"
      >
        <span class="summary-label">{{ highlight.label }}</span>
        <strong>{{ highlight.value }}</strong>
        <small>{{ highlight.description }}</small>
      </article>
    </section>

    <section class="article-card article-body">
      <article
        v-for="section in lohasChannelArticle.sections"
        :key="section.title"
        class="article-section"
      >
        <span class="summary-label">{{ section.eyebrow }}</span>
        <h2>{{ section.title }}</h2>
        <p v-for="paragraph in section.paragraphs" :key="paragraph">
          {{ paragraph }}
        </p>

        <ul v-if="section.bullets?.length" class="article-list">
          <li v-for="bullet in section.bullets" :key="bullet">{{ bullet }}</li>
        </ul>
      </article>
    </section>

    <section class="article-card article-body">
      <article class="article-section">
        <span class="summary-label">引用來源</span>
        <h2>原文中提到的延伸資料</h2>
        <ul class="article-source-list">
          <li v-for="source in lohasChannelArticle.sources" :key="source.url">
            <a :href="source.url" target="_blank" rel="noreferrer">
              {{ source.label }}
            </a>
          </li>
        </ul>
      </article>
    </section>
  </main>
</template>
