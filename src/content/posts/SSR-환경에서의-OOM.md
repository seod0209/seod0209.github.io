---
title: "SSR 환경에서의 OOM - 서버가 메모리를 먹는 이유"
date: 2025-06-26
categories: ["React"]
tags: ["SSR", "Next.js", "메모리", "OOM", "ISR"]
---

> 시리즈 'React 성능·메모리' 5편. 앞 편들이 브라우저(클라이언트) 메모리였다면, 이번엔 서버(SSR) 메모리다. 같은 React인데 서버에서 OOM이 나는 이유는 결이 다르다.

클라이언트 메모리 누수는 "한 사용자의 탭"에서 일어난다. 그런데 SSR 서버는 **모든 사용자의 요청을 하나의 프로세스가 처리**한다. 그래서 요청 하나가 조금 새면, 그게 초당 수십·수백 요청으로 곱해져 서버 프로세스가 통째로 OOM으로 죽는다. 클라이언트에선 새로고침이 리셋이지만, 서버는 리셋이 곧 장애다.

## 왜 하필 Node.js 프로세스에서 터지나

질문은 두 층위로 갈라서 봐야 한다. **"왜 Node에서?"(무대)** 와 **"왜 OOM?"(원인)** 은 서로 부정하는 게 아니라 겹쳐 있다.

| 질문 | 답 | 층위 |
| --- | --- | --- |
| 왜 하필 Node인가 | SSR·ISR·RSC가 **서버(한 프로세스)** 에서 돈다. 브라우저면 탭 하나만 죽지만 Node는 **프로세스 전체**가 죽어 전원이 장애. | 무대 |
| 왜 OOM인가 | 요청이 끝나도 참조가 안 풀려 V8 **old space가 우상향**하다 상한을 넘긴다. | 원인 |

즉 **"React가 Node에 올라가서"도 맞고 "참조가 안 풀려서"도 맞다.** 앞이 무대, 뒤가 방아쇠다. Node라는 공유 프로세스 위에서 참조 누수가 나면 치명적이 된다는 게 핵심. (우리 파드는 2GB 제한, Node heap은 그 75%인 1536MB로 잡혀 있다.)

### 그런데 "요청 스코프를 넘긴 참조"가 다 누수는 아니다

같은 "안 풀린 참조"처럼 보여도 성격이 갈린다.

- **진짜 누수 (unbounded)** — 트래픽이 멈춰도 힙이 안 내려간다. 키가 계속 느는데 eviction이 없는 것들.
  - ISR 인메모리 캐시 무한 증가
  - 서버 전역 / query client 캐시 (모듈 스코프 = 프로세스 생명주기)
- **일시 점유 (bounded)** — 요청이 끝나면 GC로 내려간다. 다만 동시 요청이 몰리면 순간 피크가 상한을 넘는다.
  - SSR pending Promise (요청 단위로 살았다 죽음)
  - 렌더 단계 throw (정리 로직을 못 타 연결/스트림이 잠깐 남음, 에러 빈도에 비례)

핵심 차이는 하나다 — **트래픽이 멈췄을 때 힙이 내려오느냐.** 안 내려오면 unbounded(캐시/전역), 내려오면 bounded(동시성). 진단도 처방도 다르다. 아래 네 전형을 이 두 버킷으로 나눠 본다.

## SSR 서버에서 메모리가 새는 전형들

### 1. 요청 스코프를 벗어난 전역 상태 — 진짜 누수(unbounded)

서버는 모듈이 한 번 로드되면 프로세스가 살아있는 내내 유지된다. 그래서 모듈 최상단(전역)에 요청별 데이터를 쌓으면 절대 안 된다.

```tsx
// 위험: 모듈 전역 캐시가 요청마다 자란다 (프로세스 수명 내내 유지)
const cache = new Map();

export async function getData(userId: string) {
  if (!cache.has(userId)) {
    cache.set(userId, await fetchUser(userId)); // 유저 수만큼 무한 증가 → OOM
  }
  return cache.get(userId);
}
```

이런 캐시는 **반드시 크기 상한(LRU)이나 TTL**이 있어야 한다. 상한 없는 `Map`은 SSR에서 시한폭탄이다.

### 2. 브라우저 전용 코드를 서버에서 실행 — 일시 점유(bounded)

서버엔 `window`, `document`, `localStorage`가 없다. 이걸 SSR 경로에서 건드리면 에러이거나, 방어 코드가 어설프면 pending Promise로 매달려 메모리를 잡는다. 실제로 SSR 환경에서 토큰 갱신을 그냥 두면 문제가 됐다.

```tsx
// SSR은 서버에서 실행됨 → 브라우저 쿠키/로컬스토리지 접근 불가
// 타임아웃이 없으면 Promise가 영원히 pending → 참조가 안 풀림
if (typeof window === 'undefined') {
  return skipTokenRefresh(); // 서버에선 갱신 시도 자체를 스킵
}
```

`typeof window === 'undefined'`로 서버/클라이언트 분기하고, 네트워크가 걸리는 곳엔 반드시 타임아웃을 둔다. **영원히 pending인 Promise는 그 클로저 스코프 전체를 붙잡는 누수다.**

### 3. ISR 인메모리 캐시가 부풀 때 — 진짜 누수(unbounded)

Next.js는 ISR(Incremental Static Regeneration) 결과를 서버 인메모리에 캐시한다. 페이지·경로가 많고 각 페이지 결과가 크면 이 캐시가 커져서 서버 메모리를 압박한다. 여기서 우리가 실제로 겪은 튜닝 히스토리가 있다.

처음엔 실험적 기능을 정리하면서 인메모리 ISR 캐시를 **아예 끄는(0)** 선택을 했다. 메모리 안정성이 먼저였기 때문이다.

```js
// next.config.js — 1차: 안정성 우선, 인메모리 ISR 캐시 비활성화
experimental: {
  isrMemoryCacheSize: 0, // 서버 메모리에 ISR 결과를 안 쌓음
  // reactCompiler: true, // 실험적 기능 비활성화
  optimizeCss: true,
},
```

그런데 캐시를 0으로 두면 매 요청이 디스크/재생성 경로를 타서 응답 지연이 생긴다. 그래서 이후에 **무한이 아니라 상한 있는 캐시**로 다시 열었다.

```js
// next.config.js — 2차: 무제한이 아니라 상한을 둔 캐시로 전환
experimental: {
  isrMemoryCacheSize: 50 * 1024 * 1024, // 50MB 상한
  optimizeCss: true,
  optimizePackageImports: ['@shared', '@entities', '@views', '@widgets', '@features'],
},
```

교훈은 1편·4편과 똑같다. **"끄기"도 "무제한"도 아니고, 상한을 둔다.** 서버 캐시는 성능(재사용)과 메모리(상한) 사이의 트레이드오프이고, 정답은 대부분 "적당한 bound".

### 4. 렌더 단계 예외 / 무한 루프 — 대체로 일시 점유(bounded)

렌더 단계에서 예외가 나거나 무한 재귀가 돌면 서버 워커가 CPU·메모리를 물고 늘어진다. 예를 들어 `useMemo`(렌더 단계)에서 방어 안 된 접근이 throw되면 렌더가 실패하고, 그 처리 경로가 반복되면 서버가 불안정해진다.

```tsx
// 위험: actions가 없으면 렌더 단계(useMemo)에서 throw → 렌더 실패
const primary = useMemo(() => actions.find((a) => a.type === 'PRIMARY'), [actions]);

// 방어: 옵셔널 체이닝으로 렌더 단계 예외 차단
const primary = useMemo(() => actions?.find((a) => a.type === 'PRIMARY'), [actions]);
```

렌더 단계에서 던지는 예외는 클라이언트에선 그 컴포넌트만 깨지지만, SSR에선 그 요청의 HTML 생성 전체가 실패한다. 서버에선 렌더 단계 안전성이 곧 가용성이다.

## SSR 메모리를 지키는 체크리스트

- 모듈 전역에 요청별 데이터를 쌓지 않는다. 캐시는 **LRU/TTL로 상한**.
- 브라우저 전용 API는 `typeof window === 'undefined'`로 분기하고, 네트워크엔 **타임아웃**.
- ISR/데이터 캐시는 끄기(0)도 무제한도 아닌 **bounded size**로.
- 렌더 단계(`useMemo`, 컴포넌트 본문)에서 예외가 안 나게 방어한다. SSR에선 렌더 예외 = 요청 실패.
- 서버 프로세스 메모리를 모니터링해서 "요청 수와 무관하게 평평한가"를 본다. 우상향하면 요청 스코프를 벗어난 참조가 있는 것.

> 💡 클라이언트 OOM은 한 명이 겪지만, SSR OOM은 전원이 겪는다. 그래서 서버에선 "이 참조가 요청이 끝나면 확실히 풀리나?"를 항상 먼저 묻는다.

## 어떻게 봤나, 뭐가 실패였나

원인을 눈으로 잡으려면 **재현 + 관측**이 필요했다. 팀에 부하·모니터링 스택이 있다 — k6로 가상 사용자 부하를 주고(0→10→50→100명), Prometheus가 메트릭을 모으고, Grafana 대시보드로 본다. 핵심 지표는 `nodejs_heap_size_used_bytes` 그래프 모양이다.

- **톱니(sawtooth)** = 정상: 힙이 올랐다 GC로 뚝 떨어져 베이스라인 복귀.
- **톱니 없이 우상향** = **누수(unbounded)**: GC 후에도 베이스라인이 계속 올라감. 캐시·전역을 의심.
- **피크만 튀고 골짜기는 평평** = **동시성 문제(bounded)**: 요청이 몰릴 때만 솟구침. 상한을 올리거나 concurrency를 제한.

계단이 나오는 페이지·경로를 좁혀 가며 위의 원인들을 하나씩 짚었다. 이 과정에서 실패하거나 되돌린 시도도 있었다.

<figure>
  <img src="/assets/ssr-oom-memory-leak-graph.png" alt="중고차 웹 Memory Usage 그래프 — 파드마다 600MB limit까지 우상향하다 재시작으로 급락하는 계단형" width="100%" />
  <figcaption>실제 그래프. <code>중고차 웹</code>의 Memory Usage(최근 7일). 파드별 컨테이너 메모리가 ~600MB limit(점선)까지 <strong>톱니 없이 우상향</strong>하다, limit에 닿으면 재시작으로 뚝 떨어지고 새 파드가 다시 바닥부터 오른다. "우상향 후 리셋" = 전형적 누수 시그니처.</figcaption>
</figure>


- **ISR 인메모리 캐시를 아예 끔(`isrMemoryCacheSize: 0`)** → 메모리는 잡혔지만 매 요청이 재생성 경로를 타 **응답이 느려졌다.** 실패로 보고 50MB 상한으로 되돌림.
- **Node 힙 상한을 올리고(`--max-old-space-size=1536`) GC를 튜닝** → OOM Kill 빈도는 줄었지만 이건 **근본 해결이 아니라 시간벌기**다. 누수 자체를 안 고치면 더 큰 양동이일 뿐, 언젠가 넘친다.
- **React Compiler(실험 기능) 켬** → 불안정해서 도로 껐다.

> 💡 heap 상한을 키우는 건 양동이를 키우는 것이지 구멍을 막는 게 아니다. 그래프가 계단이면 양동이 크기와 무관하게 결국 넘친다. 그래서 "톱니냐 계단이냐"부터 본다.

## 관련 작업

- 실험적 기능 비활성화 — React Compiler 비활성화, ISR 인메모리 캐시 비활성화(isrMemoryCacheSize: 0), staleTimes 제거
- isrMemoryCacheSize: 0 제거(50MB로 상향), splitChunks 단순화
- SSR환경에서 토큰갱신 스킵 — 서버에선 쿠키/로컬스토리지 접근 불가, 타임아웃 없으면 Promise가 영원히 pending
- actions에 옵셔널 체이닝 추가 — API 응답 누락 시 useMemo(렌더 단계)에서 throw → 렌더 실패 방지
- 안드로이드 인앱 suspend현상으로 인한 SSR오류 개선
- 부하·모니터링 스택(k6 · Prometheus · Grafana `nextjs-memory` 대시보드)과 Node 힙/GC 튜닝(`--max-old-space-size=1536`, `--max-semi-space-size`)은 동료가 구축했다. 이 글의 관측은 그 위에서 했고, 위 앱 레벨 원인 규명·수정이 내 몫이었다.
