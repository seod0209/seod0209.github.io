```
title: 첫 오픈소스 contribution
author: dongee_seo
date: 2024-02-25
categories: [Blogging]
tags: [google analytics, pageviews]
```

## 라이브러리가 deprecated되었다

오랜만에 블로그를 작성하려하는데
![](https://velog.velcdn.com/images/seod0209/post/22253406-7576-4bb5-a54c-7847a5cc1454/image.jpg)
에..? upstream/master로 chirpy theme repository를 업데이트 후 conflict 대잔치..

그러던 중 plugin관련 라이브러리가 deprecated되었다는 경고를 보게되었다.
![](https://velog.velcdn.com/images/seod0209/post/c2e8fc5d-86e4-43ff-a8e2-1910468ce570/image.png)

## Babel에서 클래스 속성을 변환하는 플러그인이 필요한 이유

`@babel/plugin-proposal-class-properties`은 Babel에서 클래스 속성을 변환하는 데 사용되는 플러그인이다.

Babel에서 클래스 속성을 변환하는 플러그인이 필요한 이유는 다음과 같다:

1. 브라우저 호환성:

최신 JavaScript 기능 중 일부는 오래된 브라우저에서 지원되지 않을 수 있다. 이러한 기능을 사용하여 작성된 코드를 모든 브라우저에서 실행하려면, Babel과 같은 도구를 사용하여 이러한 기능을 이전 버전의 JavaScript로 변환해야 한다.

2. 최신 버전의 JavaScript 표준을 준수

최신 버전의 JavaScript 표준을 준수하기 위해, 실험적인 또는 향상된 JavaScript 기능을 사용하는 경우 해당 기능을 표준 JavaScript로 변환해야 한다. Babel은 이러한 작업을 수행할 수 있는 강력한 도구 중 하나이다.

3. 효율성 및 편의성:
   클래스 속성을 변환하는 작업은 매우 일반적이며, 이를 수동으로 하려면 많은 노력이 필요하다. Babel 플러그인을 사용하면 이러한 변환 작업을 자동화하고, 코드 작성 과정을 더 효율적으로 만들 수 있다.

ES6 클래스에서 클래스 속성을 사용하는 경우 다음과 같이 코드를 작성할 수 있다.

```jsx
class Person {
  constructor(name) {
    this.name = name;
  }

  greet() {
    return `Hello, ${this.name}!`;
  }
}
```

하지만, 이 코드는 일부 브라우저에서 지원되지 않을 수 있다.이를 이전 버전의 JavaScript로 변환하려면, 클래스 속성을 생성자 내부에서 할당하는 것으로 변환해야 한다.

이를 Babel을 사용하여 클래스 속성을 변환하는 플러그인을 사용하여 자동으로 변환할 수 있다. 예를 들어, @babel/plugin-transform-class-properties 플러그인을 사용하면 다음과 같이 클래스 속성을 변환할 수 있다.

```jsx
class Person {
  name = "";

  constructor(name) {
    this.name = name;
  }

  greet = () => {
    return `Hello, ${this.name}!`;
  };
}
```

위의 코드는 클래스 속성을 **직접 클래스 본문 내에서 선언하고 초기화**하는 것으로 변환된다. 이렇게 하면 코드를 더 간결하게 유지할 수 있으며, 클래스 생성자 내부에서 일일이 할당하는 작업을 수동으로 하지 않아도 된다.

이러한 변환 작업은 플러그인을 사용하면 자동으로 이루어지므로 개발자가 직접 수동으로 변환 작업을 수행할 필요가 없습니다.따라서 **Babel에서 클래스 속성을 변환하는 플러그인을 사용**하여 최신 JavaScript 기능을 안정적이고 호환성 있게 사용할 수 있다.

## 해결방안

@babel/plugin-proposal-class-properties가 deprecated되어 더 이상 유지보수되지 않으므로, 더 이상 해당 플러그인에 대한 새로운 기능이나 버그 수정이 이루어지지 않는다. 따라서 대체할 수 있는 새로운 라이브러리나 기능을 찾아서 업데이트 하는 것이 좋다.

**@babel/plugin-transform-class-properties로 업데이트**함으로써 최신 Babel 버전과 함께 업데이트된 클래스 속성을 지원할 수 있다.

## 결과

권장하는 라이브러리로 교체 후 **[PR#1559](https://github.com/cotes2020/jekyll-theme-chirpy/pull/1559)** 을 작성했고, merge 되었다.

![](https://velog.velcdn.com/images/seod0209/post/017f5d0a-e054-4468-a93a-6ff6234b0df8/image.png)

![](https://velog.velcdn.com/images/seod0209/post/9035d6fe-c48f-4905-ad65-d3b4ed49ef8d/image.png)

![](https://velog.velcdn.com/images/seod0209/post/19807d3d-67bf-4e1f-ae10-3971fb70c1e4/image.jpeg)

허헣 소소한 문제해결:) 오늘 되게 개발자같았다.
