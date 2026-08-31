---
title: "DonZ를 만들며 #4 — 검색에 나오기 시작하니, 사람보다 봇이 먼저 왔다"
date: 2026-08-31
categories: ["Analytics"]
tags: ["GA4", "봇트래픽", "이벤트설계", "퍼널", "SEO", "실사용자"]
---

> [#3](/posts/DonZ를-만들며-3-만들고-나니-검색에-안-나왔다)에서 검색 노출을 손봤다. 그랬더니 GA Realtime에 사람이 찍히기 시작했다 — 고 생각했다. 김칫국 한 사발이었다.

## "외국인이 쓴다고?"

커스텀 도메인을 붙이고 며칠 뒤, GA4 Realtime을 열었더니 지도에 점이 떴다. 미국이다. *외국인이 내 사주 사이트를 쓴다고?* 잠깐 신났다.

숫자를 다시 봤다.

```
ACTIVE USERS IN LAST 30 MINUTES   3
ACTIVE USERS IN LAST 5 MINUTES    0
지도 점                            Oregon · Washington(동부)
Active users by First user source  No data available
Active users by Audience           All Users  3  (100%)
```

이상한 게 셋이었다. 30분에 3명인데 5분엔 0명 — 왔다가 바로 사라진다. 위치가 죄다 미 서부 Oregon과 동부 Washington 한 점. 그리고 **First user source가 "No data available"** — 사람은 google이든 direct든 어디선가 온다. 유입 소스가 통째로 비어 있다는 건, 그냥 주소로 때리고 들어왔다는 뜻이다.

김칫국이었다. 이건 사람이 아니다.

## 도시 이름이 자백이었다

로그에 찍히는 도시들을 죽 늘어놓으면 패턴이 보인다.

```
Council Bluffs · Ashburn · Boardman · Frankfurt ...
```

전부 **데이터센터 도시**다. Boardman(오리건)·Council Bluffs(아이오와)는 구글 클라우드 리전, Ashburn(버지니아)은 세계 최대 데이터센터 밀집지, Frankfurt는 유럽 리전. 사람이 사는 동네가 아니라 **클라우드가 사는 동네**다. Realtime 지도의 Oregon 점이 Boardman, 동부 Washington 점이 Ashburn이었다.

## "view는 많은데 왜 행동을 안 하지?"

봇이라고 확신한 결정타는 이벤트였다. [#3 곁다리](/posts/DonZ를-만들며-3-만들고-나니-검색에-안-나왔다)에서 화면 전환마다 직접 쏘게 만든 그 이벤트들 말이다.

- `screen_view (screen_name=home)`는 찍힌다.
- 그런데 그 뒤가 **없다.** `field_focus`(폼 필드를 건드림)도, `button_click (*_submit)`(결과 보기)도, `screen_view (*_result)`(결과 화면)도 안 따라온다.

사람이라면 홈만 보고 3초 만에 필드 하나 안 건드리고 나가지 않는다. 홈만 긁고 사라지는 트래픽 — **JS까지 실행하지만 아무 상호작용도 안 하는 봇**이다.

여기서 흔한 오해 하나. "GA4가 봇을 걸러주지 않냐?" 걸러준다. 다만 GA4의 known-bot 필터는 **알려진 크롤러 목록** 기반이라, JS를 실행하는 헤드리스 브라우저 계열 일부는 그물을 빠져나와 **사용자로 남는다.** 그래서 Total users가 지저분해진다.

## 왜 하필 지금인가

인과를 정확히 짚으면 이렇다 — **GA가 더 잘 잡게 된 게 아니라, 사이트가 더 잘 발견되기 시작한 것이다.**

`aging-project-...vercel.app` 같은 랜덤 서브도메인은 주소를 모르면 못 찾아온다. 그런데 커스텀 도메인을 붙이면 DNS가 생기고, HTTPS 인증서가 발급되고([#3](/posts/DonZ를-만들며-3-만들고-나니-검색에-안-나왔다)에서 붙인) sitemap·robots·canonical·Search Console 신호까지 얹힌다. 그 순간부터 새 도메인을 자동으로 훑는 SEO 크롤러, 보안 스캐너, 링크 검사기, 헤드리스 브라우저가 줄줄이 찾아온다.

```
도메인 공개
  → 사이트가 발견됨 (DNS·인증서·sitemap·canonical)
  → JS 실행 봇이 접속
  → GA4 known-bot 필터를 통과한 일부가 '사용자'로 남음
```

나쁜 신호만은 아니다. east2lab.com이 이제 랜덤 URL이 아니라 **공개 웹 생태계에 노출된 진짜 사이트**가 됐다는 뜻이기도 하다. 게다가 [#1의 설계](/posts/DonZ를-만들며-1-LLM을-안-부르기로-한-결정) 덕에 봇이 아무리 때려도 LLM 비용은 0이다 — 지저분해지는 건 GA 숫자뿐, 지갑이 아니다.

## 그래서 "active user"를 다시 정의했다

교훈은 하나였다. **Total users는 못 믿는다. 믿을 건 행동이다.** active user가 사람이냐를 묻지 말고, "어디까지 행동한 사람을 실사용자로 볼 것인가"를 먼저 정해야 한다. 그 기준이 곧 지표다.

DonZ의 이벤트 퍼널로 층을 나눴다.

```
전체 방문자          → 참고용 (봇 섞임)
field_focus          → 관심 후보 (보조 · 노이즈 있음)
*_result screen_view → 실사용자   [헤드라인]
*_submit button      → 자력 이용자 (엄격)
*_share button       → 강한 engagement
```

**헤드라인은 `*_result` 화면 도달**로 잡았다(`age_result`·`saju_car_result`·`compatibility_result`).

- Home-only 봇은 **절대 여기 도달하지 못한다** → 봇 배제 목적에 정확히 맞다.
- 폼을 끝까지 채운 사람 + 공유 링크로 결과를 열어본 사람 둘 다 잡힌다 — 둘 다 진짜 사용이다.
- `screen_name` 하나로 거는 단일 필터라 리포트가 깔끔하다.

`field_focus`는 헤드라인이 아니라 **"관심은 보였으나 결과까지 안 감" 이탈 퍼널용 보조 코호트**로 뒀다(JS 봇도 포커스를 흉내 낼 수 있어 노이즈가 더 크다). 스스로 폼을 돌린 사람만 엄격히 세고 싶으면 `*_submit` 클릭이 최강 신호다(공유 링크 방문자까지 걷어낸다).

> 부수 소득: "First user source가 비어 있음" 자체가 쓸 만한 봇 판별 신호였다. 유입 소스 없이 홈만 긁고 나가는 세션은 사람일 확률이 낮다.

## 마무리

Realtime의 "3명"을 보고 잠깐 설렜지만, 5분 체류 0·데이터센터 도시·유입 소스 공백·상호작용 0이 전부 같은 방향을 가리켰다. 초기 새 사이트는 **사람 둘에 자동화 열다섯**만 섞여도 그래프가 커 보인다.

그래서 숫자를 못 믿을 땐 행동을 믿기로 했다. **"active user가 사람일까"가 아니라, "어디까지 행동해야 사람으로 칠까"** — 판단 기준을 먼저 박는 게 지표 설계의 시작이었다.

## 관련 작업

- 이벤트 택소노미: `src/lib/analytics.ts` — `SCREEN`(screen_name), `BUTTON`(button), `FIELD`(field_focus). 이름을 한 곳에서만 만들어 도구 간 규칙 통일.
- 화면 전환 추적: `src/lib/firebase.ts` `trackScreen`(SPA `send_page_view:false` 후 라우트별 수동 전송) — [#3](/posts/DonZ를-만들며-3-만들고-나니-검색에-안-나왔다) 참고.
- 앞 편: [#1](/posts/DonZ를-만들며-1-LLM을-안-부르기로-한-결정) · [#2](/posts/DonZ를-만들며-2-생년월일-하나가-생각보다-어려웠다) · [#3](/posts/DonZ를-만들며-3-만들고-나니-검색에-안-나왔다)
- 관측 기록은 GA4 Realtime 기준 필자 관측치이며, 원인(도메인 공개 → 자동화 유입)은 정황을 종합한 가장 그럴듯한 설명이다.
