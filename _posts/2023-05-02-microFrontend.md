```
title: Micro Frontend
author: dongee_seo
date: 2023-05-02
categories: [Blogging]
tags: [google analytics, pageviews]
```

마이크로 프론트앤드는 마이크로 서비스처럼 전체 화면을 작동할 수 있는 단위로 나누어 개발한 후 서로 조립하는 방식이다. 여기서 작동 단위에 사용된 프론트앤드 프레임워크로 Angular 이든, React 또는 Vue 또는 Vanilla 자바스크립트에 상관하지 않고 조합 가능한 방법을 제공한다. 본글에서는 마이크로 프론트앤드 개발 방법중 Angular 프레임워크를 사용하면서 [Web Components](https://developer.mozilla.org/ko/docs/Web/Web_Components)를 사용한 통합 방법에 대핸 알아보자.

![](https://blog.kakaocdn.net/dn/Z8Xpj/btqD8ivThmR/Eli8ghsYYVPmTokeiQno81/img.png)
마이크로 프론트앤드 기반 독립된 팀별 애플리케이션 개발

## Micro Frontend 개념

마이크로 프론앤드 개념으로 개발을 하는 잇점은 대규모 엔터프라이즈 애플리케이션을 개발한다고 가정할 때, 각 팀별 또는 업무단위에 대해 Backend + Frontend 개발 후 통합하는 이슈를 줄일 수 있다.

- 작고, 응집력 있고 유지보수성을 가지는 코드베이스를 가질 수 있다. ( **_Simple, decoupled codebase_** )
- 분리배포가 용이하고, 자율적인 팀 조직운영이 수월해진다. ( **_Independent deployment, Autonomous teams_** )
- 프론트앤드 개발을 점진적 업그레이드 또는 재작성이 수월해진다. ( **_Incremental upgrades_** )

하지만 단점도 존재한다.

- 배포 번들 사이즈가 커질 수 있다. ( **_Payload size_** )
- 서로간의 개발 환경의 차이로 복잡도가 올라간다. ( **_Environment differences_** )
- 운영 및 거버넌스도 당연히 복잡해진다. ( **_Operational governance complexity_** )

[Thoughtworks의 Technology Radar에 의하면 Micro Frontend가](https://www.thoughtworks.com/radar/techniques/micro-frontends) 현재 적용 가능한(Adapt) 상황이다.

[마틴 파울러의 글](https://martinfowler.com/articles/micro-frontends.html) (또는 [번역글](https://medium.com/@juyeon.kate/micro-frontends-%EB%B2%88%EC%97%AD%EA%B8%80-1-5-29c80baf5df)) 에서 잘 설명을 하고 있으니 참조하자.

## Micro Frontend 통합 방법

![](https://blog.kakaocdn.net/dn/Dq0Wh/btqD9uvB5Ps/UriEcpocPkt5a9fICSAgYK/img.png)
독립적인 개발 및 배포

마이크로 프론앤드 방식으로 개발 후 각 단위 애플리케이션을 어떻게 통합할지 고려해야 한다. 통합할 때는 각 화면을 조합하는 컨테이너 애플리케이션이 있고, 그 하부에 들어가는 단위 애플리케이션이 존재한다. ([참조](https://medium.com/@juyeon.kate/micro-frontends-%EB%B2%88%EC%97%AD%EA%B8%80-2-5-66e3a31b72a9))

- 서버 템플릿 통합: 각 서버로 html 템플릿을 요청하고, 최종 응답서버에서 각 템플릿을 조합해서 응답을 보냄
  - 서버측에서 최종 화면을 조합한다.
- 빌드타임 통합: 단위 애플리케이션을 패키지로 배포하고, package.json에 명시한 후 컨테이너 애플리케이션에서 import하여 사용하는 방법
  - 각 애플리케이션에 대한 런타임 대응이 안된다.
  - 애플리케이션을 릴리즈하고 최종 애플리케이션에서 컴파일해야 한다.
- iframe 통합: 전통적인 방식이면서 가장 쉬운 방식이다.
  - 애플리케이션 통합의 유연성 높다.
  - 애플리케이션의 기술 종속성이 없다.
  - routing, history, deep-link같은 것이 복잡해질 수 있다.
  - 컨테이너 애플리케이션과 iframe에 들어가는 단위 애플리케이션간의 통신규약도 필요하다.
  - UX가 iframe안에 갇히기 때문에 어색한 UI 표현을 가질 수 있다.
- Javascript를 통한 런타임 통합: iframe과 달리 유연한 통합이 가능하다. 현실적으로 가장 많이 사용하는 방식이다.
  - 컨테이너 애플리케이션을 단위 애플리케이션 번들을 `<script>` 태그를 통합 다운로드 받고
  - 약속된 초기화 메소드를 호출한다.
  - 클라이언트측에서 (브라우져) 통합한다.
- Web Components를 통한 통합: HTML 커스텀 엘리먼트를 통한 통합방법, static, runtime 통합 둘 다 가능함.
  - Javascript를 통한 런타임 통합과 유사하지만 "The web component way"를 지향한다.
  - 클라이언트측에서 (브라우져) 통합한다.

Mirco Frontend 통합할 때 몇가지 고려사항

- UI 스타일 일관성은 UI Component Library를 만들어 대응한다.
  - 한번에 만들지 말고, 중복코드가 발생하는 지점에서 만들고
  - 코드 일관성을 유지하는 팀이 수행한다.
- 어플리케이션 통신은 Custom events를 사용한다.
  - 커스텀 이벤트를 위해 [PubSubJS](https://github.com/mroderick/PubSubJS)를 고려해 보자.
  - 호출시 URL 라우팅에 넘기기
- 백앤드 호출 API 구성
  - BFF(Backend for Frontend Pattern) 패턴으로 프론트앤드 전용 API를 갖는다.
  - 별도의 데이터베이스를 가질 수도 있다.
  - 로그인은 인증 정보는 통합하는 Container가 소유한다.

![](https://blog.kakaocdn.net/dn/OURFu/btqEd8sGlj4/VlGpBl2RKrW5Mqs0UvB2EK/img.png)
프론트앤드와 백앤드의 구조화
