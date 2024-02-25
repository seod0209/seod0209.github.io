```
title: 첫 오픈소스 contribution
author: dongee_seo
date: 2024-02-25
categories: [Blogging]
tags: [google analytics, pageviews]
```

jekyll로 블로그를 만들어 두었었는데,엉성한 UI를 고쳐보고자 chirpy 테마적용!

![](https://velog.velcdn.com/images/seod0209/post/22253406-7576-4bb5-a54c-7847a5cc1454/image.jpg)

오랜만에 블로그를 작성하려하는데
에..? upstream/master로 chirpy theme repository를 업데이트 후 conflict 대잔치..

그러던 중 plugin관련 라이브러리가 deprecated되었다는 경고를 보게되었다.
![](https://velog.velcdn.com/images/seod0209/post/c2e8fc5d-86e4-43ff-a8e2-1910468ce570/image.png)

라이브러리가 deprecated되면 해당 라이브러리는 더 이상 유지되지 않으며 더 이상 지원되지 않을 수 있다. 따라서 deprecated된 라이브러리를 사용하는 것보다 대체할 수 있는 새로운 라이브러리나 기능을 찾아서 업데이트 하는 것이 좋다.

그래서 권장하는 라이브러리로 교체 후 [PR#1559](https://github.com/cotes2020/jekyll-theme-chirpy/pull/1559)을 작성했고, merge 되었다.

![](https://velog.velcdn.com/images/seod0209/post/017f5d0a-e054-4468-a93a-6ff6234b0df8/image.png)

![](https://velog.velcdn.com/images/seod0209/post/9035d6fe-c48f-4905-ad65-d3b4ed49ef8d/image.png)

![](https://velog.velcdn.com/images/seod0209/post/19807d3d-67bf-4e1f-ae10-3971fb70c1e4/image.jpeg)

허헣 소소한 문제해결:) 오늘 되게 개발자같았다.
