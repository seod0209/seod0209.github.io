---
title: "Sneaky React Memory Leaks: useCallback과 클로저의 함정"
date: 2025-06-25
categories: ["React"]
tags: ["메모리", "useCallback", "클로저", "성능"]
---

> 시리즈 'React 성능·메모리' 3편. 유명한 "Sneaky React Memory Leaks" 류 아티클을 읽고 정리한 노트에, 실제 프로젝트에서 겪은 재생성/누수 사례를 접목했다.

메모리 누수라고 하면 보통 "리스너 안 지웠네" 같은 명백한 걸 떠올린다. 그런데 React에서 정말 은근한(sneaky) 누수는 **클로저와 memoize가 얽히면서 오래된 참조를 붙잡고 있는** 경우다. 코드는 멀쩡해 보이는데 메모리는 슬금슬금 오른다. 아티클들을 정리하면서 "아 이거 우리 배너에서 겪은 거네" 싶은 게 많아서 같이 묶어 적는다.

## 클로저는 "그 시점의 값"을 기억한다

함수는 자기가 정의된 스코프의 변수를 계속 붙잡는다. React 컴포넌트 안에서 만든 함수는 **그 렌더 시점의 props/state를 캡처**한다.

```tsx
function Component({ data }) {
  const handle = () => console.log(data); // 이 렌더의 data를 캡처
  useEffect(() => {
    window.addEventListener('scroll', handle);
    return () => window.removeEventListener('scroll', handle);
  }, []); // deps 비어있음 → 최초 handle만 등록됨
}
```

이런 코드는 두 가지가 동시에 새어나간다. (1) `handle`은 영원히 첫 렌더의 오래된 `data`만 본다(stale closure). (2) 첫 렌더의 클로저가 계속 살아있어 그 스코프 전체가 GC되지 않는다.

> 이 둘은 서로 다른 문제다. **stale closure**는 함수가 오래된 값을 계속 참조하는 *동작* 버그(메모리가 안 줄어드는 것과 무관하게 값이 틀림)이고, **누수(leak)**는 그 클로저와 클로저가 붙잡은 스코프가 해제되지 않아 메모리가 쌓이는 *자원* 문제다. 위 코드처럼 얽혀서 같이 터질 수 있을 뿐, 원인과 증상은 구분해서 봐야 한다.

## 함정 1: useCallback을 쓰면서 deps를 잘못 줄 때

`useCallback`은 "이 함수의 참조를 유지해줘"라는 도구다. 그런데 deps를 비우면 오래된 클로저를 그대로 고정해버린다. 반대로 deps에 매번 바뀌는 객체를 넣으면 useCallback이 무의미해진다(매번 새 함수).

```tsx
// 잘못: deps 비움 → count는 영원히 0에 갇힘
const onClick = useCallback(() => {
  console.log(count); // 항상 초기값
}, []);
```

핵심은 **memoize 자체가 목적이 아니라, "안정된 참조"와 "최신 값" 사이의 균형**이라는 것이다.

## 함정 2: 콜백을 deps에 넣어 observer/effect가 재등록될 때

배너 섹션을 리팩토링하면서 정확히 이 패턴을 만났다. `IntersectionObserver`를 붙이는 effect가 `onVisibilityChange` 콜백을 deps로 갖고 있었는데, 이 콜백은 부모에서 렌더마다 새로 만들어져 내려왔다. 결과적으로 **렌더마다 observer가 해제·재등록**됐다. 재등록 자체도 비싸지만, 이전 observer/콜백 참조가 깔끔히 정리되지 않으면 그게 누수의 씨앗이 된다.

해결은 콜백을 `ref`에 미러링해서 effect deps에서 빼는 것이다.

```tsx
const sectionRef = useRef<HTMLDivElement>(null);
// 콜백을 ref로 미러링 → deps에서 제외해 observer 재등록 방지
const onVisibilityChangeRef = useRef(onVisibilityChange);
onVisibilityChangeRef.current = onVisibilityChange;

useEffect(() => {
  const el = sectionRef.current;
  if (!el) return;
  const observer = new IntersectionObserver(([entry]) => {
    onVisibilityChangeRef.current(entry.isIntersecting); // 항상 최신 콜백
  });
  observer.observe(el);
  return () => observer.disconnect(); // 정리도 확실히
}, []); // 콜백이 deps에 없으니 재등록 안 됨
```

ref 미러링 패턴의 이점: 참조는 고정(effect 재등록 없음)이면서, `.current`로 항상 최신 콜백을 읽는다. stale closure와 재등록을 동시에 피한다.

## 함정 3: "배너당 1회" 같은 로직이 참조로 판정될 때

노출(impression) 이벤트를 "배너당 한 번만" 보내려는데 자꾸 중복 발송됐다. 원인은 effect deps가 배너 **객체 참조**였기 때문이다. 리렌더로 객체가 새로 만들어지면 같은 배너인데도 "바뀐 것"으로 보고 다시 발송했다.

```tsx
// 현재 배너 노출(impression) 기록 — 배너당 1회 (id 기준 비교)
const viewedBannerIds = useRef<Set<string>>(new Set());

useEffect(() => {
  if (!isVisible || !currentBanner) return;
  if (viewedBannerIds.current.has(currentBanner.id)) return;
  viewedBannerIds.current.add(currentBanner.id);
  onImpression(currentBanner.id);
  // eslint-disable-next-line react-hooks/exhaustive-deps
}, [currentBanner?.id, isVisible]); // 객체가 아니라 id 기준
```

두 가지를 바꿨다. (1) deps를 `[currentBanner, isVisible]`(객체 참조)에서 `[currentBanner?.id, isVisible]`(원시값)로. (2) 이미 본 id를 `useRef(Set)`에 누적. ref는 리렌더와 무관하게 값이 유지되고, 리렌더를 유발하지도 않는다.

## 함정 4: 언마운트 시 정리가 debounce에 먹힐 때

토스트가 화면 전환 직후 사라지는 버그가 있었다. 토스트 함수 내부의 debounce가 언마운트 타이밍에 호출을 삼켜버린 것. "cleanup을 했는데 왜 안 되지"의 반대 케이스로, **비동기 처리가 언마운트 이후 실행되며 엉키는** 전형이다.

```tsx
const once = useRef(false);
const { noDebounceShowToast } = useToast();

useEffect(() => {
  if (once.current) return; // StrictMode 이중 실행/재마운트 방어
  once.current = true;
  // debounce 없는 토스트를 써서 언마운트 타이밍에 삼켜지지 않게
  noDebounceShowToast(message);
}, []);
```

## 정리: 은근한 누수를 막는 체크리스트

- effect에 등록한 것(observer/listener/timer/subscription)은 **반드시 cleanup**한다.
- 콜백을 effect deps에 넣어 재등록이 반복되면 **ref 미러링**으로 참조를 고정하되 최신 값을 유지한다.
- "1회성" 판정은 객체 참조가 아니라 **id 같은 원시값**으로 하고, 누적 상태는 `useRef(Set)`에 담는다.
- 비동기(debounce/throttle/타이머)는 언마운트와의 경합을 항상 의심한다.
- `useCallback`/`useMemo`는 "memoize했으니 안전"이 아니라, **deps가 맞아야** 안전하다. deps가 틀리면 stale closure(오래된 값 참조 버그)가 생기고, 그 고정된 클로저가 참조를 계속 붙잡으면 누수로도 이어진다 — 별개의 두 증상이다.

> 💡 메모리 누수 디버깅은 감으로 하지 말자. Chrome DevTools의 Memory 탭에서 heap snapshot을 두 번 찍어 비교하면(자란 객체가 뭔지) 붙잡고 있는 참조가 보인다.

## 관련 작업

- banner section 리팩토링 — impression effect deps를 `[currentBanner, isVisible]`(객체) → `[currentBanner?.id, isVisible]`(id)로 변경해 재발송 방지, 자동전환 타이머 useAutoSlide로 격리
- toast 내부 debounce 때문에 언마운트 시 토스트 호출이 지워지는 문제 — debounce 없는 toast로 전환
- list memoization 추가 — React.memo + 콜백 시그니처 정리
