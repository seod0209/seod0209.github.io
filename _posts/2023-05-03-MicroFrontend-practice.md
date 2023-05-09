`title: Micro Frontend: Practice author: dongee_seo date: 2023-05-03 categories: [Blogging] tags: [Micro Frontend]`

# 마이크로 프론트엔드 아키텍처 소개

별도로 개발 및 배포 가능한 여러 작은 웹 애플리케이션을 조합하여 하나의 웹 애플리케이션을 만드는 개발방법론.

마이크로프론트엔드는 한 팀이 하나의 유닛으로 독립적으로 개발하고, 시험하고, 배포할 수 있는 프론트엔드의 조각이다. 그러나 우리는 이 조각들을 함께 붙여서 단일한 웹 애플리케이션으로 사용자에게 보여주는 것을 확실히 해야 한다.

## **마이크로프론트엔드들 조립을 위한 전략들**

주로 두 개의 접근 방법이 있다. 하나는 각 마이크로프론트엔드를 구성하고 호스팅하는 단일한 컨테이너 앱을 사용하는 것이다. 또 다른 접근 방법은 각각 서로 다른 곳으로 찾아갈 수 있는 URL(통합 포인트)과 파라미터들을 알고 있어서 이것들을 따로따로 호스팅 하는 것이다. (웹사이트의 페이지들과 유사)

마이크로엔드들을 컨테이너 앱으로 합치는 방법은 여러가지가 있다. 이러한 방법들은 컴포지션을 사용한 서버사이드에서부터 프론트엔드 빌드 타임에서 통합, 그리고 런타임에서 등 다양하다.
만약 런타임 통합을 택했다면 아이프레임을 사용한 애플리케이션 통합, 자바스크립트를 사용한 통합, 또는 웹 컴포넌트들을 사용한 통합 등 다수의 선택지를 가지게 된다.

저장소(각 마이크로 프론트엔드의 저장소) 간 컴포넌트들을 공유하는 것. 이것은 일관적인 UI와 유지보수 가능하고 확장성 있는 프로젝트를 위해 결정적이다.

# 1단계: 리액트를 사용하여 기저 프로젝트 구조 만들기

이 애플리케이션에서 List와 Auth 컴포넌트를 분리하여 각각 마이크로 프론트엔드를 대표하게 한다.
이러한 접근은 이것들을 단일한 앱으로 붙이는 방법을 넓은 범위에서 고를 수 있게 더 많은 융통성을 준다.

NextJS에서 마이크로 아키텍쳐를 구성하고 이를 통해서 얻을 수 있는 장점을 설명

### 1. **`next-create-app`을 통해 3개의 서비스를 만든다.**

```jsx
npx create-next-app --ts container
npx create-next-app --ts list
npx create-next-app --ts auth
```

아래 명령어를 입력하여 `@module-federation/nextjs-mf` 패키지를 설치하도록 한다.

```
npm i @module-federation/nextjs-mf@5.5.0
```

###### "@module-federation/nextjs-mf" 패키지를 사용하면

모노리스 응용 프로그램을 여러 Next.js 마이크로 앱으로 분할하고
소프트웨어 개발 수명주기에서 마이크로 프론트 엔드를 활성화할 수 있다.

그러나 실행 시에는 서버 및 클라이언트에서 모듈 연합에 의해 원격/공유 모듈 로드 논리가 처리되므로
하나의 ReactDOM 트리로 작동하는 모놀리스 앱으로 작동.

기본적으로 nextjs.config에 "@module-federation/nextjs-mf" 플러그인을 추가하기만 하면됨.

### 2. 라이브러리 패키지에서 공통 소스 코드만들기

```jsx
./contianer/src/component/Header.tsx

import React from "react";

const Header = () => {
    return (
        <div style={{ padding: "12px", width: "100%", height: "100px", backgroundColor: "#000", color: "#fff" }}>
            Header
        </div>
    );
};

export default Header;
```

### 3. 만들고 나서 Webpack 설정을 통해 해당 utility를 외부에서 사용하겠다고 알려주어야 한다.

```jsx
// ./list/next.config.js

const NextFederationPlugin = require("@module-federation/nextjs-mf");
/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: true,
};

const remotes = (isServer) => {
    const location = isServer ? "ssr" : "chunks";
    return {
        auth: `auth@<http://localhost:3000/_next/static/${location}/remoteEntry.js`>,
        container: `container@<http://localhost:3001/_next/static/${location}/remoteEntry.js`>,
        list: `list@<http://localhost:3002/_next/static/${location}/remoteEntry.js`>,
    };
};

module.exports = {
    ...nextConfig,
    webpack5: true,
    swcMinify: true,
    distDir: "build",
    webpack(config, options) {
        Object.assign(config.experiments, { topLevelAwait: true });
        if (!options.isServer) {
            config.plugins.push(
                new NextFederationPlugin({
                    name: "list",
                    remoteType: "var",
                    remotes: remotes(options.isServer), //만들어진 remoteEntry 파일 경로를 입력한다.
                    filename: "static/chunks/remoteEntry.js",
                    exposes: {
                        "./header": "./src/component/Header.tsx", // 이 곳에 외부에서 가져와 사용할 파일 명을 입력해준다.
                        "./photoList": "./src/component/PhotoList.tsx",
                    },
                    shared: {
                        react: {
                            eager: true,
                            singleton: true,
                            requiredVersion: false,
                        },
                    },
                })
            );
        }

        return config;
    },
};
```

### 4. 컨테이너 서비스에서 공통 소스 코드를 가져와 사용해보자.

```jsx
const NextFederationPlugin = require("@module-federation/nextjs-mf");
/** @type {import('next').NextConfig} */

const remotes = (isServer) => {
    const location = isServer ? "ssr" : "chunks";
    return {
        auth: `auth@<http://localhost:3000/_next/static/${location}/remoteEntry.js`>,
        container: `container@<http://localhost:3001/_next/static/${location}/remoteEntry.js`>,
        list: `list@<http://localhost:3002/_next/static/${location}/remoteEntry.js`>,
    };
};
const nextConfig = {
    reactStrictMode: true,
    webpack5: true,
    disDir: "build", // Defined build directory
    swcMinify: true,
    webpack: (config, options) => {
        Object.assign(config.experiments, { topLevelAwait: true });
        if (!options.isServer) {
            config.plugins.push(
                new NextFederationPlugin({
                    name: "container",
                    filename: "static/chunks/remoteEntry.js", // remote file name which will used later
                    remotes: remotes(options.isServer), //만들어진 remoteEntry 파일 경로를 입력한다.
                    exposes: {
                        // 이 곳에 외부에서 가져와 사용할 파일 명을 입력해준다.
                    },
                    shared: {
                        react: {
                            singleton: true,
                            requiredVersion: false,
                        },
                        "react-dom": {
                            singleton: true,
                            requiredVersion: false,
                        },
                    },
                })
            );
        }

        return config;
    },
};

module.exports = nextConfig;
```

```tsx
import dynamic from "next/dynamic";

// Importing modules
const Header = dynamic(() => import("list/src/component/Header"), {
  suspense: true
});

export default function Home() {
  return (
    <>
      <div> {"CONTAINER"}</div>
      <Header />
    </>
  );
}
```

참고자료

[](https://okhivrych.io/nextjs-with-module-federation-the-future-of-micro-frontends)[https://okhivrych.io/nextjs-with-module-federation-the-future-of-micro-frontends](https://okhivrych.io/nextjs-with-module-federation-the-future-of-micro-frontends)

[](https://velog.io/@lucas/%EB%A7%88%EC%9D%B4%ED%81%AC%EB%A1%9C-%ED%94%84%EB%A1%A0%ED%8A%B8%EC%97%94%EB%93%9C-%EC%A0%95%EB%B3%B5%EA%B8%B0)[https://velog.io/@lucas/마이크로-프론트엔드-정복기](https://velog.io/@lucas/%EB%A7%88%EC%9D%B4%ED%81%AC%EB%A1%9C-%ED%94%84%EB%A1%A0%ED%8A%B8%EC%97%94%EB%93%9C-%EC%A0%95%EB%B3%B5%EA%B8%B0)

[](https://dev.to/logrocket/micro-frontend-with-react-and-nextjs-n6h)[https://dev.to/logrocket/micro-frontend-with-react-and-nextjs-n6h](https://dev.to/logrocket/micro-frontend-with-react-and-nextjs-n6h)
[](https://caramellow.tistory.com/10086859)[https://caramellow.tistory.com/10086859](https://caramellow.tistory.com/10086859)

[](https://ux.stories.pe.kr/38)[https://ux.stories.pe.kr/38](https://ux.stories.pe.kr/38)

[](https://velog.io/@dalbodre_ari/%EB%A7%88%EC%9D%B4%ED%81%AC%EB%A1%9C-%ED%94%84%EB%A1%A0%ED%8A%B8%EC%97%94%EB%93%9C%EC%99%80-%EB%AA%A8%EB%85%B8%EB%A0%88%ED%8F%AC-%EC%A0%9C%EB%A1%9C%EB%B9%8C%EB%93%9C)[https://velog.io/@dalbodre_ari/마이크로-프론트엔드와-모노레포-제로빌드

https://www.kimcoder.io/blog/micro-frontend-module-federation
](https://velog.io/@dalbodre_ari/%EB%A7%88%EC%9D%B4%ED%81%AC%EB%A1%9C-%ED%94%84%EB%A1%A0%ED%8A%B8%EC%97%94%EB%93%9C%EC%99%80-%EB%AA%A8%EB%85%B8%EB%A0%88%ED%8F%AC-%EC%A0%9C%EB%A1%9C%EB%B9%8C%EB%93%9C)
