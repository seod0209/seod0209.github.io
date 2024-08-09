
---
title: React Native를 선택한 이유
author: dongee_seo
date: 2023-04-23
categories: [Zippu, React-Native]
tags: [google analytics, react native, side project]
---


# **왜 React Native를 도입해야 하는가 ? 🧐**
**1. 앱개발은 처음이라.. ✨**
React Native는 React 문법을 통해 앱 개발을 할수있는 프레임워크이다. React와 매우 유사하므로 React를 통한 웹 개발 경험이 있는 나에게 앱개발의 진입장벽을 낮춰주었달까? 쉽게 React Native를 익힐 수 있다. 그리고 Emulator를 이용하여 에러 메시지를 잘 표시해주기 때문에 개발 경험이 매우 좋았다.
 
**2. 시간은 없는데요 두개를 만들라고하네요? **

기존 Native 앱 개발에 있어서 android는 Kotlin, ios는 Swift를 이용해서 따로 개발해야했던 반면에, 하나의 코드로 android와 ios를 둘 다 개발할 수 있다는 장점이 있다. 하지만 이것은 양날의 검과도 같다..이유는 후술.

**3. 사용성 개선**
이게 가장 큰 이유이다.
- 대상 플랫폼의 표준 렌더링 API를 사용
- 작성한 마크업을 플랫폼에 상응하는 진짜 네이티브 엘리먼트로 전환
    - 코르도바(Cordova)나 아이오닉(Ionic)과 같은 기존 크로스 플랫폼 앱 개발 방법과 다른 점
    - Webview
        - JS, HTML, CSS를 사용하여 모바일 앱을 만드는 기존 방법.
        - 네트워크를 통해서 서버를 거쳐 로딩하기 때문에 페이지가 로드될 때 발생하는 로딩 시간을 피할 수 없습니다.
- 또한 메인 UI 스레드와 분리되어 실행되기에 앱의 역량을 줄이지 않고도 빠른 성능을 유지.
- React Native 코드는 자바스크립트로 작성되지만 브릿지 역할만 할 뿐 
네이티브 코드로 렌더링되기 때문에
 Webview보다 좀 더 네이티브에 가까운 경험을 제공
 (가끔 Android 에서 보이는 UI와 iOS 에서 보이는 UI가 일관되지 않게 보이는 경우가 존재…😇)

### 그러나 리액트 네이티브는 다음의 단점도 가지고 있다.

**1. React Native와 Native와의 간극** 
React Native는 대상 플랫폼의 네이티브 엘리먼트로 변환시켜주긴 하지만, 어쨌는 Native 앱은 아니기 때문에 필요에 따라 직접적인 native 코드 수정이 필요할 때가 있다. 

> 예를 들어, 앱에 첫 진입시 보이는 splash(launch screen)화면에 애니메이션을 넣어달라는 요구사항이 있었다. xCode나 android studio에서는 수정하기 어려운 부분이었다. 🥲 
splash화면의 네이티브코드가 어떻게 구성되어있는지 어느 부분에 애니매이션을 어떻게 넣아야하는지 알고 있다면 간단히 수정할 수 있는 사항이었다. 즉 네이티브 코드를 수정해야하는 사항이었다.

또한, 새로운 버전의 네이티브가 나왔을 때(예를 들어, 업데이트 된 안드로이드 버전에서 새로운 API 세트를 제공할 때) React Native에서 이를 지원해줄 때까지 시간이 걸린다. 

**2. 디버깅의 어려움** 
React Native는 매우 좋은 디버깅 기능을 제공하고 있지만 그것은 React Native 생명 주기와 관련된 내용이거나 JavaScript와 관련된 내용에 대해서고, 실제로 개발을 진행하면서 느낀 점은 네이티브 쪽과 관력된 사항에는 디버깅이 어려웠다. 
디버깅한다고 코드를 타고들어가다보면 어느새 나는 native코드에 도달해있다.

# **프로젝트 초기 환경**

React Native 커뮤니티에서 많은 개발자들은 **React Native CLI** 또는 **Expo CLI** 중 하나를 선택하게 된다.

우리는 새로운 React Native 프로젝트를 **React Native CLI** 를 통하여 생성하였다.

React Native CLI 를 사용하면 Java / Object-C 로 작성된 기본 모듈을 추가할 수 있다는 강력한 기능이 있기 때문에Android 및 iOS 플랫폼 모두에서 애플리케이션을 완벽하게 제어할 수 있다는 점 때문이었다.

### 정적 타입 check

React Native에 기본적인 정적 타입 체커로 [Flow](https://flow.org/) 가 적용되어 있지만, Flow 대신 사용이 익숙한 Typescript 를 도입하였다. React Native에서도 Typescript를 지원한다.

아래의 명령어를 통하여 별도의 설정 없이 Typescript 템플릿으로 프로젝트를 시작할 수 있다.

`npx react-native init zippu-react-native --template react-native-template-typescript`

### JWT(Json Web Token) 핸들링

네이티브 앱에 임베딩된 React Native 화면이기 때문에 
API 요청을 하기 위해서는 먼저 네이티브 앱으로부터 **활성 토큰을 전달**받아 처리해야 했다.

** 네이티브 앱으로부터 활성 토큰을 가져오는 부분**

보통 HTTP client 로 많이 사용하는 [axios](https://axios-http.com/) 를 사용하고 있다.

네이티브 앱에서 React Native로 화면 전환 시, 활성 토큰을 prop 으로 전달받아 [axios instance](https://axios-http.com/docs/instance) 헤더에 추가해주었다.

애플리케이션이 종료되거나 재시작되었을 때 토큰을 유지하기 위해  AsyncStorage나 보안 저장소를 사용하여 토큰을 저장하고, 애플리케이션이 시작될 때 이를 읽어와서 상태를 복원하였다.

** 만료된 토큰을 갱신하는 부분 **
일정 시간이 지나 토큰이 만료되었을 때에 토큰 갱신에 대한 처리가 필요했다.

axios 의 [interceptor](https://axios-http.com/docs/interceptors) 를 활용하였다. interceptor 는 Promise 가 `then` 이나 `catch` 로 처리되기 전에 요청이나 응답을 가로챌 수 있다.

`catch` 로 처리되기 전에 응답을 가로채어 서버에서 보내주는 상태 코드에 따라 토큰저장, 토큰 갱신, 로그아웃 및 네비게이션을 처리하였다.


### API 요청 상태 관리 (feat. react-query)

API 요청 상태 관리를 위해 [React Query](https://react-query.tanstack.com/) 를 사용하였다.

React Query 를 사용하면 아래와 같이 API 요청 상태 관리를 Hook 으로 표현할 수 있다.
```tsx
  `**const** { data, isLoading, isError, isIdle } **=** useQuery(queryKeys.GET_LEVEL_STATUS, getLevelStatus, options);`
```
React Query 는 현재 ReactDOM 에서만 지원되는 `devtools` 를 제외하고 React Native와 바로 동작할 수 있게 설계되어 있다. 따라서, 팀에서 관리하는 **Webview, Webclient 등 다른 서비스와 API 요청 상태를 관리하기 위해 만든 커스텀 Hook 을 쉽게 공유하고 재사용 할 수 있다는 장점이 있다.**

### 컴포넌트 스타일링

 React Native에서 컴포넌트 스타일링을 하기 위해서 보통 [StyleSheet](https://reactnative.dev/docs/stylesheet)를 사용한다. `StyleSheet.create`는 스타일을 앱의 시작 시 미리 처리하여, 실행 시 성능을 최적화한다. 스타일 객체를 메모리에 한 번만 저장하고, 이후에는 참조만 하므로 성능이 좋다.

1. 컴포넌트 파일에 `StyleSheet` 를 정의하거나 스타일을 정의한다.
2. 아래처럼 컴포넌트마다 별도의 스타일 정의 파일(`styles.ts`)을 추가한다.

일반적으로 위 두가지 방법 중 하나를 택하게 된다. 

초기에는 StyleSheet를 사용하였지만, 컴포넌트 스타일을 쉽게 정의하고 관리하기 위해 emotion을 추가적으로 사용하였다. Emotion CSS 라이브러리는 스타일링을 위한 강력하고 유연한 도구로, 리액트네이티브 개발에도 적용할 수 있다. 

### 빌드 & 배포

배포는 두 가지로 구분된다.

**1. 네이티브 앱이 빌드할 때 포함되는 초기 번들 및 디펜던시를 가져오는 과정 (Artifact Upload)**

**2. 두 번째는 네이티브 변경이 필요하지 않을 때, 사용자 디바이스에 직접 배포되는 과정 (CodePush)**

이 두 과정 모두 Github Actions 사용해서 자동으로 돌아가게끔 구성하였다.

### Artifact Upload
** 빌드 및 저장소 업로드 자동화 **
React Native에 네이티브와 의존성이 필요한 모듈이 추가될 때는 앱 스토어 배포가 불가피하다. 따라서, 네이티브 앱이 빌드할 때 React Native의 의존성과 번들 파일을 업로드 할 임의의 저장소가 필요하다.
 github repository에 업로드 하도록 설정해두었고, Github Actions 사용해서 Tag 생성 시 자동으로 진행되게끔 구성하였다.

**  스토어 배포 자동화** 
해당부분은 구현하지 못하였다. fastlane의 추가 설정이 필요해보인다. 


### CodePush

먼저 [appcenter cli](https://docs.microsoft.com/ko-kr/appcenter/cli/) 을 통해서 배포 환경 (Staging / Production)을 추가해 주었다.

그리고 나서는 Github Actions를 사용해서 `develop`, `master` 브랜치에 머지 될 때 자동으로 appcenter 내에 Staging / Production으로 번들이 업로드 되도록 설정해 주었다.

# **마치며**

참고 자료

- https://hyperconnect.github.io/2022/03/02/embedded-react-native.html
- https://reactnative.dev/docs/typescript
- https://blog.soomgo.com/posts/6673bb8c52107866fb86a78b