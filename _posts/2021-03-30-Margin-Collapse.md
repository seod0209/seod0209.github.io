---
title: 마진 상쇄(margin collapsing)
author: dongee_seo
date: 2021-03-30
categories: [Blogging, Tutorial]
tags: [google analytics, pageviews]
---

> 분명 margin-top(또는 margin-bottom)을 먹였는데... 왜죠 왜 사라지는거죠;;
> '마진 상쇄(Margin collapsing)'가 일어나는 원인을 알아보고 아래 사진처럼 대참사가 일어나지 않게하는 방법을 찾아보자.

![](https://velog.velcdn.com/images/seod0209/post/bbd30cb9-6ef1-417c-b98b-94ab652b4ecd/image.png)

## 1. Margin collapsing 의의

### 1-1 개념

마진이 겹치게 되면 상쇄가 일어나는 현상. 즉,흔히 **마진 겹침 현상**이 일어나는 것이다.

블록의 top 및 bottom 마진은 때로는 (결합되는 마진 중 크기가) 가장 큰 한 마진으로 결합(combine, 상쇄(collapsed))됩니다, 마진 상쇄(margin collapsing)로 알려진 행동

CSS에서 인접한 2개 또는 그 이상의 박스(block 요소)들의 마진이 하나의 마진으로 결합될 수 있다. 이러한 결합현상을 **마진 상쇄**라고 한다.
즉, 어떤 두 개 이상 블록 요소의 상하 마진이 겹칠 때 어느 한 쪽의 값만 적용하는것을 의미.
:: 이하부터는 '블록(block) 요소'를 '박스'라고 부르겠다.

### 1-2 마진 상쇄가 일어나는 3가지 상황

#### 1-2-1 인접 형제

인접 형제 박스 간 상하 마진이 겹칠 경우
겹쳐진 두 마진 값을 비교해, **_더 큰 마진 값_**으로 상쇄해 렌더링한다. 만약 겹쳐진 두 값이 동일할 경우, **_중복_**을 상쇄해 렌더링한다.

#### 1-2-2 빈 블록의 상하 마진이 겹칠 때

- '빈 블록'이란 높이(height)가 0인 상태의 블록 요소를 뜻한다.
- height / min-height / padding / border 등 상하로 늘어나는 프로퍼티 값을 명시적으로 주지 않았거나
- 내부에 Inline 콘텐츠가 존재하지 않는 요소

=> 이 경우 **위와 아래를 가르는 경계가 없으므로** ,
자신의 상단 마진의 값과 하단 마진의 값을 비교해
더 큰 값으로 상쇄한다.
만약 겹쳐진 두 값이 동일할 경우, 중복을 상쇄한다.
특히 빈 요소와 인접 박스들 간에 마진 겹침이 일어나는 구조에서는 상쇄가 여러 번 발생하게 된다.

> "빈 블록을 안 만들면 되지 않나?"
> 하지만 슬프게도 빈블록이 필요한 경우가 의외로 빈번..
>
> - 빠른 레이아웃 구성을 위해 div로 영역을 만들어 놓을 경우
> - 내부에 요소를 append 하기 위해 빈 컨테이너를 만들어 놓을 경우 등
>   height, padding, border 등 **높이와 관련된 속성들은 상위로부터 상속되지 않기** 때문이다.

#### 1-2-3 부모 박스와 첫 번째(마지막) 자식 박스의 상단(하단) 마진이 겹칠 때

margin이란 콘텐츠 간의 간격이고, 간격을 벌리기 위해서는 경계를 필요한다.
브라우저는 '부모 박스와 첫 번째(마지막) 자식 박스 간의 경계'를 그 사이에 있는 border / padding / inline 콘텐츠 유무로 판단한다.
앞에 설명했던 빈 박스의 마진 상쇄 현상과는 조금 다르게, 이미 명시적으로 height / min-height 값을 줬더라도 이번 경우엔 적용되지 않는다.

따라서 부모와 첫 번째(마지막) 자식 사이에

- inline 콘텐츠(텍스트 등)가 없거나,
- 상단(하단)에 명시적으로 padding 또는 border 값을 주지 않았다면
  마진이 겹치게 됩니다.
  이때, 자식 요소의 마진이 더 크든 작든 상관없이 상쇄된 마진은 부모 박스의 바깥으로만 렌더링이 된다.
  (대환장파티가 열리는거다,,)

1. 부모 박스와 첫 번째 자식 박스의 상단 마진이 나란히 겹칠 때
2. 부모 박스와 마지막 자식 박스의 하단 마진이 나란히 겹칠 때(상단 마진끼리 겹칠 때와 같은 원리)

### 1-3 마진 상쇄 특징(규칙)

- 마진 상쇄는 인접한 두 박스가 온전한 block-level 요소일 경우에만 적용된다.
  (inline, inline-block, table-cell, table-caption 등의 요소는 block-level이 아님.)
- 마진 값이 0이더라도 상쇄 규칙은 적용.
  부모의 바깥 여백이 0이건 아니건 자손의 바깥 여백은 부모 밖으로 나오게 된다. (weegle과제참고)
- 좌우 마진은 겹치더라도 상쇄되지 않는다.
- 상하 마진이 겹칠 경우에만 일어난다.
- (세 개 이상의 여백 사이의) 더 복잡한 여백 상쇄는 위의 기본 상황이 서로 결합되어 발생.
- 음수 값을 가진 바깥 여백을 포함할 경우
  :상쇄된 여백의 크기= 제일 큰 양수 여백과 제일 작은(음의 방향으로, 절댓값이 제일 큰) 여백의 합.
- 모든 바깥 여백이 음수 값을 가질 경우
  : 상쇄된 여백의 크기= 제일 작은(음의 방향으로, 절댓값이 제일 큰) 여백의 크기.인접 요소와 중첩 요소 모두에 적용.

## 2. Margin collapsing 해결방안

#### 2-1 인접 형제/ 빈 블록의 상하 마진이 겹칠 때

1. height / min-height / padding / border 등 상하로 늘어나는 프로퍼티 값을 명시적으로 주지 않은경우
   => 해결방안
   상하로 늘어나는 프로퍼티 값을 명시적으로 준다.
2. 내부에 Inline 콘텐츠가 존재하지 않는 요소
   => 해결방안
   display:inline-block;width:100%;

#### 2-2 부모 박스와 첫 번째(마지막) 자식 박스의 상단(하단) 마진이 겹칠 때

1. inline 콘텐츠(텍스트 등)가 없는경우
   => 해결방안
   display:inline-block;width:100%;
2. 상단(하단)에 명시적으로 padding 또는 border 값을 주지 않은경우
   => 해결방안
   부모 박스 상단(하단)에 padding 또는 border 값을 주어 벽을 만들어주는 것이 안전함.
   이렇게 하면 의도했던 대로 첫 번째(마지막) 자식 요소를 배치할 수 있다.

### _즉 CSS에 border, padding, inline를 상황에 맞게 포함시켜주면 된다._

이외에도#### 2-3 마진 상쇄의 예외를 고려해보기.

다음과 같은 상황에서는 인접 요소 간 마진 상쇄가 일어나지 않는다.

- 박스가 position: absolute 된 상태
- 박스가 float: left/right 된 상태 (단, clear 되지 않은 상태)
- 박스가 display: flex 일 때 내부 flexbox item
- 박스가 display: grid 일 때 내부 grid item

> 참고자료
>
> - [https://developer.mozilla.org/ko/docs/Web/CSS/CSS_Box_Model/Mastering_margin_collapsing](https://developer.mozilla.org/ko/docs/Web/CSS/CSS_Box_Model/Mastering_margin_collapsing)
> - [https://www.w3.org/TR/CSS2/box.html#collapsing-margins](https://www.w3.org/TR/CSS2/box.html#collapsing-margins)
> - [https://velog.io/@raram2/CSS-%EB%A7%88%EC%A7%84-%EC%83%81%EC%87%84Margin-collapsing-%EC%9B%90%EB%A6%AC-%EC%99%84%EB%B2%BD-%EC%9D%B4%ED%95%B4](https://velog.io/@raram2/CSS-%EB%A7%88%EC%A7%84-%EC%83%81%EC%87%84Margin-collapsing-%EC%9B%90%EB%A6%AC-%EC%99%84%EB%B2%BD-%EC%9D%B4%ED%95%B4)

:: 마치며
지난번 CSS과제를 하면서 모든것에 absolute로 도배하며 원하는 화면이 나오는것에만 만족했는데,,absolute로 모든 문제를 해결하기란 무리였고,, 계속되는 상쇄현상을 피하고자 이번 기회에 개념을 집고넘어갔다. 그리고 해결했다!!
![](https://velog.velcdn.com/images/seod0209/post/37ddc5c9-cff0-4844-8bbf-63fe2fcbd5cc/image.png)

```null
부모박스(feedBox)에 display:inline-block; 을 추가하니
아무일 없다는듯,,,

.feedBox {
   max-width: 560px;
   width: 100%;
   height: 900px;
   background-color: yellow;
   margin:0 0 0 40px;
   display: flex;
   flex-direction: column;
   display:inline-block;
}
```

하,,허무하구먼
