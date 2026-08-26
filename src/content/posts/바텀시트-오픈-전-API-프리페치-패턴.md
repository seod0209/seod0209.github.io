---
title: "바텀시트 오픈 전 API 프리페치 패턴"
date: 2026-07-23
categories: ["Architecture"]
tags: ["React", "react-query", "BottomSheet", "UX"]
---

> 이 글은 '프론트엔드 아키텍처 패턴' 시리즈의 한 편이다.

## 들어가며

차량 상세 페이지에서 "등급 변경" 버튼을 누르면 바텀시트가 스윽 올라오면서 등급 목록을 보여준다. 그런데 초기 구현은 이런 순서였다.

1. 버튼 클릭
2. 바텀시트 오픈
3. 그제서야 API 호출
4. 스피너 뱅글뱅글
5. 데이터 도착 → 목록 렌더

사용자는 바텀시트가 올라온 뒤 텅 빈 로딩 화면을 잠깐 보게 된다. 애니메이션은 이미 끝났는데 내용은 비어 있으니 어색하다. 엥, 뭔가 순서가 잘못됐다.

이 글은 **"열기 전에 미리 fetch"** 로 이 어색함을 없앤 패턴을 정리한 것이다.

## 반응형 오버레이부터: 모바일은 바텀시트, 데스크탑은 모달

먼저 전제를 하나 깔아야 한다. 우리 서비스는 같은 콘텐츠를 **모바일에선 바텀시트로, 데스크탑에선 중앙 모달로** 띄운다. 그래서 오픈/클로즈 로직을 컴포넌트마다 재구현하지 않고 컨트롤러 훅으로 공통화했다.

```tsx
interface UseModalControllerParams {
  /** 지정 시 URL 쿼리(`?{modalKey}=open`)로 열림/닫힘 상태를 관리한다. 없으면 로컬 state. */
  modalKey?: string;
  onClose?: () => void;
  /** 오버레이 클릭으로 닫기 허용 여부 */
  enableOverlayClick: boolean;
}

export const useModalController = ({
  modalKey,
  onClose,
  enableOverlayClick,
}: UseModalControllerParams) => {
  const [isOpen, setIsOpen] = useState(false);
  const isOpenRef = useRef(false);

  const open = useCallback(() => {
    setIsOpen(true);
    isOpenRef.current = true;
  }, []);

  // 리액트 setState는 비동기라, 동기 조회가 필요한 imperative handle을 위해 ref도 함께 갱신
  const getIsOpen = useCallback(() => isOpenRef.current, []);

  // ...open/close/onClickOverlay
  return { isOpen, open, close, getIsOpen, onClickOverlay };
};
```

> 💡 `open()` 직후 `getIsOpen()`을 부르면 `setState`가 비동기라 아직 이전 값이 나온다. 그래서 동기 `ref`를 함께 갱신해서 곧바로 최신값을 읽게 했다. 이벤트 수집처럼 "열자마자 상태를 봐야 하는" 곳에서 이 함정을 실제로 밟았다.

바텀시트는 `@toss/use-overlay` 위에 얇은 헬퍼를 하나 얹어서, 콘텐츠 컴포넌트만 넘기면 알아서 마운트되고 열리도록 했다.

```tsx
export const useOpenOverlay = () => {
  const { open } = useOverlay();

  const openBottomSheet = (
    ContentComponent: React.ComponentType<any>,
    props?: any,
    bottomSheetProps?: any,
  ) => {
    open(() => {
      const ref = useRef<BottomSheetRef>(null);

      useEffect(() => {
        ref.current?.open();
      }, []);

      return (
        <BottomSheetV2 ref={ref} enableOverlayClick {...bottomSheetProps}>
          <ContentComponent {...props} close={() => ref.current?.close()} />
        </BottomSheetV2>
      );
    });
  };

  return { openBottomSheet };
};
```

## 문제의 핵심: fetch 타이밍

여기까지는 "여는 법"이다. 진짜 UX 문제는 **언제 데이터를 가져오냐**였다. 콘텐츠 컴포넌트가 마운트되고 나서야 `useQuery`가 돌면, 바텀시트 애니메이션 → 빈 화면 → 로딩 → 렌더 순서가 된다.

그래서 순서를 뒤집었다. **버튼을 누르는 순간(또는 hover 시점) 먼저 데이터를 데워두고, 그 다음에 연다.** react-query의 `prefetchQuery`가 딱 이 용도다. 프리페치된 쿼리는 캐시에 이미 올라가 있으니, 콘텐츠가 마운트될 때 `useQuery`가 캐시 히트로 즉시 데이터를 받는다.

차량 상세는 SSR 단계에서 이 방식을 이미 쓰고 있었다.

```tsx
const queryClient = new QueryClient();

await queryClient.prefetchQuery({
  queryKey: ['car/detail/info'],
  queryFn: () => fetchCarDetailInfo({ id_cargrade }),
});

return {
  props: {
    id_cargrade: parsedId,
    dehydratedState: dehydrate(queryClient),
  },
};
```

같은 발상을 클라이언트 오버레이에도 옮긴다. 열기 직전에 프리페치하는 커스텀 훅으로 감싸면 이렇게 된다.

```tsx
function usePrefetchAndOpen() {
  const queryClient = useQueryClient();
  const { openBottomSheet } = useOpenOverlay();

  // 열기 전에 데이터부터 데운다
  const prefetch = (id_cargrade: string) =>
    queryClient.prefetchQuery({
      queryKey: ['car/detail/info', id_cargrade],
      queryFn: () => fetchCarDetailInfo({ id_cargrade }),
    });

  const openGradeSheet = async (id_cargrade: string) => {
    await prefetch(id_cargrade);      // 1) fetch
    openBottomSheet(GradeSheetContent, { id_cargrade }); // 2) open
  };

  return { prefetch, openGradeSheet };
}
```

콘텐츠 쪽은 평범하게 `useQuery`만 쓰면 된다. 이미 캐시에 있으니 스피너가 안 뜬다.

```tsx
function GradeSheetContent({ id_cargrade }: { id_cargrade: string }) {
  const { data } = useQuery({
    queryKey: ['car/detail/info', id_cargrade],
    queryFn: () => fetchCarDetailInfo({ id_cargrade }),
  });
  // data는 프리페치 캐시에서 즉시 온다
  return <GradeList grades={data?.grades ?? []} />;
}
```

> 여기서 중요한 건 **`queryKey`를 프리페치와 실제 조회가 정확히 똑같이 쓴다**는 점이다. 키가 어긋나면 캐시 히트가 안 나고, 프리페치는 그냥 낭비된 네트워크 호출이 된다.

hover가 가능한 데스크탑에서는 한 발 더 앞서갈 수 있다.

```tsx
<button
  onMouseEnter={() => prefetch(id_cargrade)} // 마우스 올릴 때 미리
  onClick={() => openGradeSheet(id_cargrade)} // 클릭하면 이미 캐시됨
>
  등급 변경
</button>
```

## 반대 방향도 있다: 닫혀 있을 땐 구독 끊기

프리페치가 "미리 데운다"라면, 그 짝은 "안 볼 땐 계산도 구독도 하지 말자"다. 바텀시트 안의 콘텐츠가 전역 스토어를 구독하고 있으면, 시트가 닫혀 있어도 스토어가 바뀔 때마다 리렌더가 돈다. 그래서 **열려 있을 때만 구독**하도록 셀렉터에 조건을 걸었다.

```tsx
const [isOpen, setIsOpen] = useState(false);

// 닫혀 있으면 null을 반환해서 리렌더 유발을 끊는다
const currSection = useCardetailSectionStore(state =>
  isOpen ? state.section : null,
);
```

`ref.current?.visible`을 함께 활용하기도 했다.

```tsx
const sectionState = useCardetailSectionStore(state =>
  ref.current?.visible ? state.section : null,
);
```

프리페치(열기 전에 미리)와 지연 구독(닫혀 있으면 안 함)은 방향은 반대지만 목표는 같다. **"필요한 순간에 정확히"** 데이터를 흐르게 하는 것.

## 모바일 특유의 함정 하나

바텀시트를 모바일에서 열 때 스크롤 잠금을 `document.body.style.overflow = 'hidden'`으로 처리하면, iOS/모바일 브라우저의 주소창(상단바)이 계속 활성 상태로 남는 문제가 있었다. 그래서 바텀시트는 `portal`로 띄우고 자동 높이 조정을 쓰도록, 드롭다운 계열은 `useCloseOutside`로 바깥 클릭 시 닫히도록 정리했다. 오버레이 하나 여는 것도 모바일에선 이런 디테일이 붙는다.

## 정리

- 반응형 오버레이(모바일 바텀시트 / 데스크탑 모달)는 **컨트롤러 훅으로 공통화**한다.
- fetch 순서를 뒤집어라: **열기 전에 `prefetchQuery`**로 데이터를 데운 뒤 연다. 애니메이션 끝나면 이미 채워져 있다.
- 프리페치와 실제 조회의 **`queryKey`를 반드시 일치**시킨다.
- hover 가능한 환경이면 `onMouseEnter`로 더 앞당긴다.
- 반대로 **닫혀 있을 땐 구독을 끊어** 불필요한 리렌더를 없앤다.

바텀시트는 "열고 나서 채우는" 게 아니라 "채워두고 여는" 것이다. 순서 하나 바꿨을 뿐인데 체감 속도가 확 달라진다.

## 관련 작업

- 반응형 상담신청 화면 — 하단 고정 버튼 UI, `useThrottle`/resize debounce 훅 추가, 정적/동적 렌더링 옵션 정리
- 모달 구조 정리 — ModalLayout/CommonModal/ResponsiveModal 재편, 공통 open/close 로직을 `useModalController` 훅으로 추출, ResponsiveModalShell 도입
- 등급 선택 바텀시트/드롭다운 스크롤·높이 정리, bottom sheet scroll 수정
- 드롭다운이 모바일 주소창에 가려지는 문제를 portal 기반 bottom sheet로 해결, `useCloseOutside` 적용
- 차량상세 `useOpenOverlay` BottomSheet를 V2로 변경, 차량변경 바텀시트 적용
- Bottom sheet가 열렸을 때에만 section 정보를 구독하도록 변경
