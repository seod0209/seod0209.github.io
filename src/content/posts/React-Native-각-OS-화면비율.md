---
title: "React Native 각 OS 화면비율 맞추기"
date: 2023-06-13
categories: ["Zippu", "React-Native"]
tags: ["react-native", "styling", "side project"]
---

# Problem

iOS화면만 보고 개발했을 때 AOS의 화면이 와장창..
<img src="https://velog.velcdn.com/images/seod0209/post/95b77fb0-e5ad-435d-b8e2-930250c11441/image.png" width="50%" height="auto" alt="bad_ui"/>


# Improvement
해당 코드는 React Native 프로젝트에서 화면 크기, 여백, 글자 크기 등을 일정한 기준에 맞추어 설정하기 위한 유틸리티 함수와 상수를 정의하였다.
```jsx
import { Dimensions, PixelRatio, Platform, StatusBar } from 'react-native';

export const basicDimensions = {
  // 디자이너가 작업하고 있는 XD파일 스크린의 세로,가로
  height: 812,
  width: 375,
};
export const height = (x: number) => {
  return Number(
    Number(
      Dimensions.get('window').height * (x / basicDimensions.height),
    ).toFixed(2),
  );
};
// 가로 변환 작업

export const width = (x: number) => {
  return Number(
    Number(
      Dimensions.get('window').width * (x / basicDimensions.width),
    ).toFixed(2),
  );
};

```

# Limitation
1. 성능 이슈 가능성 & 화면 갱신
 Dimensions.get('window') 호출이 매번 함수 호출 시 실행되므로 최적화가 필요하고, 무엇보다 값이 모듈 최상단에서 한 번만 계산되면 회전·폴더블·split view 등에서 값이 갱신되지 않는다. 이런 경우 useWindowDimensions() 훅을 쓰면 화면 크기 변화에 맞춰 값이 실시간으로 다시 계산된다. (참고: 'screen'은 상태 바·내비게이션 바를 포함한 물리 화면 전체를 가리키고, RN이 실제로 그리는 영역은 'window'이므로 비율 계산에는 'window'를 써야 AOS 레이아웃이 어긋나지 않는다.)

2. ~~디바이스 특화 로직 부재~~
 아이폰 X와 그 이후 모델들은 상단에 노치(notch)가 있어서 상태 바 높이나 레이아웃에서 다른 기기와 차이가 있다. 따라서 해당 사항을 반영하는 추가적인 코드가 필요하다.

```jsx

// 아이폰 X인지 체크하는 함수
export const isIphoneX = () => {
  return (
    Platform.OS === 'ios' &&
    !Platform.isPad &&
    !Platform.isTV &&
    // 노치/다이나믹 아일랜드 모델의 세로 길이(iPhone X~15 계열): 812, 844, 852, 896, 926, 932 ...
    // 이렇게 특정 값을 하드코딩하면 새 기기가 나올 때마다 누락되므로 신뢰하기 어렵다.
    // 노치/세이프 에어리어 처리는 react-native-safe-area-context 의 insets 로 판단하는 것을 권장한다.
    [812, 844, 852, 896, 926, 932].includes(screenHeight) ||
    [812, 844, 852, 896, 926, 932].includes(screenWidth)
  );
};

// 주어진 두 스타일 중 하나를 선택하는 함수
export const applyStyleForIphoneX = (
  iphoneXStyle: number,
  regularStyle: number,
) => {
  return isIphoneX() ? iphoneXStyle : regularStyle;
};

export const getStatusBarHeight = (safe: boolean) => {
  return Platform.select({
    ios: applyStyleForIphoneX(safe ? height(72) : height(56), height(72)),
    android: StatusBar.currentHeight,
  });
};
```

## 출처
- [React Native — Dimensions](https://reactnative.dev/docs/dimensions)