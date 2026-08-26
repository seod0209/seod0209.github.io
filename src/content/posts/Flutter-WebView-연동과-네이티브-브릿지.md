---
title: "Flutter WebView 연동과 네이티브 브릿지"
date: 2026-06-10
categories: ["Flutter"]
tags: ["Flutter", "WebView", "Bridge", "DeepLink", "Kakao"]
---

> 시리즈 '웹뷰·네이티브 연동' 1편. 회사 앱은 상당 부분이 웹(피키 웹뷰)으로 굴러간다. 앱 껍데기는 Flutter, 알맹이는 웹. 이 구조에서 제일 많이 터진 게 웹↔네이티브 경계였다.

앱을 하다 보면 "이거 그냥 웹뷰로 감싸면 되는 거 아냐?" 싶은 순간이 온다. 맞다. 근데 그 "그냥 감싸면"이 진짜 일이 되는 건 경계에서다. 웹이 모르는 스킴을 뱉을 때, 웹이 앱한테 뭘 시키고 싶을 때, 웹뷰가 웹뷰를 또 열 때. 이 글은 회사 앱에서 그 경계를 하나씩 정리한 기록이다.

## 1. 비표준 스킴이 앱을 터뜨린다

처음 만난 건 이거였다. 웹뷰 안에서 어떤 링크를 눌렀는데 Android는 `ERR_UNKNOWN_URL_SCHEME` 에러 페이지를 띄우고, iOS는 조용히 다른 앱으로 튕겨나가 버렸다. 같은 링크인데 플랫폼마다 반응이 다른 비대칭 상태. 띠용..?

원인은 웹이 `naversearchapp://`, `intent://` 같은 **비표준(래퍼) 스킴**을 던지는데 웹뷰가 이걸 어떻게 처리할지 우리가 정해준 적이 없어서였다. 기존 코드는 `tel / mailto / sms / geo` 정도만 외부로 넘기고 나머지는 전부 그냥 navigate시키고 있었다.

그래서 `onNavigationRequest`를 아예 재설계했다. 규칙은 이렇다.

- `http / https / about` → 웹뷰가 직접 로드
- 래퍼 딥링크(`naversearchapp / naverapp / daumapps`) → `url=` 파라미터에서 진짜 https를 꺼내 **인앱 로드**
- `intent://` → `S.browser_fallback_url`을 추출해 인앱 로드
- 위에서 다 실패하면 → **외부 앱으로 위임** (조용히 사라지는 케이스 방지)

```dart
/// url= 쿼리 파라미터로 실제 https URL을 감싸는 래퍼 딥링크 스킴들.
const Set<String> _wrapperSchemes = {'naversearchapp', 'naverapp', 'daumapps'};

onNavigationRequest: (NavigationRequest request) {
  final uri = Uri.tryParse(request.url);
  if (uri == null) return NavigationDecision.navigate;

  final scheme = uri.scheme.toLowerCase();

  // 표준 스킴은 그대로 통과
  if (scheme == 'http' || scheme == 'https' || scheme == 'about') {
    return NavigationDecision.navigate;
  }

  // 1) 래퍼 딥링크: url= 파라미터에서 실제 http(s)를 꺼내 인앱 로드
  if (_wrapperSchemes.contains(scheme)) {
    final inner = uri.queryParameters['url'];
    final innerUri = (inner != null && inner.isNotEmpty) ? Uri.tryParse(inner) : null;
    if (innerUri != null &&
        (innerUri.scheme == 'http' || innerUri.scheme == 'https')) {
      controller.loadRequest(innerUri);
      return NavigationDecision.prevent;
    }
  }

  // 2) Android intent://...;S.browser_fallback_url=...;end → 있으면 인앱 로드
  if (scheme == 'intent') {
    final fallback = _intentFallbackUrl(request.url);
    final fbUri = (fallback != null && fallback.isNotEmpty) ? Uri.tryParse(fallback) : null;
    if (fbUri != null) {
      controller.loadRequest(fbUri);
      return NavigationDecision.prevent;
    }
  }

  // 3) 그 외 커스텀 스킴 + 위에서 폴스루된 케이스 → 외부 앱 위임
  unawaited(_launchExternalIfPossible(uri));
  return NavigationDecision.prevent;
},
```

`intent://` 파싱은 문자열 노가다다. `#Intent;` 뒤에서 `S.browser_fallback_url=`을 찾아 디코드한다.

```dart
String? _intentFallbackUrl(String intentUrl) {
  final i = intentUrl.indexOf('#Intent;');
  if (i == -1) return null;
  final body = intentUrl.substring(i + '#Intent;'.length);
  final endIdx = body.lastIndexOf(';end');
  final params = (endIdx == -1 ? body : body.substring(0, endIdx)).split(';');
  const key = 'S.browser_fallback_url=';
  for (final part in params) {
    if (part.startsWith(key)) {
      try {
        return Uri.decodeComponent(part.substring(key.length));
      } catch (_) {
        return null;
      }
    }
  }
  return null;
}
```

여기서 하나 더. navigation delegate에서 막아도 redirect/iframe 체인을 타고 에러가 **한 박자 늦게** 새어 올라온다. 정상 페이지인데 로딩 실패로 기록되는 걸 막으려고 `onWebResourceError`에서 이 스킴 에러는 걸러줬다.

```dart
onWebResourceError: (WebResourceError error) {
  final desc = error.description.toLowerCase();
  final isUnknownScheme = desc.contains('err_unknown_url_scheme') ||
      desc.contains('unsupported_url');
  if (isUnknownScheme) return; // 정상 페이지가 fail로 기록되는 것 방지
  // ... 실제 에러 처리
},
```

마지막으로 OS가 "이 앱 설치돼 있어?"를 물어볼 수 있게 매니페스트/plist에 조회 대상을 등록해야 한다. 안 그러면 `canLaunchUrl`이 항상 false를 뱉는다.

```xml
<!-- AndroidManifest.xml <queries> -->
<intent>
  <action android:name="android.intent.action.VIEW" />
  <data android:scheme="https" />
</intent>
<package android:name="com.kakao.talk" />
<package android:name="com.nhn.android.search" />
```

```xml
<!-- iOS Info.plist -->
<key>LSApplicationQueriesSchemes</key>
<array>
  <string>kakaotalk</string>
  <string>naversearchapp</string>
  <string>naverapp</string>
  <string>daumapps</string>
  <string>itms-apps</string>
  <!-- ... -->
</array>
```

## 2. 카카오 로그인이라는 단골 크래시

웹뷰 얘기하다 카카오가 안 나올 수 없다. 두 건이 있었다.

첫째, **웹뷰용 JavaScript 앱 키 누락.** 카카오 SDK 초기화 시 네이티브 앱 키만 넣고 있었는데, 웹뷰에서 도는 카카오 로그인은 JavaScript 키가 필요했다. 키 한 줄 추가로 해결.

```dart
void initializeKakao({required String? flavor}) {
  KakaoSdk.init(
    nativeAppKey: flavor == 'development'
        ? '<DEV_NATIVE_APP_KEY>'   // 실제 키는 마스킹
        : '<PROD_NATIVE_APP_KEY>',
    javaScriptAppKey: '<JS_APP_KEY>',
  );
}
```

둘째, **SDK 2.0 마이그레이션 후 Android 네이티브 크래시.** 카카오계정 웹 로그인을 마치고 `kakao{appkey}://oauth`로 앱에 복귀하는 순간 `ClassNotFoundException`으로 앱이 죽었다. Dart의 try/catch 바깥, 순수 네이티브 크래시라 잡히지도 않았다.

원인은 리다이렉트 핸들러 Activity 경로가 SDK 2.0에서 옮겨간 것. 매니페스트가 2.0에 없는 옛 클래스를 가리키고 있었다.

```xml
<!-- kakao_flutter_sdk 2.0: AuthCodeCustomTabsActivity → auth.AuthCodeHandlerActivity 로 이동 -->
<activity
    android:name="com.kakao.sdk.flutter.auth.AuthCodeHandlerActivity"
    android:exported="true">
  <intent-filter android:label="flutter_web_auth">
    <action android:name="android.intent.action.VIEW" />
    <category android:name="android.intent.category.DEFAULT" />
    <!-- ... -->
  </intent-filter>
</activity>
```

> 💡 SDK 메이저 버전 올릴 때 매니페스트에 하드코딩된 벤더 클래스명은 꼭 릴리스 노트랑 대조하자. 컴파일도 통과하고 Dart에서도 안 잡히고, 오직 실기기에서만 죽는다.

## 3. 웹→앱 브릿지 프로토콜을 문서로 못 박다

경계가 복잡해지니 "이 target이 뭐 하는 거였지?"를 매번 코드 뒤져서 확인하고 있었다. 그래서 브릿지 프로토콜을 문서로 정리했다. 채널 구조는 이렇다.

| 방향 | 메커니즘 | 진입점 |
|---|---|---|
| **Web → App** | `window.MyAppBridge.postMessage(<JSON string>)` (JavaScriptChannel) | `_onMessage()` |
| **App → Web** | `window.postMessage(<JSON string>, "*")` + `window.isNativeApp = true` 주입 | `sendToWebView()` |

- 채널 이름은 `MyAppBridge`로 고정. 모든 페이로드는 JSON 문자열.
- App→Web 호출 때마다 `window.isNativeApp = true`를 먼저 주입해서 웹이 네이티브 환경을 판별하게 한다.
- 웹이 보내는 메시지는 `target` 키로 디스패치한다. 표에 없는 target은 `Webview Bridge 미정의` 로그만 남기고 무시.

웹이 던지는 메시지는 전부 `@SafeString` / `@SafeInt` / `@SafeBool`로 타입 방어를 걸어서 파싱한다. 웹이 뭘 어떻게 보낼지 100% 믿을 수 없기 때문이다.

```dart
// Web → App: target으로 분기
switch (model.target) {
  case 'handleLink':   // 링크 라우팅
  case 'navigate':     // 네이티브 라우트 push
  case 'share':        // 공유 시트
  case 'getFromAsyncStorage':  // 저장소 읽어 응답
  case 'toast':        // 토스트
  // ... 정의되지 않은 target은 무시
}
```

App→Web으로 내려보내는 공통 헤더도 규약으로 고정했다.

```dart
// App → Web 공통 헤더 블록 (init/mount 응답에 포함)
final headers = {
  'x-cha-agent': 'flutter',
  'x-app-version': packageInfo.version,
  'x-cha-os': isAndroid ? 'android' : 'ios', // macOS는 ios로 매핑
  'x-picky-session-id': sessionId,
  if (deviceId != null) 'x-picky-device-id': deviceId,
};
```

> 프로토콜을 코드가 아니라 문서로 못 박으니, 웹팀이랑 "그 target 필드 이름 뭐였죠"로 핑퐁하는 시간이 확 줄었다. 경계 규약은 한쪽 코드에만 살면 안 된다.

## 4. 웹뷰 이중구조 제거 — 인플레이스 연동

가장 크게 뜯어고친 건 웹뷰가 웹뷰를 쌓는 구조였다. 웹 안에서 웹 링크(웹→웹 SELF 링크)를 누를 때마다 새 `/Web` 라우트를 push하고 있었다. 즉 WebView 위에 WebView가 계속 쌓였다.

증상은 두 갈래로 왔다.

**(1) 웹→웹 링크가 아예 안 열림.** 이미 `Routes.WEB` 위에 있는데 같은 라우트를 push하니 GetX가 `preventDuplicates:true` 기본값 때문에 "같은 라우트네" 하고 무시했다. 아무 반응이 없었다. 처음엔 이걸 중복 허용으로 풀어서 새 WEB을 쌓게 했는데...

**(2) 그랬더니 WebView 인스턴스가 무한히 쌓여 OOM 위험.** 그래서 살아있는 `/Web` 인스턴스를 직접 카운트해서 한도(3) 도달 시 push 대신 replace하도록 임시방어까지 했다.

근데 이건 결국 대증요법이었다. 진짜 해법은 **애초에 새 웹뷰를 안 쌓는 것**. 이미 WEB 위에 있으면 새 라우트를 만들지 말고 **현재 WebView에 그대로 loadRequest**하면 된다. 이게 인플레이스 연동이다.

```dart
case 'SELF':
  if (!href.startsWith('myapp://')) {
    final isOnWeb = Get.currentRoute == Routes.WEB.name;
    final controller = WebPage.activeController;

    // 이미 WEB 위면 새 WebView 를 쌓지 않고 현재 WebView 에 직접 로드.
    // 상대경로(/community/...)는 현재 페이지 URL 을 base 로 해석
    // → scheme 누락으로 인한 loadRequest 크래시 방지.
    if (isOnWeb && controller != null) {
      final base = await controller.currentUrl();
      final target = (base != null && base.isNotEmpty)
          ? Uri.tryParse(base)?.resolve(href)
          : Uri.tryParse(href);

      if (target != null && target.hasScheme) {
        await controller.loadRequest(target);
      } else {
        MyAppToast.show('열 수 없는 링크에요');
      }
      break;
    }

    // 네이티브 → 웹: 절대 http(s) URL 만 새 WebView 로 연다.
    final uri = Uri.tryParse(href);
    if (uri != null && uri.hasScheme) {
      Navigation.push(Routes.WEB.name,
          arguments: {'url': href, 'title': headerTitle ?? '회사'});
    } else {
      MyAppToast.show('열 수 없는 링크에요');
    }
    break;
  }
```

여기서 놓치기 쉬운 함정이 상대경로였다. 웹이 `/community/123` 같은 scheme 없는 경로를 던지면 `loadRequest`가 크래시난다. 그래서 **현재 페이지 URL을 base로 resolve**해서 절대 URL로 만든 다음에만 로드한다.

인플레이스로 바꾸니 헤더 처리도 손봐야 했다. 라우트가 안 바뀌니 `onUrlChange`에서 헤더를 재평가해서, 서브페이지로 이동하면 뒤로가기 헤더를 복원하도록 했다.

성과는 명확했다. WebView 인스턴스 누적으로 인한 OOM 리스크가 사라졌고, 웹→웹 링크가 스택을 쌓지 않으니 뒤로가기 동작도 예측 가능해졌다. `_maxWebDepth` 같은 방어 상수도 통째로 지웠다. 대증요법을 걷어내고 원인을 없앤 셈이다.

## 정리

- 웹뷰 경계는 "스킴"에서 제일 많이 샌다. 표준/래퍼/intent/커스텀을 명시적으로 분기하고, 애매하면 외부 위임으로 폴스루.
- 벤더 SDK 메이저 업 시 매니페스트의 하드코딩 클래스명이 조용한 네이티브 크래시의 단골이다.
- 웹↔앱 브릿지는 한쪽 코드에만 두지 말고 규약 문서로 못 박자.
- 웹뷰가 웹뷰를 쌓는 구조는 언젠가 OOM으로 돌아온다. 인플레이스 로드로 애초에 안 쌓는 게 정답이었다.

