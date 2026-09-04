---
title: "DonZ를 만들며 #3 — 만들고 나니 검색에 안 나왔다: 사이드 프로젝트 SEO 수정기"
date: 2026-08-31
categories: ["SEO"]
tags: ["SEO", "canonical", "hreflang", "Next.js", "SPA", "i18n"]
---

> [1편](/posts/DonZ를-만들며-1-LLM을-안-부르기로-한-결정)·[2편](/posts/DonZ를-만들며-2-생년월일-하나가-생각보다-어려웠다)은 "어떻게 만들었나"였다. 이 편은 만든 다음이다. 코드는 도는데 검색엔 안 나온다. 클라이언트 라우팅 + 다국어 + 커스텀 도메인 이전이 한꺼번에 겹친, 흔한 사이드 프로젝트 SEO 삽질 기록이다.

## 문제 0 — 모든 라우트가 같은 제목이었다

가장 기본이 빠져 있었다. 도구가 여럿(차 나이 `/age`, 궁합 `/compatibility`, 사주 차량 `/saju-car`)인데 **모든 라우트가 루트 레이아웃의 사이트 기본 title을 그대로** 달고 있었다. 검색 결과에서 다 똑같이 뜨니 어느 페이지도 자기 키워드로 잡힐 근거가 없었다.

라우트마다 자기를 설명하게 만드는 게 첫 수정이었는데, 여기서 클라이언트 컴포넌트 함정을 밟았다.

- `/age`는 `page.tsx`가 `'use client'`라 `metadata`를 못 내보낸다. → 그 라우트에 **서버 `layout.tsx`를 따로 두고** title/description을 거기서 채웠다.
- `/saju-car` metadata는 하드코딩된 한국어였다. → 로케일별 메시지로 교체.

## 문제 1 — 홈이 자기 자신을 설명하지 못했다

홈을 도구 허브(대시보드)로 바꾼 뒤에도 사이트 전역 메타는 여전히 **차량 나이 계산기 하나만** 설명하고 있었다. 게다가 홈엔 카드 라벨 말고 본문도 h1도 없어서, 크롤러가 "이 사이트가 뭐다"라고 읽을 텍스트 근거 자체가 없었다.

```
홈이 도구 허브가 된 뒤에도 사이트 전역 메타는 차량 나이 계산기만
설명하고 있었다. 카드 라벨 외에 본문·h1이 없어 색인 근거도 없었다.
```

고친 것:

- `meta.title/description/keywords`를 허브 기준(나이 계산 + 궁합 + 사주 추천)으로 5개 언어 모두 교체.
- 홈 `page.tsx`를 **서버 컴포넌트로 분리**(본문은 `dashboard.tsx`)해 구조화 데이터를 붙일 수 있게 함.
- 홈 본문에 **h1 + 리드 + "할 수 있는 것" 섹션**(도구 3개 × 2문장, 각 제목이 해당 라우트로 가는 내부 링크).
- **JSON-LD 분리** — 루트 레이아웃은 `WebSite`, 홈은 `ItemList`(도구 3개를 각각 이름·설명·URL·무료 `Offer`를 가진 `WebApplication`으로 노출).
- 브랜드명을 5개 언어에서 제각각이던 걸 **DonZ로 통일**.

이후 화면 배치상 h1·리드를 카드 그리드 아래로 내렸다. 판단 근거는 명확했다 — **문서에 존재하고 description과 내용이 맞으면 위치는 색인에 영향이 없다.** SEO를 이유로 레이아웃을 억지로 비틀 필요는 없었다.

## 문제 2 — 이름이 검색 신호가 아니었다

원래 라우트는 `/ilju`였다. "ilju"는 아무도 검색창에 치지 않는 로마자 표기라, 그 URL엔 검색 유입 신호가 0이었다. 그래서 `/saju-car`로 이관했다.

- `src/app/ilju` → `src/app/saju-car`, `public/ilju` → `public/saju-car`.
- sitemap, 대시보드 카드 href(5개 로케일), 공유 링크 경로, 캐릭터 SVG 경로를 **함께** 수정.
- 아직 색인 전이라 리다이렉트는 두지 않았다(`/ilju`는 404).
- 반면 도메인 모듈 `src/lib/ilju`는 **개념 이름**이라 그대로 뒀다 — URL 슬러그와 코드 정체성은 다른 층위다.

## 다국어라서 URL이 언어마다 하나씩 생긴다

5개 로케일(ko/en/ja/zh/ar)을 지원하면, 각 언어가 **자기만의 크롤 가능한 URL**을 가져야 한다(hreflang). 라우팅은 Next 16 프록시로 처리했다.

```ts
// proxy.ts — 기본(ko)은 무접두 루트, 나머지는 접두 경로
// /ko/... -> 무접두 canonical (기본 로케일의 중복 URL 방지)
if (pathLocale === defaultLocale) {
  url.pathname = pathname.replace(/^\/ko(?=\/|$)/, '') || '/';
  const res = NextResponse.redirect(url);
  res.cookies.set(LOCALE_COOKIE, defaultLocale, { path: '/', maxAge: ONE_YEAR });
  return res;
}
// /en, /ja, ... -> 공유 라우트 트리로 rewrite + 로케일/경로 헤더 전달
if (pathLocale) {
  headers.set('x-locale', pathLocale);
  headers.set('x-pathname', pathname);
  return NextResponse.rewrite(url, { request: { headers } });
}
```

여기서 canonical은 실제 경로를 `x-pathname` 헤더로 받아 로케일별로 짓는다.

```ts
// layout.tsx — generateMetadata
const suffix = stripLocalePrefix(store.get('x-pathname') || '/');
const canonical = localizePath(locale, suffix);
const languages = { 'x-default': localizePath(defaultLocale, suffix) };
for (const loc of locales) languages[loc] = localizePath(loc, suffix);
return { metadataBase: new URL(SITE_URL), alternates: { canonical, languages }, /* … */ };
```

sitemap도 4개 경로 × 로케일마다 엔트리를 뽑고, 각각에 `x-default` + 언어별 `alternates`를 붙인다. 기본 로케일 경로를 무접두로 리다이렉트한 이유가 여기 있다 — 안 그러면 `/`와 `/ko/`가 같은 내용의 중복 URL이 된다.

## 중복 콘텐츠를 막는다

색인에 넣지 말아야 할 것도 있다.

- **공유 페이지**(`/share/[data]`, `/saju-car/share/[data]`)엔 `noindex`. 결과 조합마다 URL이 생겨 사실상 무한 중복 콘텐츠이고, 사이트맵에도 넣지 않았다.
- **preview·로컬 배포는 통째로 크롤 차단.** Vercel 프리뷰는 커밋마다 임시 URL이 생기는데, 색인되면 사이트 전체가 복제된다.

```ts
// robots.ts — production 배포만 크롤 허용
if (process.env.VERCEL_ENV !== 'production') {
  return { rules: { userAgent: '*', disallow: '/' } };
}
return { rules: { userAgent: '*', allow: '/' }, sitemap: `${SITE_URL}/sitemap.xml`, host: SITE_URL };
```

## 도메인 하나로 수렴시킨다

마지막은 커스텀 도메인 이전(`vercel.app` → `www.east2lab.com`)이었다. 이게 아프지 않았던 건, 그 전에 **절대 URL의 출처를 한 값으로 모아뒀기** 때문이다. canonical·hreflang·OG·sitemap·robots·JSON-LD가 layout·robots·sitemap 세 곳에 하드코딩돼 있던 걸 `lib/site.ts` 하나로 통합했다.

```ts
// site.ts — 크롤러가 보는 모든 절대 URL의 단일 출처
export const SITE_URL =
  (process.env.NEXT_PUBLIC_SITE_URL ?? 'https://www.east2lab.com').replace(/\/$/, '');
```

도메인 이전은 결국 이 환경변수 한 줄을 바꾸는 일이 됐다.

> 곁다리로, 클라이언트 라우팅 SPA라 GA 자동 `page_view`가 최초 `/`에서 한 번만 찍히고 라우트 전환이 안 잡혔다. `send_page_view:false`로 끄고 화면 전환마다 `trackScreen`으로 직접 쏴서 라우트별 집계를 살렸다. 검색과 분석 양쪽에서 "SPA는 페이지 전환이 자동으로 안 잡힌다"는 같은 병이었다.

## 마무리

코드가 도는 것과 검색에 잡히는 건 완전히 다른 일이었다. 되짚어 보면 원칙은 둘이었다.

1. **라우트마다 자기를 설명하게 하라** — 공용 기본 메타에 얹혀 가면 아무도 안 잡힌다. title·h1·구조화 데이터·내부 링크까지.
2. **절대 URL은 단일 출처에서** — canonical·hreflang·sitemap·robots·OG가 한 값에서 파생되면, 도메인 이전이 환경변수 한 줄로 끝난다.

## 관련 작업

- 라우트별 metadata + 공유 noindex: `src/app/*/layout.tsx`, `generateMetadata`(`5513c5f`).
- 홈 허브 메타·h1·JSON-LD·DonZ 통일: `src/app/_components/dashboard.tsx`(`971b505`), h1 위치(`058fd6d`).
- 슬러그 이관 `/ilju → /saju-car`: sitemap·href·공유·SVG 동시 수정(`00df67c`).
- 로케일 라우팅·canonical·hreflang: `src/proxy.ts`, `src/app/layout.tsx`, `src/app/sitemap.ts`.
- 크롤 정책: `src/app/robots.ts`(production-only).
- 절대 URL 단일 출처·도메인 이전: `src/lib/site.ts`, `NEXT_PUBLIC_SITE_URL`(`ae8ae90`).
- 앞 편: [#1 LLM을 안 부르기로 한 결정](/posts/DonZ를-만들며-1-LLM을-안-부르기로-한-결정) · [#2 생년월일 하나가 생각보다 어려웠다](/posts/DonZ를-만들며-2-생년월일-하나가-생각보다-어려웠다)
