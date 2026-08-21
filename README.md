# DonZ 기술 블로그

CS 공부와 회사 업무 중 발견한 이슈 경험담을 기록하는 기술 블로그.

## Stack

[Astro](https://astro.build/)로 빌드하는 정적 사이트. GitHub Actions로 GitHub Pages에 배포.

- 글: `src/content/posts/*.md` (Content Collections)
- 페이지/레이아웃: `src/pages`, `src/layouts`
- 스타일: `src/styles/global.css`
- 조회수: GoatCounter, 댓글: utterances

## Develop

```bash
npm install
npm run dev      # http://localhost:4321
npm run build    # -> dist/
npm run preview
```
