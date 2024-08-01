---
title: React Native 각 OS 화면비율 맞추기
author: dongee_seo
date: 2023-06-13
categories: [Zippu, React-Native]
tags: [google analytics, react native, side project]
---

# Problem

iOS화면만 보고 개발했을 때 AOS의 화면이 와장창..
<image src="https://velog.velcdn.com/images/seod0209/post/95b77fb0-e5ad-435d-b8e2-930250c11441/image.png" width="50%" height="auto" alt="bad_ui"/>


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
      Dimensions.get('screen').height * (x / basicDimensions.height),
    ).toFixed(2),
  );
};
// 가로 변환 작업

export const width = (x: number) => {
  return Number(
    Number(
      Dimensions.get('screen').width * (x / basicDimensions.width),
    ).toFixed(2),
  );
};

```

# Limitation
1. 성능 이슈 가능성
 Dimensions.get('screen') 호출이 매번 함수 호출 시 실행되므로, Dimensions.get('screen') 호출을 최적화하거나 useWindowDimensions 훅이 필요하다.

2. ~~디바이스 특화 로직 부재~~
 아이폰 X와 그 이후 모델들은 상단에 노치(notch)가 있어서 상태 바 높이나 레이아웃에서 다른 기기와 차이가 있다. 따라서 해당 사항을 반영하는 추가적인 코드가 필요하다.

```jsx

// 아이폰 X인지 체크하는 함수
export const isIphoneX = () => {
  return (
    Platform.OS === 'ios' &&
    !Platform.isPad &&
    !Platform.isTV &&
    (screenHeight === 812 ||
      screenWidth === 812 ||
      screenHeight === 896 ||
      screenWidth === 896)
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