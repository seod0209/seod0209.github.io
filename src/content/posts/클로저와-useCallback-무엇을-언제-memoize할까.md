---
title: "클로저와 useCallback: 무엇을 언제 memoize할까"
date: 2025-06-25
categories: ["React"]
tags: ["useCallback", "useMemo", "메모이제이션", "성능"]
---

> 시리즈 'React 성능·메모리' 4편. 3편(클로저의 함정)의 심화. 이번엔 "그래서 뭘 memoize하고 뭘 하지 말까"를 실제 사례로 판단 기준을 세운다.

memoize는 공짜가 아니다. `useMemo`/`useCallback`도 값을 캐시하고 deps를 매 렌더 비교하는 비용이 든다. 그래서 "일단 다 감싸"는 최적화가 아니라 오히려 **코드를 복잡하게 만들고 메모리를 더 쓰는** 안티패턴이 되기 쉽다. 실제로 우리 코드에서 memoize를 넣었다 다시 뺀 적도 있다. 그 판단들을 정리한다.

## 먼저: memoize가 실제로 효과를 내는 조건

`useMemo`/`useCallback`은 **참조 동일성(referential equality)이 누군가에게 중요할 때만** 의미가 있다. "누군가"는 셋 중 하나다.

1. `React.memo`로 감싼 자식의 props로 내려갈 때
2. 다른 훅의 **deps 배열**에 들어갈 때 (`useEffect`, `useMemo`, `useCallback`)
3. 계산 자체가 정말 무거울 때 (`useMemo` 한정)

이 셋 중 어디에도 해당 안 되면 memoize는 순수 오버헤드다.

```tsx
// 무의미: label은 자식 memo/deps에 안 쓰이고 계산도 가볍다
const label = useMemo(() => `${data.title} (${data.status})`, [data]);
// 그냥 이게 낫다
const label = `${data.title} (${data.status})`;
```

## 실제로 memoize를 "제거"한 케이스

뷰포트 리스트 훅에서 `processedItems`를 `useMemo`로 감싸고 있었는데, 이걸 걷어냈다.

```tsx
// Before: useMemo로 감쌈
const processedItems: VisibleItem<T>[] = useMemo(
  () =>
    items.map((item, index) => ({
      item,
      index,
      isVisible: visibleItems.has(index),
    })),
  [items, visibleItems],
);
```

```tsx
// After: 그냥 계산
const processedItems: VisibleItem<T>[] = items.map((item, index) => ({
  item,
  index,
  isVisible: visibleItems.has(index),
}));
```

왜 뺐나? `visibleItems`는 스크롤할 때마다 바뀐다. 즉 deps가 거의 매 렌더 바뀌니 `useMemo`가 캐시를 재사용하는 일이 거의 없다. **재사용률이 0에 가까운 memoize는 캐시 + deps 비교 비용만 더하고 이득이 없다.** 게다가 이 배열은 대부분 그 자리에서 바로 `.map`으로 렌더에 쓰여 소비된다. 참조 안정성이 아무에게도 필요 없었다.

> 💡 판단 질문: "이 memoize의 deps가 얼마나 자주 바뀌나?" 거의 매번 바뀐다면 memoize는 대체로 손해다.

## 반대로: memoize가 정답이었던 케이스

3편에서 본 이벤트 데이터 객체는 memoize가 맞았다.

```tsx
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

// (1) effect deps로 쓰이고 (2) 자식 컴포넌트 props로도 내려간다 → 참조 안정화 이득 명확
useEffect(() => {
  sendAllTypeEvent(eventName, { ...promotionDetailEventData });
}, [searchParams, promotionDetailEventData]);
```

차이가 뭔가? 여기선 deps(`data`)가 자주 안 바뀌고, 결과 객체가 **effect deps + 자식 props** 두 소비처로 흘러간다. 위의 "제거" 사례와 정확히 반대 조건이다.

## useCallback: 언제 감싸나

`useCallback(fn, deps)`는 `useMemo(() => fn, deps)`의 축약이다. 함수 참조를 안정화한다. 감싸야 할 때는 딱 하나: **그 함수가 memo된 자식이나 effect/훅 deps로 내려갈 때.**

리스트 아이템을 `React.memo`로 감쌌다면, 부모가 내려주는 콜백도 안정돼야 memo가 산다.

```tsx
// 자식: React.memo
const ArticleListItem = memo(
  ({ index, article, onSendEvent }: ArticleListItemProps) => {
    const handleClick = () => onSendEvent(article.categoryKo, article.title);
    return (
      <li>
        <Link href={`/articles/${article.titleId}`} onClick={handleClick}>
          {/* ... */}
        </Link>
      </li>
    );
  },
);

// 부모: 콜백을 안정화해야 memo가 의미 있음
const handleSendEvent = useCallback((category: string, title: string) => {
  sendEvent('article_click', { category, title });
}, []);

return items.map((article, i) => (
  <ArticleListItem key={article.titleId} index={i + 1} article={article} onSendEvent={handleSendEvent} />
));
```

여기서 콜백 시그니처를 `handleSendEvent: () => void`(아이템마다 다른 클로저)에서 `onSendEvent: (category, title) => void`(하나의 안정된 함수 + 인자로 구분)로 바꾼 게 핵심이다. **아이템마다 다른 클로저를 만들면 memo가 다 깨진다.** 인자로 넘기면 콜백 하나를 전 아이템이 공유한다 → 참조 안정 + 클로저 N개가 아니라 1개.

## 클로저를 피하는 대안: ref 패턴

콜백이 자주 바뀌는 값을 참조해야 하는데 참조는 고정하고 싶다면, deps에 넣는 대신 ref로 최신값을 읽는다.

```tsx
const onChangeRef = useRef(onChange);
onChangeRef.current = onChange; // 매 렌더 최신화

const stableHandler = useCallback(() => {
  onChangeRef.current(); // 항상 최신, 그런데 stableHandler 참조는 고정
}, []);
```

이건 useCallback deps 지옥(`[a, b, c, d...]`)을 피하면서 stale closure도 막는다. 다만 남발하면 데이터 흐름이 안 보이니, "이 콜백이 정말 effect/observer에 재등록 문제를 일으킬 때"로 한정한다.

## 결정 트리로 요약

```text
이 값(함수/객체)의 참조가 안정돼야 하는 소비처가 있나?
├─ 아니오 → memoize 하지 마라 (그냥 계산)
└─ 예 (memo 자식 / 훅 deps / 무거운 계산)
   └─ deps가 얼마나 자주 바뀌나?
      ├─ 거의 매번 → memoize 이득 거의 없음. 재검토
      └─ 가끔 → memoize 적합 (useMemo/useCallback)
         └─ 자주 바뀌는 값을 참조해야 하나?
            └─ 예 → ref 미러링으로 참조 고정 + 최신값 유지
```

무지성 memoize도, 무지성 제거도 답이 아니다. "누가 이 참조를 필요로 하나 / deps가 얼마나 자주 바뀌나"만 물으면 대부분 답이 나온다.

## 관련 작업

- processedItems 메모이제이션 제거 — deps가 매 스크롤마다 바뀌어 이득 없던 useMemo 제거
- promotionDetailEventData를 useMemo로 묶어 오브젝트 재생성 방지 (memoize가 정답이던 케이스)
- options 메모이제이션
- list memoization 추가 — React.memo + 콜백 시그니처를 인자 기반으로 변경해 참조 공유
- banner section 리팩토링 — currentIdxRef 패턴으로 콜백 안정화, ref 미러링 적용
