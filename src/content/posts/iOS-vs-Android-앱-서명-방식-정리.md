---
title: "iOS vs Android 앱 서명 방식 정리"
date: 2026-04-29
categories: ["CI/CD"]
tags: ["Flutter", "코드서명", "keystore", "provisioning-profile", "iOS", "Android"]
---

> RN → Flutter 전환 시리즈. Shorebird 배포 파이프라인을 만들면서 CI에서 두 플랫폼의 코드 서명을 세팅해야 했다. iOS와 Android가 서명을 대하는 방식이 근본부터 달라서, 한 번 정리해두면 두고두고 도움이 된다.

## 두 플랫폼은 서명을 다르게 본다

한 줄 요약부터.

- **Android**: 개발자가 만든 **keystore**로 APK/AAB에 직접 서명한다. 키 관리 주체가 나(혹은 Play App Signing).
- **iOS**: Apple이 발급한 **인증서(certificate) + 프로비저닝 프로파일(provisioning profile)** 조합으로 서명한다. 애초에 Apple의 통제 아래 있다.

그래서 CI에서 준비하는 파일도, 실패하는 방식도 다르다.

## Android: keystore 하나로 끝

Android는 릴리스 keystore 파일 하나와 그 비밀번호/alias만 있으면 된다. `build.gradle`의 `signingConfigs.release`가 `local.properties`(CI에선 `key.properties`)에서 값을 읽어 서명한다.

```groovy
signingConfigs {
    release {
        def keystoreFileName = localProperties.getProperty('keystore.file')
        if (keystoreFileName != null && file(keystoreFileName).exists()) {
            storeFile file(keystoreFileName)
            storePassword localProperties.getProperty('keystore.password', '')
            keyAlias localProperties.getProperty('keystore.keyAlias', '')
            keyPassword localProperties.getProperty('keystore.keyPassword', '')
        } else {
            // keystore 정보가 없으면 release 빌드 시점에 명확히 에러
            logger.warn("⚠️ Release keystore not configured. Production build will fail.")
        }
    }
}
```

CI에서는 안전한 위치에 둔 keystore를 빌드 전에 프로젝트로 복사해 넣는다.

```bash
cp ~/github/myapp.keystore ./android/app/myapp.keystore
cp ~/github/key.properties  ./android/key.properties || true
```

### 삽질: 파일 이름이 어긋났다

여기서 실제로 하루를 날린 버그. keystore 원본은 `myapp.keystore`인데, CI 스크립트가 이걸 `store.keystore`라는 이름으로 복사하고 있었다.

```bash
# 문제: 원본은 myapp.keystore 인데 store.keystore 로 복사
cp ~/github/myapp.keystore ./android/app/store.keystore
```

근데 `build.gradle`이 기대하는 파일명은 `myapp.keystore`. 이름이 어긋나니 gradle이 keystore를 못 찾고, release 빌드가 조용히(혹은 애매한 메시지로) 깨졌다. 고친 건 단순하다. **복사 대상 파일명을 실제 참조명과 일치**시켰다.

```bash
# 수정: 참조하는 이름 그대로 복사
cp ~/github/myapp.keystore ./android/app/myapp.keystore
```

프로젝트 안에서 `store`니 `myapp`이니 이름이 섞여 있던 것도 이때 `myapp`으로 통일했다. **서명 파일 이름은 한 곳에서만 정하고 나머지는 그대로 따라가야** 이런 미스가 안 난다.

> 💡 keystore와 비밀번호는 절대 저장소에 커밋하지 않는다. CI 러너의 보호된 경로(`~/github/…`)나 secret에서 빌드 시점에만 주입한다.

> 💡 한 가지 정확히 하고 가자. 위 keystore로 "내가 최종 서명"하는 건 **Play App Signing을 안 쓸 때**의 얘기다. Play App Signing을 켜면 개발자가 가진 keystore는 앱 서명 키가 아니라 **업로드 키**가 되고, 스토어에 올릴 AAB는 이 업로드 키로 서명한다. 실제 배포용 **앱 서명 키**는 Google이 보관·수행한다. 즉 최종 서명 주체가 개발자가 아니라 Google로 넘어가고, 업로드 키는 분실 시 재발급이 가능하다는 점이 다르다.

## iOS: 인증서 + 프로비저닝 + p8

iOS는 손이 더 간다. 준비물이 세 종류.

1. **프로비저닝 프로파일** — 어떤 App ID / 기기 / 인증서로 서명할지 정의.
2. **배포 인증서** — Apple이 발급한 distribution certificate.
3. **App Store Connect API 키(`.p8`)** — fastlane이 업로드/메타데이터를 다룰 때 인증용.

CI에서는 이것들을 credentials 디렉터리에 복사해 넣는다.

```bash
mkdir -p ./ios/credentials
cp ~/github/fastlane-apple-appstore-credentials.p8 ./ios/credentials/
```

> ⚠️ 여기서 `.p8`은 **코드 서명 자산이 아니다.** iOS 코드 서명은 인증서 + 프로비저닝 프로파일이 담당하고, `.p8`은 App Store Connect API(및 APNs)용 인증 키라 fastlane이 빌드 산출물을 **업로드/메타데이터 처리**할 때 쓰인다. 서명 준비물과 같은 디렉터리에 두다 보니 헷갈리기 쉽지만, 역할은 서명이 아니라 API 인증이다.

그리고 빌드 시 **어떤 프로파일로 서명할지**를 `ExportOptions.plist`로 명시한다. iOS의 핵심이 이 파일이다.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<plist version="1.0">
<dict>
    <key>method</key>
    <string>app-store</string>
    <key>provisioningProfiles</key>
    <dict>
        <key>kr.myapp</key>
        <string>MyApp-Distribution</string>
        <key>kr.myapp.NotiflyNotificationExtension</key>
        <string>MyApp-Distribution_NotificationExtension</string>
    </dict>
    <key>signingStyle</key>
    <string>manual</string>
    <key>teamID</key>
    <string>YOUR_TEAM_ID</string>   <!-- 실제 팀 ID는 secret/치환 -->
</dict>
</plist>
```

포인트 두 가지.

- **번들 ID마다 프로파일을 지정한다.** 앱 본체(`kr.myapp`)뿐 아니라 알림 확장(`NotificationExtension`) 같은 extension도 각자 프로파일이 필요하다. 하나라도 빠지면 아카이브가 실패한다.
- **`signingStyle`을 `manual`로 둔다.** CI에서는 자동 서명이 오히려 예측 불가라, 프로파일을 명시적으로 물리는 게 안전하다.

Shorebird release에도 이 plist를 그대로 물린다. (dev/prod용을 따로 뒀다.)

```yaml
- name: 🚀 Shorebird Release iOS (production)
  run: |
    shorebird release ios \
      --flutter-version=3.41.6 \
      --flavor=production \
      --export-options-plist=ios/ExportOptions-Production.plist \
      --dart-define-from-file=env.production.json
```

### 삽질: 카카오 프로덕션 키 누락

iOS 쪽에서도 비슷한 "누락" 버그가 있었다. 프로덕션 빌드에서 카카오 로그인이 안 됐는데, iOS 프로덕션 설정에 카카오 네이티브 앱 키가 빠져 있었다. dev에는 있는데 prod에는 없던 케이스. **환경별로 키/설정을 나눠 관리하면 한쪽에만 빠지는 실수가 꼭 난다.** 그래서 "prod에 있어야 할 키 목록"을 체크리스트로 못박았다.

## dev / production 분리

Android든 iOS든, 우리는 서명 자산을 **dev와 production으로 완전히 분리**했다.

- Android: dev/alpha는 Firebase App Distribution용 credentials, production은 Play Store용 credentials.
- iOS: dev는 `ExportOptions-Development.plist`(+ development 프로파일), production은 `ExportOptions-Production.plist`(+ distribution 프로파일).

이렇게 나눠두면 "내부 배포 빌드가 실수로 실사용자 서명으로 나가는" 사고를 구조적으로 막는다.

## 정리 표

| | Android | iOS |
|---|---|---|
| 서명 자산 | keystore(`.keystore`) + 비번/alias | 인증서 + 프로비저닝 프로파일 (`.p8`은 서명 자산 아님·API 인증 키) |
| 서명 주체 | 개발자(또는 Play App Signing) | Apple 통제 |
| 빌드 설정 | `build.gradle signingConfigs` | `ExportOptions.plist` |
| 흔한 실패 | keystore 파일명/경로 불일치 | 프로파일/번들ID 매핑 누락 |
| 환경 분리 | credentials json 분리 | plist(dev/prod) 분리 |

## 결론

Android는 "내 keystore로 내가 서명", iOS는 "Apple이 준 프로파일로 서명"이라는 근본 차이를 이해하면 CI 세팅이 한결 명료해진다. 실전에서 우리를 괴롭힌 건 거창한 게 아니라 **이름 하나(`store` vs `myapp`), 키 하나(카카오 prod), 프로파일 매핑 하나** 같은 사소한 불일치였다. 그래서 자산 이름과 환경별 목록을 한 곳에서 못박고, dev/prod를 물리적으로 분리하는 게 답이었다.

