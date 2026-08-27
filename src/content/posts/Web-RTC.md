---
title: "Web RTC?"
date: 2023-06-28
categories: ["Frontend"]
tags: ["webrtc", "p2p"]
---

## 1. Web RTC ?

웹 애플리케이션과 사이트가 중간자 없이 브라우저 간에 오디오나 영상 미디어를 포착하고 마음대로 스트림 할 뿐 아니라, 임의의 데이터도 교환할 수 있도록 하는 기술

- 드라이버나 플러그인 설치 없이 웹 브라우저 간 P2P(peer-to-peer network; 동등 계층간 통신망) 연결을 통해 데이터 교환을 가능하게 하는 기술

- WebRTC가 실시간으로 웹에서 데이터를 교환할 수 있는 이유는 시그널링(signaling)으로 연결 정보(SDP, 후보 주소 등)를 주고받고, STUN/TURN 서버를 활용한 ICE 과정을 통해 NAT를 우회하기 때문

- 화상 통화와 실시간 스트리밍, 파일 공유, 스크린 공유 등이 WebRTC를 기반

#### P2P 연결

- 비교적 소수의 서버에 집중하기보다는 망구성에 참여하는 기계들의 계산과 대역폭 성능에 의존하여 구성되는 통신망

- 대칭형(symmetric) NAT나 방화벽 환경에서는 ICE가 TURN 릴레이 서버로 폴백하여 모든 트래픽이 릴레이를 거치게 된다. 따라서 항상 P2P로 직접 연결되는 것도, 항상 빠른 속도가 보장되는 것도 아니다.

- 미디어·데이터의 암호화 보안은 HTTPS가 아니라 **필수(mandatory) DTLS-SRTP**에서 온다. HTTPS는 페이지와 시그널링 채널만 보호할 뿐이며, 시그널링 서버를 신뢰할 수 없다면 지문(fingerprint) 검증 없이는 중간자 공격이 가능하므로 보안이 '보장'된다고 말할 수 없다.

- 실시간으로 상호작용 => 더욱 개인화되고 참여 유도적인 웹 어플리케이션을 제작할 기회 제공

## 2. WebRTC 통신 원리

![](https://velog.velcdn.com/images/seod0209/post/900631fd-4d52-4e9d-bb5c-5eca12d333b7/image.png)

#### STUN vs TURN, 그리고 시그널링

- **STUN** 서버는 단말이 자신의 공인 IP·포트를 알아내도록 돕는 역할만 한다. 이렇게 알아낸 주소로 양쪽이 직접(P2P) 연결되면 트래픽은 서버를 거치지 않는다.

- **TURN** 서버는 직접 연결이 불가능한 NAT/방화벽 환경에서 모든 미디어·데이터 트래픽을 대신 중계(relay)한다. ICE는 STUN으로 직접 연결을 먼저 시도하고 실패하면 TURN 릴레이로 폴백한다.

- WebRTC는 시그널링(signaling) 프로토콜을 표준으로 규정하지 않는다. SDP·후보 주소를 어떻게 주고받을지는 애플리케이션이 자유롭게 선택하며(WebSocket, HTTP 등), 이 채널의 신뢰성이 곧 보안과 직결된다.

### Web RTC의 브라우저 호환성

WebRTC가 범용적으로 사용되기 위해서는 다양한 플랫폼과 브라우저에서 접속하는 사용자들에게 동일한 사용자 경험을 제공하는 일이 중요함. 때문에 WebRTC에서 브라우저와 플랫폼 간 호환성은 가장 큰 숙제.

- 크롬(Chrome)에서 호환성이 높음. WebRTC는 구글이 주도한 오픈소스 프로젝트를 기반으로 하는 웹 표준이기 때문.

- 파이어폭스(Firefox)와 오페라(Opera) 등이 WebRTC 표준을 적극적으로 후원

- 사파리(Safari) 역시 WebKit 기반 브라우저이기 때문에 WebRTC가 지원되기는 하지만,
  애플의 정책이 늘 그렇듯 다른 브라우저에 비해 호환성도 가장 떨어지고 기본으로 지원해주는 설정들이 적은 편.

크로스 브라우징 이슈

> 해당 내용은 거의 해결되었음
> => 참고!! https://caniuse.com/?search=web%20rtc

### 참고자료

- https://caniuse.com/?search=web%20rtc

- [WebRTC는 어떻게 실시간으로 데이터를 교환할 수 있을까? - 재그지그의 개발 블로그](https://wormwlrm.github.io/2021/01/24/Introducing-WebRTC.html#stun-turn)

## 출처
- [RFC 8827 — WebRTC Security Architecture](https://www.rfc-editor.org/rfc/rfc8827)
