---
title: "확장 가능한 Analytics 이벤트 아키텍처"
date: 2026-06-23
categories: ["Architecture"]
tags: ["Analytics", "Airbridge", "GA4", "Notifly", "React"]
---

> 이 글은 '프론트엔드 아키텍처 패턴' 시리즈의 한 편이다.

## 들어가며

이벤트 로깅은 처음엔 참 쉬워 보인다. 버튼 클릭할 때 `track('click')` 한 줄 넣으면 되니까. 그런데 우리 서비스는 마케팅 어트리뷰션은 Airbridge, 제품 분석은 GA4, 앱 푸시/CRM은 Notifly… 이렇게 SDK가 하나둘 늘어났다. 그러다 보니 화면 곳곳에 이런 코드가 복붙되기 시작했다.

```tsx
const events: IEventItem[] = [
  { type: 'airbridge', eventName, eventData },
  { type: 'notifly', eventName, eventData },
  { type: 'ga', eventName, eventData },
];
sendEvent(events);
```

똑같은 배열을 화면마다 다시 쓰고 있었다. SDK 하나 추가되면? 이 배열을 쓰는 모든 파일을 다 찾아 고쳐야 한다. 띠용..

그래서 **여러 애널리틱스 SDK를 하나의 이벤트 레이어로 추상화**하는 작업을 진행했다. 이 글은 그 설계 이야기다.

## 문제: SDK마다 다른 전송 방식

각 SDK는 요구하는 데이터 형태가 다르다.

- **Airbridge**: `action`, `label`, `value`는 최상위 필드로, 나머지는 `customAttributes`로 넣어야 한다.
- **GA4**: `gtag('event', action, {...})` 형태.
- **Notifly**: `notifly.trackEvent(name, data)`, 게다가 **웹에서는 동작하지 않는다**(앱 웹뷰 전용).

이걸 화면 컴포넌트가 하나하나 알고 있어야 한다면, 이벤트 하나 붙일 때마다 SDK 3개의 스펙을 다 신경 써야 한다. 관심사가 완전히 잘못 새어 나온 상태였다.

## 설계: 단일 진입점 + 타입별 어댑터

핵심 아이디어는 두 가지다.

1. 화면은 **"무슨 이벤트를, 어떤 데이터로"**만 말한다.
2. **"어느 SDK에 어떻게 보낼지"**는 레이어 안쪽 어댑터가 책임진다.

이벤트 항목의 인터페이스를 이렇게 정의했다.

```tsx
export interface IEventItem {
  type: 'airbridge' | 'ga' | 'notifly' | 'picky';
  eventName: string;
  eventData: EVENT_DATA;
}
```

그리고 단일 진입점 `sendEvent`가 `type`에 따라 알맞은 어댑터로 분기한다.

```tsx
import { gtagSendEvent } from '@shared/GA/ga';
import { sendAirBridge } from './airbridge';
import { sendNotiflyEvent } from './notifly';

export function sendEvent(eventList: IEventItem[]) {
  try {
    eventList.forEach(({ type, eventName, eventData }) => {
      switch (type) {
        case 'airbridge':
          sendAirBridge(eventName, eventData);
          break;
        case 'ga':
          gtagSendEvent({ action: eventName, rest: eventData });
          break;
        case 'notifly':
          // sendNotiflyEvent는 async라 rejection이 이 동기 try/catch엔 안 잡힌다 → .catch()로 따로 처리
          sendNotiflyEvent(eventName, eventData).catch(console.error);
          break;
        default:
          break;
      }
    });
  } catch (err) {
    // XXX: sentry 추가 후 로그설정 보완 필요
    console.error(err);
  }
}
```

각 어댑터는 자기 SDK의 스펙만 안다. Airbridge 어댑터를 보면 Airbridge가 원하는 body 모양으로 가공하는 책임이 여기 갇혀 있다.

```tsx
/**
 * Airbridge에 보낼 데이터를 가공하고 요청한다.
 */
export function sendAirBridge(eventName: string, eventData: EVENT_DATA) {
  if (process.env.NEXT_PUBLIC_ENV !== 'pro') return;
  if (!eventName) return;

  if (Array.isArray(eventData.airbridge)) {
    eventData.airbridge.forEach(item => {
      Airbridge.trackEvent(eventName, getAirbridgeBody(item));
    });
  } else if ('airbridge' in eventData && eventData.airbridge) {
    Airbridge.trackEvent(eventName, getAirbridgeBody(eventData.airbridge));
  } else if (!isEmpty(eventData)) {
    Airbridge.trackEvent(eventName, getAirbridgeBody(eventData));
  }
}

// action/label/value는 최상위로, 나머지는 customAttributes로
function getAirbridgeBody(eventData: AIRBRIDGE_EVENT_DATA) {
  return {
    ...(eventData.action && { action: eventData.action }),
    ...(eventData.label && { label: eventData.label }),
    ...(eventData.value && { value: eventData.value }),
    customAttributes: { ...eventData },
  };
}
```

Notifly 어댑터는 특히 "웹에서는 안 돌아간다"는 SDK의 제약을 안쪽에 숨긴다. 프로덕션 환경에서만, 이벤트명이 있을 때만 전송한다.

```tsx
import notifly from 'notifly-js-sdk';

/**
 * Notifly에 로그를 보낸다. Notifly는 웹에서는 동작하지 않는다.
 */
export async function sendNotiflyEvent(eventName: string, eventData: object) {
  if (process.env.NEXT_PUBLIC_ENV !== 'pro') return;
  if (!eventName) return;

  notifly.trackEvent(eventName, eventData);
}
```

> 💡 어댑터 안쪽에 `NEXT_PUBLIC_ENV !== 'pro'` 가드를 두면, 화면 코드는 "지금 프로덕션인가?"를 신경 쓸 필요가 없다. 개발 환경에서 실 이벤트가 새어 나가는 사고도 막힌다.

## 반복 제거: sendAllTypeEvent 헬퍼

대부분의 이벤트는 "전 채널로 다 보내라"였다. 그래서 화면마다 3줄짜리 배열을 다시 쓰고 있었는데, 배너 섹션을 리팩토링하면서 이 중복을 **모듈 헬퍼로 추출**했다.

```tsx
export function sendAllTypeEvent(eventName: string, eventData: any) {
  const events: IEventItem[] = [
    { type: 'airbridge', eventName, eventData },
    { type: 'notifly', eventName, eventData },
    { type: 'ga', eventName, eventData },
  ];
  sendEvent(events);
}
```

이제 화면은 이렇게 한 줄이면 된다.

```tsx
sendAllTypeEvent('home_article_click', { action: '아티클 클릭' });
```

그런데 여기서 문제가 하나 더 나왔다. 어떤 이벤트는 "Airbridge랑 GA만, Notifly는 빼고" 보내야 했다(로그인 완료 같은 앱 전용 이벤트 이슈). 그래서 헬퍼를 **기본은 전 채널, 필요하면 대상 채널 배열로 좁힐 수 있게** 확장했다.

```tsx
export type EventType = 'airbridge' | 'notifly' | 'ga';

export function sendAllTypeEvent(
  eventName: string,
  eventData: any,
  targets: EventType[] = ['airbridge', 'ga', 'notifly'],
) {
  const events: IEventItem[] = targets.map(type => ({
    type,
    eventName,
    eventData,
  }));
  sendEvent(events);
}
```

호출부는 이렇게 자연스러워진다.

```tsx
// 전 채널로
sendAllTypeEvent('view_lease', eventData);

// 특정 채널만
sendAllTypeEvent('login_complete', eventData, ['airbridge', 'ga']);
```

기본값을 전 채널로 둔 게 포인트다. 대부분의 호출부는 세 번째 인자를 몰라도 되고, 예외 케이스만 명시적으로 채널을 좁힌다.

## 이벤트명은 반드시 상수에서

레이어를 잘 만들어놔도, 호출부에서 `sendAllTypeEvent('community_post_detail_click', ...)` 처럼 문자열을 그때그때 손으로 쓰면 오타 한 방에 데이터가 새 이벤트로 잘못 잡힌다. 실제로 커뮤니티 상세에서 하드코딩된 이벤트명이 흩어져 있었고, 이걸 **정의된 상수를 쓰도록** 싹 정리했다.

```tsx
import { COMMUNITY_EVENT_NAME } from '@shared/utils/constant/event';

sendAllTypeEvent(
  COMMUNITY_EVENT_NAME.community_post_detail_click,
  { ...eventData, action: '투표 참여하기' },
  ['airbridge', 'ga'],
);
```

> 이벤트명을 상수 객체(`XXX_EVENT_NAME`)로 모아두면 데이터팀의 수집 문서와 코드가 1:1로 맞아떨어진다. 자동완성도 되고, 오타로 인한 유령 이벤트도 사라진다.

## 중복 이벤트와의 싸움

멀티 채널 레이어가 완성되고 나서 진짜 골치 아픈 건 따로 있었다. **같은 이벤트가 두 번 찍히는 문제.** 특히 view 계열 이벤트가 그랬다.

원인은 이전 URL을 구독하는 로직이었다. 이전 페이지를 알아야 `prevScreen`을 채우는데, 이 값이 처음엔 `null`로 시작한다. 그런데 `useEffect`가 `null`일 때 한 번, 값이 채워지고 또 한 번 도는 바람에 view 이벤트가 중복 발화됐다.

해결은 단순하다. **이전 URL이 확정되기 전엔 전송하지 않는다.**

```tsx
useEffect(() => {
  if (prevUrl !== null) {
    const eventName = ARTICLE_EVENT_NAME.view_article;
    const eventData = {
      from: searchParams.get('from'),
      screen: '아티클 상세',
      prevScreen: getPageTypeFromUrl(prevUrl),
      articleId,
      label: articleTitle,
    };

    sendEvent([
      { type: 'airbridge', eventName, eventData },
      { type: 'notifly', eventName, eventData },
      { type: 'ga', eventName, eventData },
    ]);
  }
}, [prevUrl, searchParams]);
```

여기에 더해 `prevScreen`을 계산하는 `getPageTypeFromUrl`도 손봤다. 원래 `url.includes('articles')` 같은 부분 문자열 매칭이었는데, 이러면 `/lease-articles` 같은 경로가 엉뚱하게 잡힌다. **정규표현식으로 경로 시작을 정확히 매칭**하도록 바꿨다.

```tsx
const ARTICLE_Regex = /^\/articles(?:\/|$)/;
const LEASE_Regex = /^\/lease(?:\/|$)/;
const RENT_Regex = /^\/rent(?:\/|$)/;
const AUTO_CASHBACK_Regex = /^\/auto-cashback(?:\/|$)/;

export const getPageTypeFromUrl = (url: string | null): string => {
  if (url === null) return '';
  if (LEASE_Regex.test(url)) return '리스';
  if (RENT_Regex.test(url)) return '장기렌트';
  if (AUTO_CASHBACK_Regex.test(url)) return '오토캐시백';
  if (ARTICLE_Regex.test(url)) return '아티클';
  return '';
};
```

`includes` → 정규식 매칭으로 바꾸니 잘못된 화면 분류 때문에 생기던 데이터 오염도 같이 잡혔다.

## 정리

정리하면 이 아키텍처는 세 겹이다.

```
화면 컴포넌트
   │  sendAllTypeEvent(NAME.xxx, data, targets?)
   ▼
이벤트 레이어  (sendEvent: type별 분기)
   │
   ├─ airbridge 어댑터  (customAttributes 가공)
   ├─ ga 어댑터         (gtag)
   └─ notifly 어댑터    (앱 전용, env 가드)
```

- 화면은 **이벤트명 상수 + 데이터**만 신경 쓴다.
- SDK가 늘어도 어댑터 하나만 추가하고 `switch`에 한 줄 붙이면 끝. 화면 코드는 안 건드린다.
- 전송 대상 채널은 헬퍼 인자로 유연하게 좁힌다.
- 오타·중복은 상수화와 발화 조건 정리로 막는다.

이벤트 로깅은 "한 줄 넣으면 되는 일"이 아니라, 시간이 지날수록 SDK와 화면이 곱으로 늘어나는 영역이다. 레이어 하나 잘 세워두면 나중에 훨씬 편하다.

## 관련 작업

- Picky/airbridge event function 추가, GA4·notifly event 전송 추가, 이벤트 중복 발생 수정, 정규표현식을 사용한 패턴 매칭 추가, 아티클 상세 중복 이벤트 로그 방지코드 추가
- Banner section 리팩토링 — 반복되는 `sendAllTypeEvent`를 모듈 헬퍼로 추출
- `sendAllTypeEvent` 수정 — 기본으로 all type을 보내되 마지막 params에 타입 배열로 대상 채널 지정 가능
- 정의된 이벤트명(상수) 사용하도록 수정, 커뮤니티 상세 이벤트 정리
