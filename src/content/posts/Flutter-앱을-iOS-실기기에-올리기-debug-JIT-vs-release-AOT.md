---
title: "실기기에서 Flutter 앱이 혼자 안 돌 때: iOS는 JIT, Android는 옛 APK (feat. RN 비교)"
date: 2026-08-21
categories: ["Flutter"]
tags: ["Flutter", "iOS", "Release", "AOT", "실기기", "코드사이닝"]
---

> 앞서 vision-camera 얼굴 인식을 Flutter로 재구현한 글의 마지막 과제가 **실기기 검증**이었다. iOS·Android 둘 다에서 "앱이 혼자 안 돈다"는 **같은 증상**을 만났는데, 파보니 원인이 서로 달랐다. 게다가 "RN은 되는데 Flutter는 안 되네"라고 느꼈던 것도, 알고 보니 **불공정한 비교**였다. 그 삽질과 반성의 기록이다.

## 증상: 케이블 뽑으면 앱이 죽는다

Flutter로 포팅한 FaceCamera를 아이폰에 꽂고 `flutter run`으로 띄웠다. 카메라도 잘 뜨고 얼굴 인식도 돈다. 좋아, 됐다 싶어서 케이블을 뽑았다. **그 순간 앱이 죽었다.** 다시 꽂으면 살고, 뽑으면 죽고. 홈에서 아이콘을 눌러도 스플래시 뜨자마자 튕긴다.

엥..? 분명 설치는 됐는데 왜 단독으로는 안 살지.

## 원인: debug는 JIT, iOS는 그걸 금지한다

한참 헤매다 알았다. 이건 내 앱 버그가 아니라 **빌드 모드**의 문제다.

- **Flutter debug 빌드 = Dart VM의 JIT(Just-In-Time).** hot reload 같은 개발 편의가 다 여기서 온다. 코드를 실행 시점에 컴파일한다.
- 그런데 **iOS는 디버거가 붙어 있지 않은 상태에서 JIT 코드 실행을 보안상 금지**한다. `flutter run`이 lldb를 attach해 두는 동안만 JIT가 허용되는 거다.
- 그러니 케이블(=디버거)을 떼는 순간 JIT 실행 권한이 사라지고 앱이 죽는다. RN 개발 모드에서 Metro 번들러가 붙어 있어야 도는 것과 같은 결이다.

즉 `flutter run`으로 실기기에서 "단독 실행"을 기대한 게 애초에 틀린 전제였다.

## 해결: release는 AOT라 디버거가 필요 없다

답은 release 빌드다.

- **Flutter release 빌드 = AOT(Ahead-of-Time) 네이티브 컴파일.** Dart 코드가 미리 기계어로 굳어 나온다. JIT가 아니다.
- JIT가 아니니 iOS의 JIT 금지 규칙에 안 걸린다. **디버거 없이 혼자 뜬다.** 껐다 켜도, 재부팅해도 정상.

```bash
# debug(JIT) — 디버거 붙어 있어야만 삶
flutter run -d <device>

# release(AOT) — 단독 실행 가능
flutter run --release -d <device>
```

> 💡 실기기 "동작 검증"은 반드시 release로 해야 의미가 있다. debug로 되는 걸 확인해봤자, 사용자 손에서 도는 건 release라 검증이 안 된 셈이다.

## 두 번째 삽질: iOS 26에서 무선 설치가 실패

release로 빌드·서명까지 다 됐는데, 이번엔 **설치/실행 단계에서 막혔다.**

```
Could not run ... on device
```

폰이 케이블 없이 Wi-Fi로 붙어 있는 상태였는데, iOS 26의 **무선(wireless) 설치가 불안정**한 알려진 이슈였다. 빌드 산출물은 멀쩡한데 "run"(설치 + 실행 + attach)을 한 번에 하려다 무선 구간에서 엎어지는 거다.

그래서 실행까지 붙지 말고 **설치만** 시켰다. `flutter install`은 attach/run 없이 기기에 앱만 밀어 넣는다.

```bash
flutter install --release -d <device-id>
```

```
Installing com.facecamera to <device>...
Uninstalling old version...
# exit code 0
```

`exit 0` — 로그는 짧지만 설치 성공이다. 그다음은 **폰 홈 화면에서 아이콘을 직접 탭**해서 단독 실행. run으로 무선 attach를 시도하는 불안정 구간을 통째로 건너뛴 셈이다.

## 첫 실행 전에: 개발자 서명 신뢰

dev 서명으로 설치한 앱은 첫 실행 때 iOS가 막을 수 있다. 그러면:

```
설정 → 일반 → VPN 및 기기 관리 → 개발자 앱(내 개발자 이름) → 신뢰
```

한 번 신뢰하면 그다음부턴 그냥 뜬다.

> 💡 프로비저닝 프로파일 만료도 알아두면 좋다. **유료 개발자 계정(조직 팀)** 으로 서명하면 대략 1년, **무료 개인 팀**이면 약 7일 뒤에 만료돼서 재설치가 필요하다. 데모용 폰에 오래 물려둘 거면 유료 팀 서명이 편하다.

## Android도 같은 증상이었는데, 원인이 달랐다

재밌는 건 Android 폰에 올렸을 때도 **똑같이 "혼자 안 도는"** 증상이 났다는 거다. 그래서 처음엔 "아 이거 Flutter가 문제구나" 싶었는데, 파보니 원인이 iOS랑 완전히 달랐다.

- **Android는 debug 빌드도 JIT를 허용한다.** iOS 같은 OS 차원의 금지가 없다. 즉 Android는 debug APK를 홈에서 탭해도 단독 실행이 **된다.**
- 그럼 왜 안 됐나? 폰에 깔려 있던 게 **예전에 설치한 초기 debug APK(옛 코드)** 였다. 그 버전에 `CameraController` dispose 관련 크래시가 있어서 **켜자마자 죽은** 거다.
- 즉 Android 쪽은 빌드 모드 문제가 아니라 **코드 버그**였고, 그건 이번에 고쳤다(dispose 크래시 수정).

| | debug 단독 실행 | 안 되던 진짜 원인 |
| --- | --- | --- |
| **iOS** | ❌ 불가 | OS가 JIT를 디버거 없이 금지 (debug=JIT) |
| **Android** | ✅ 가능 | 옛 debug APK의 dispose 크래시 (코드 버그) |

**같은 증상, 다른 원인.** iOS는 빌드 모드(OS 제약), Android는 옛 코드 크래시. 우연히 둘 다 "혼자 안 뜸"으로 보였을 뿐이다.

## RN이랑 비교하면 — 사실 불공정한 비교였다

솔직히 짚고 갈 게 있다. 처음에 "RN은 되는데 Flutter는 안 된다"처럼 보였던 건, 비교 조건이 틀려서였다.

- 내가 보고 있던 RN 쪽 = **release(번들) 빌드** → 단독 실행 O
- 내가 돌린 Flutter 쪽 = **debug 빌드(`flutter run`)** → (iOS에선) 단독 실행 X

즉 **RN release vs Flutter debug**를 비교한 거다. 애초에 급이 안 맞는 비교였다. 같은 조건(둘 다 release)으로 놓으면 Flutter도 RN과 똑같이 단독 실행된다.

빌드 모드 개념 자체는 두 프레임워크가 닮았다.

| | 개발(dev/debug) | 배포(release) |
| --- | --- | --- |
| **RN** | Metro 번들러 + dev 서버 필요 | JS 번들 임베드 → 단독 |
| **Flutter** | Dart JIT (iOS는 디버거 필요) | AOT 네이티브 컴파일 → 단독 |

둘 다 "개발 모드는 붙어 있어야 편하고, 배포 모드는 혼자 돈다"는 같은 구조다. 차이라면 Flutter의 debug가 **JIT라서 iOS의 OS 정책에 정면으로 걸린다**는 점 정도. RN dev도 Metro가 없으면 못 도는 건 마찬가지라, "Flutter가 유독 나쁘다"는 결론은 틀렸다.

(반성 겸) 처음 데모를 `flutter run`(debug)으로 보여준 게 실수였다. 실기기 시연은 처음부터 release로 했어야 했다.


## 정리

- **같은 증상이라고 원인이 같은 게 아니다.** iOS의 "선 뽑으면 죽음" = debug(JIT)를 OS가 금지 → release(AOT)로 해결. Android의 "혼자 안 뜸" = 옛 debug APK의 dispose 크래시(코드 버그) → 코드 수정 + release로 해결.
- **Flutter 결함이 아니다.** iOS·Android 둘 다 release 빌드면 RN release와 똑같이 단독 실행된다. iOS는 release 설치로, Android는 새 release APK로 확인.
- 실기기 검증·데모는 처음부터 **release**로. debug로 되는 걸 봐봤자, 사용자 손에 가는 건 release다.
- iOS 부가 팁: 무선 `run`이 `Could not run ... on device`로 엎어지면 `flutter install --release`로 설치만, 첫 실행 전 개발자 앱 신뢰, 서명 유효기간(유료 ~1년/무료 ~7일).

이걸로 vision-camera → Flutter 재구현의 마지막 관문이던 실기기 검증(iOS·Android)까지 끝났다. 카메라·얼굴 인식·크롭 토글·FPS HUD 전부 폰에서 단독으로 도는 걸 눈으로 확인했다.

## 관련 작업
- `FaceCamera` — `feat: 가이드/크롭 토글, FPS·감지시간 HUD, iOS 실기기 대응 및 크래시 수정` (2026-08-21). RN→Flutter 마이그레이션 후 실기기 대응 마무리.
- 실기기 설치: iOS는 `flutter install --release`로 무선 `run` 실패(iOS 26) 우회, Android는 dispose 크래시 수정 후 release APK로 단독 실행 확인.
- 이 작업은 로컬 빌드/설치일 뿐 저장소·PR에 코드 변경으로 남기지 않았다(설치 트러블슈팅).
