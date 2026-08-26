---
title: "React 재렌더링과 함수 재할당이 OOM으로 이어지기까지"
date: 2025-09-11
categories: ["React"]
tags: ["성능", "메모리", "useMemo", "재렌더링"]
---

> 시리즈 'React 성능·메모리' 2편. 오늘 한 일 노트를 정리하며, "재렌더링 → 함수/객체 재할당 → 메모리 압박"의 연결고리를 따라가 본다.

오늘 이벤트 로깅 쪽을 손보다가 문득 "이거 왜 매번 이벤트가 두 번 찍히지?"에서 시작해서, 결국 "왜 이 컴포넌트가 이렇게 자주 리렌더되지?"까지 파고들었다. 처음엔 성능 얘기였는데 파다 보니 메모리 얘기로 이어졌다. 오늘 정리한 사고 흐름을 그대로 적어둔다.

## 재렌더링이란 무엇을 다시 하는가

리렌더링은 DOM을 통째로 다시 그리는 게 아니다. 함수 컴포넌트가 **다시 호출되는 것**이다. 다시 호출되면 그 안의 모든 것이 새로 만들어진다.

```tsx
function Component({ data }) {
  // 리렌더될 때마다 아래 전부 "새로" 생성된다
  const handleClick = () => doSomething(data); // 새 함수 객체
  const config = { id: data.id, label: data.title }; // 새 객체
  return <Child onClick={handleClick} config={config} />;
}
```

`handleClick`도, `config`도 렌더마다 **주소가 다른 새 값**이다. 값은 같아 보여도 참조(reference)가 다르다. 이게 성능·메모리 두 관점에서 다 문제가 된다.

## 함수/객체 재할당이 만드는 나비효과

### 1. 자식의 불필요한 리렌더

`React.memo`로 감싼 자식이라도, props의 참조가 매번 바뀌면 memo는 무력화된다. `handleClick`이 매번 새 함수면 자식은 "props 바뀌었네" 하고 또 렌더한다.

### 2. `useEffect`가 매번 재실행

더 골치 아픈 건 의존성 배열이다. 새로 만든 객체를 deps에 넣으면 effect가 렌더마다 다시 돈다.

```tsx
const eventData = { promotionId: data?.key, label: data?.title };

useEffect(() => {
  sendEvent(eventName, eventData);
}, [eventData]); // eventData가 매 렌더 새 객체 → effect 무한에 가깝게 재실행
```

이벤트가 두 번, 세 번 찍히던 원인이 바로 이거였다. `eventData`는 내용이 같아도 매번 새 객체라 `[eventData]`가 항상 "바뀐 것"으로 판정된다.

### 3. 여기서 메모리로 번진다

effect가 매번 돌면서 그 안에서 타이머·리스너·구독을 만들거나, 매 렌더마다 새 클로저가 이전 스코프를 붙잡고 있으면, GC가 회수하지 못한 참조가 쌓인다. 리스트가 길거나 화면 전환이 잦은 페이지에서 이게 누적되면 결국 메모리가 계속 우상향하고, 심하면 OOM(Out Of Memory)까지 간다. **한 번의 재할당은 싸지만, "매 렌더 × 항목 수 × 체류 시간"으로 곱해지면 싸지 않다.**

## 해결: 참조를 안정화한다 (useMemo)

기획전 상세 페이지에서 실제로 이 패턴을 정리했다. 이벤트 데이터 객체를 `useMemo`로 묶어 `data`가 바뀔 때만 새로 만들도록 했다.

```tsx
// Before: 렌더마다 새 객체, effect가 searchParams/data 참조로 계속 재실행
useEffect(() => {
  const eventData = {
    screen: '기획전 상세',
    action: '기획전 상세 조회',
    promotionId: data?.key,
    payType: data?.buyTypes.join(','),
    isNew: data?.openAt ? isNewWithin7Days(data.openAt) : false,
    promotionStatus: data?.status,
    label: data?.title,
  };
  sendAllTypeEvent(eventName, eventData);
}, [searchParams, data]);
```

```tsx
// After: 객체 생성을 useMemo로 격리 → 참조 안정화
const promotionDetailEventData = useMemo(
  () => ({
    promotionId: data?.key,
    payType: data?.buyTypes.join(','),
    isNew: data?.openAt ? isNewWithin7Days(data.openAt) : false,
    promotionStatus: data?.status,
    label: data?.title,
  }),
  [data],
);

useEffect(() => {
  const eventData = {
    from: searchParams.get('from'),
    screen: '기획전 상세',
    action: '기획전 상세 조회',
    ...promotionDetailEventData,
  };
  sendAllTypeEvent(eventName, eventData);
}, [searchParams, promotionDetailEventData]);
```

포인트:
- deps를 `data`(전체 객체)에서 `promotionDetailEventData`(useMemo 산출물)로 바꿨다. 이제 `data`의 참조가 흔들려도 실제 사용하는 필드가 그대로면 effect는 다시 돌지 않는다.
- 이 메모된 객체는 공유하기 버튼의 `additionalEventData`로도 재사용된다. 같은 참조를 여러 소비처가 나눠 쓰니 생성 비용과 참조 불일치를 동시에 줄인다.

```tsx
<ShareButton
  screen="기획전 상세"
  customEventName="promotion_detail_click"
  additionalEventData={promotionDetailEventData}
/>
```

## 오늘의 결론

- 리렌더는 함수 컴포넌트를 "다시 호출"하는 것이고, 그 안의 함수·객체는 전부 새로 만들어진다.
- 새 참조가 `memo`를 뚫고, `useEffect` deps를 흔들고, 그게 곱해지면 메모리로 번진다.
- 그래서 "이 객체/함수의 참조를 안정시켜야 하는가?"를 먼저 묻는다. 답이 yes면 `useMemo`/`useCallback`. 특히 **effect deps에 들어가는 객체**는 참조 안정화 1순위 후보다.
- 다만 무지성 memoize는 또 다른 문제(다음 편에서 다룬다)를 부른다. 참고 자료를 뒤져봐도 결론은 늘 "측정하고, 참조가 실제로 문제를 일으키는 곳만 잡아라"로 수렴한다.

## 관련 작업

- promotionDetailEventData를 useMemo로 묶어 오브젝트 재생성 방지, 공유하기 클릭시 promotion_detail_click 추가
- view_event 의존성 배열 요소 변경 — searchParams.get('from')에 의존하도록 변경 (deps로 인한 이벤트 오작동 사례)
