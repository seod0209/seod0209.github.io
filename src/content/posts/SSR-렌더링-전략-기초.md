---
title: "SSR 렌더링 전략 기초 - landing을 SSR로 옮기며 배운 것들"
date: 2025-03-18
categories: ["React"]
tags: ["Next.js", "SSR", "CLS", "성능"]
---

> 시리즈 'React 성능·메모리' 1편. 렌더링 전략을 어디서 결정하느냐가 초기 성능을 좌우한다.

오토캐시백 landing 페이지를 열면 처음엔 멀쩡한데, 이미지가 뒤늦게 들어오면서 아래 내용이 우르르 밀려 내려갔다. 소위 CLS(Cumulative Layout Shift). 사용자 입장에선 "누르려던 버튼이 갑자기 도망가는" 그 경험이다. 이걸 잡으려고 하다 보니 결국 "이 페이지를 클라이언트에서 그릴 거냐, 서버에서 그릴 거냐"라는 렌더링 전략 얘기로 돌아왔다.

## CSR / SSR / SSG, 뭐가 다른가

간단히만 정리한다.

- **CSR(Client-Side Rendering)**: 서버는 빈 HTML + JS 번들만 준다. 브라우저가 JS를 받아 실행해야 화면이 생긴다. 초기엔 아무것도 없다가 확 채워진다 → 레이아웃이 흔들린다.
- **SSR(Server-Side Rendering)**: 요청 시점에 서버가 HTML을 완성해서 내려준다. 첫 페인트에 이미 실제 내용이 들어있다.
- **SSG/ISR**: 빌드(또는 일정 주기)에 미리 HTML을 만들어 캐시해두고 재사용한다. 이 구간엔 서버 렌더/서버 API 호출이 아예 안 일어난다.

landing 같은 "SEO도 중요하고, 첫 화면이 곧 광고인" 페이지는 첫 페인트가 곧 지표다. 그래서 CSR에서 SSR로 옮기는 게 맞았다.

## Landing을 서버 컴포넌트로

기존 `Landing`은 `'use client'`에 `useSearchParams`, `useEffect`로 이벤트를 쏘는 클라이언트 컴포넌트였다. 문제는 이 이벤트 로직 때문에 landing 전체가 클라이언트에 묶여 있었다는 것.

```tsx
// Before: landing 전체가 클라이언트
'use client';

import { useSearchParams } from 'next/navigation';
import { useEffect } from 'react';

const Landing = () => {
  const searchParams = useSearchParams();

  useEffect(() => {
    // view_autocashback 이벤트 전송...
  }, []);

  return <section>{/* ...정적인 마크업 대부분 */}</section>;
};
```

내용의 대부분은 사실 정적 마크업인데, 화면 진입 이벤트 하나 때문에 `'use client'`가 붙어 있었다. 그래서 이벤트 전송은 아래 계산기 섹션(어차피 상호작용이 있는 곳)으로 옮기고, landing 자체는 서버 컴포넌트로 되돌렸다.

```tsx
// After: 서버 컴포넌트. 'use client' 제거, 이벤트 로직 분리
import Image from '@shared/common/Image';
import { AUTO_CASHBACK_MAX_DISCOUNT_PERCENTAGE } from '@shared/utils/constant/auto-cashback';

const Landing = () => {
  const imageUrl = 'auto-cashback-card-2';
  return <section>{/* 정적 마크업만 남김 */}</section>;
};
```

페이지도 async 서버 컴포넌트로 바꾸고, 각 섹션을 `Suspense`로 감싸되 **fallback을 실제 높이를 차지하는 스켈레톤**으로 줬다.

```tsx
export default async function AutoCashback() {
  return (
    <div className={Wrapper}>
      <div className={Container}>
        <div className={LeftSideContainer}>
          <Suspense fallback={<ContentLoading />}>
            {/* @ts-expect-error Async Server Component */}
            <Landing />
          </Suspense>
          <Suspense fallback={<ContentLoading />}>
            <CalculatorTabs />
          </Suspense>
          {/* 리스트도 자리를 미리 잡아두는 fallback */}
          <Suspense fallback={<div className={CarBrandListSection} />}>
            <div className={CarBrandListSection}>
              <CarBrandList title="캐시백 금액 비교해보기" />
            </div>
          </Suspense>
        </div>
      </div>
    </div>
  );
}
```

여기서 핵심은 `fallback`이 빈 값이 아니라는 점이다. 빈 `<Suspense>`는 콘텐츠가 도착하기 전엔 높이 0이라, 도착하는 순간 아래를 밀어낸다. 자리를 미리 잡아주는 fallback이 곧 CLS 방어다.

## CLS를 잡는 두 축: 최소 높이 + blur placeholder

첫째, 컨테이너에 최소 높이를 박아 초기 뷰포트를 확보했다.

```tsx
// index.css.ts (vanilla-extract)
export const mainContainer = style({
  width: '100%',
  minHeight: '100dvh', // height: fit-content → minHeight로
});
```

`100vh`가 아니라 `100dvh`를 쓴 이유는 모바일 주소창 유무에 따라 뷰포트 높이가 출렁이기 때문이다. `dvh`(dynamic viewport height)는 그 변화를 반영한다. 리스/렌트/아티클 각 홈 화면에도 동일하게 `minHeight: '100dvh'`를 줬다.

둘째, 이미지에 blur placeholder를 기본값으로 넣어 로드 전에도 자리와 톤을 유지하게 했다.

```tsx
const DEFAULT_BLUR = 'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQ...'; // 초경량 blur

export default function Image({
  isLazy = false,
  isSmall = false,
  blurDataUrl = DEFAULT_BLUR,
  ...props
}: ImageProps) {
  return (
    <NextImage
      priority={!isLazy}
      loading={isLazy ? 'lazy' : 'eager'}
      placeholder={isSmall ? undefined : 'blur'}
      blurDataURL={isSmall ? undefined : blurDataUrl}
      {...props}
    />
  );
}
```

## sharp를 왜 추가했나

`next/image`는 서버에서 이미지를 리사이즈·포맷 변환(webp/avif)해서 내려준다. 이때 프로덕션에서 이 변환을 담당하는 게 `sharp`다. 설치돼 있지 않으면 Next가 훨씬 느린 순수 JS 변환으로 폴백하거나 최적화 자체가 불안정해진다. SSR로 옮기면서 이미지 최적화 경로가 서버로 확실히 들어오게 되므로, `sharp`를 명시적으로 의존성에 추가했다.

> 💡 `next/image` + SSR 조합에서 프로덕션 이미지 변환이 느리다면 `sharp`가 설치돼 있는지부터 보자. blur placeholder도 결국 이 변환 파이프라인 위에서 돈다.

## 정리

- landing처럼 "첫 화면이 곧 콘텐츠"인 페이지는 SSR이 유리하다. 이벤트 로직 하나 때문에 `'use client'`가 붙어 있었다면 그 로직만 떼어내면 서버 컴포넌트로 돌릴 수 있다.
- CLS는 (1) `Suspense` fallback이 자리를 잡고, (2) 컨테이너 `minHeight`로 초기 높이를 확보하고, (3) 이미지 blur placeholder로 로드 전 자리를 유지하는 삼단으로 막는다.
- 반대로 무조건 SSR이 답은 아니다. 홈 광고 배너처럼 유저·시점마다 달라지는 데이터는 오히려 CSR로 빼는 게 맞을 때도 있다.

## 관련 작업

- sharp추가, 오토캐시백 main container CLS관련 수정 — landing 페이지 SSR로 변경, 최소높이 추가, 내부 이벤트를 계산기 섹션으로 이동
- 리스/렌트/아티클 각 홈 화면에 `minHeight: '100dvh'` 추가
- 홈광고배너 API fetch위치 SSR → CSR 전환 (반대 방향 사례)
- promotion list/detail 폴더 분리 — SSR 적용되도록 파일 구조 변경
