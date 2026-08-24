import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const posts = defineCollection({
  // Preserve the exact filename (case + unicode) as the entry id so URLs match
  // the original Chirpy permalinks, e.g. `Zippu.md` -> `/posts/Zippu/`.
  loader: glob({
    pattern: '**/*.md',
    base: './src/content/posts',
    generateId: ({ entry }) => entry.replace(/\.md$/, '')
  }),
  schema: z.object({
    title: z.string(),
    date: z.coerce.date(),
    categories: z.array(z.string()).default([]),
    tags: z.array(z.string()).default([]),
    image: z.string().optional(),
    pin: z.boolean().default(false)
  })
});

// 미리보기 전용: 발행 폴더(src/content/posts) 밖의 drafts/ 를 로컬에서만 렌더.
const drafts = defineCollection({
  loader: glob({
    pattern: '**/*.md',
    base: './drafts',
    generateId: ({ entry }) => entry.replace(/\.md$/, '')
  }),
  schema: z.object({
    title: z.string(),
    date: z.coerce.date(),
    categories: z.array(z.string()).default([]),
    tags: z.array(z.string()).default([]),
    image: z.string().optional(),
    pin: z.boolean().default(false)
  })
});

export const collections = { posts, drafts };
