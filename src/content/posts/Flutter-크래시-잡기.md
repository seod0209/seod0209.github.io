---
title: "Flutter 크래시 잡기: WebView dispose와 scheme 누락 방어"
date: 2026-06-10
categories: ["Flutter"]
tags: ["Flutter", "WebView", "Crashlytics", "크래시"]
---

> RN → Flutter 전환 시리즈의 크래시 편. 스토어 나가고 나서 Crashlytics에 쌓인 상위 크래시 두 개 — WebView dispose 시 `NSInternalInconsistencyException`, 그리고 scheme 누락 링크로 `loadRequest`가 터지는 문제 — 를 어떻게 막았는지 적는다.

## 크래시는 대부분 "경계"에서 터진다

앱 로직 안쪽은 의외로 잘 안 죽는다. 죽는 건 항상 **네이티브 경계**다. WebView, 딥링크, 이미지 로더 같은, Flutter와 OS 사이를 오가는 지점. 이번에 잡은 것도 전부 거기서 났다.

## 1. WebView dispose 시 NSInternalInconsistencyException

iOS에서 유독 이 크래시가 잡혔다. WebView가 있는 화면을 빠르게 들락거리면 가끔 앱이 죽었다.

원인은 이렇다. `WKWebView`가 dealloc 되는 시점에, 아직 끝나지 않은 JS 콜백이나 navigation 콜백이 **이미 정리된 FlutterEngine 쪽으로 전달**되면서 `NSInternalInconsistencyException`이 난다. 화면을 빨리 닫을수록 이 race에 걸릴 확률이 올라간다.

해결은 dispose 시점에 **채널/델리게이트/페이지를 명시적으로 끊어주는 것**. dealloc 전에 붙어 있는 걸 미리 떼어내서 pending 콜백이 갈 곳을 없애준다.

```dart
@override
void dispose() {
  EnvironmentService.to.routeObserver.unsubscribe(this);
  _lifecycleListener.dispose();

  // WKWebView dealloc 시 pending JS/navigation 콜백이 이미 종료된
  // FlutterEngine 으로 전달되어 NSInternalInconsistencyException 발생.
  // 명시적으로 채널/delegate/페이지를 정리해 race 가능성을 줄인다.
  try {
    _webViewController.removeJavaScriptChannel('MyAppBridge');
    _webViewController.setNavigationDelegate(NavigationDelegate());
    _webViewController.loadRequest(Uri.parse('about:blank'));
  } catch (_) {}

  super.dispose();
}
```

포인트는 `try/catch`로 통째로 감싼 것. dispose 시점에 컨트롤러가 이미 반쯤 죽어 있을 수도 있으니, 여기서 나는 예외로 또 죽으면 본말전도다. **정리 과정 자체는 실패해도 조용히 넘긴다.**

## 2. scheme 누락 링크로 loadRequest가 터짐

두 번째는 WebView 안에서 링크를 눌렀을 때다. 웹→웹으로 이동하는 SELF 링크가 있는데, 이게 두 가지 문제를 동시에 갖고 있었다.

1. **웹 링크를 누를 때마다 새 `/Web` 라우트를 쌓았다.** WebView 인스턴스가 계속 누적 → OOM.
2. **상대경로(`/community/123` 같은)를 그대로 `loadRequest`에 넘겼다.** scheme(`http(s)://`)이 없으니 `Uri`가 유효하지 않고, 이 상태로 `loadRequest`를 부르면 크래시.

처음엔 1번을 "스택 깊이 제한"으로 막았었다. `activeInstances` 카운터를 두고 최대 깊이(3)를 넘으면 새로 쌓지 않고 현재 WEB을 replace 하는 식. 근데 이건 증상 완화지 해결이 아니었다.

제대로 고친 방향은 **이중 웹뷰 자체를 없애는 것**. 이미 WEB 위에 있으면 새 라우트를 쌓지 말고, 살아있는 컨트롤러에 **인플레이스로 직접 로드**한다. 그리고 상대경로는 현재 페이지 URL을 base로 삼아 절대 URL로 resolve 한다.

```dart
// WebPage 는 현재 살아있는 컨트롤러를 정적으로 노출한다.
class WebPage extends StatefulWidget {
  /// 살아있는 /Web 라우트의 WebView 컨트롤러.
  /// 웹→웹 SELF 링크를 새 WebView 로 쌓지 않고(이중 웹뷰/OOM 방지)
  /// 이 컨트롤러에 직접 로드(인플레이스)하기 위해 노출한다.
  static WebViewController? activeController;
}
```

```dart
// Navigation.handleLink — SELF 링크 처리
final isOnWeb = Get.currentRoute == Routes.WEB.name;
final controller = WebPage.activeController;

if (isOnWeb && controller != null) {
  final base = await controller.currentUrl();
  // 상대경로는 현재 페이지 URL 을 base 로 해석 → scheme 누락 크래시 방지
  final target = (base != null && base.isNotEmpty)
      ? Uri.tryParse(base)?.resolve(href)
      : Uri.tryParse(href);

  if (target != null && target.hasScheme) {
    await controller.loadRequest(target); // 인플레이스 로드
  } else {
    MyAppToast.show('열 수 없는 링크에요');
  }
  return;
}

// 네이티브 → 웹: base 가 없으니 절대 http(s) URL 만 새 WebView 로.
final uri = Uri.tryParse(href);
if (uri != null && uri.hasScheme) {
  Navigation.push(Routes.WEB.name, arguments: {'url': href, 'title': headerTitle ?? '회사'});
} else {
  MyAppToast.show('열 수 없는 링크에요'); // scheme 없으면 무시(크래시 방지)
}
```

핵심 원칙은 두 개다.

- **`loadRequest` 앞에서는 항상 `target.hasScheme`을 확인한다.** scheme 없는 URI는 절대 넘기지 않는다.
- **웹→웹은 새 뷰를 쌓지 않고 인플레이스로 로드한다.** WebView 누적이 원천적으로 안 생긴다.

이렇게 하니 깊이 제한 카운터(`activeInstances`, `_maxWebDepth`)가 통째로 필요 없어져서 같이 지웠다.

## 3. 겸사겸사: 회복 가능한 에러는 non-fatal로

크래시를 잡다 보면 "이건 앱이 죽는 게 아니라 그냥 로그만 쌓이는 거"인 경우가 많다. 네트워크 일시 단절, 이미지 다운로드 실패, 스크롤 중 dispose된 이미지 위젯 race 같은 것들. 이런 건 fatal로 올리면 크래시 지표만 오염된다.

그래서 Crashlytics에 올릴 때 **회복 가능한 에러는 non-fatal로 분류**했다. 판정은 타입 이름 + 메시지 + 스택 문자열을 같이 본다.

```dart
static bool _isRecoverableError(Object error, [StackTrace? stack]) {
  final typeName = error.runtimeType.toString();
  const recoverableTypes = {'ClientException', 'SocketException', /* ... */};
  if (recoverableTypes.contains(typeName)) return true;

  final message = error.toString();
  if (message.contains('Connection closed') ||
      message.contains('Connection reset') ||
      message.contains('Failed host lookup')) {
    return true;
  }

  // octo_image / cached_network_image 등 이미지 위젯의 라이프사이클 race
  // (스크롤 중 dispose 된 부모 Element 접근 등)는 라이브러리 버그성 → non-fatal.
  final stackString = stack?.toString() ?? '';
  if (stackString.contains('octo_image') ||
      stackString.contains('cached_network_image') ||
      stackString.contains('image_provider.dart')) {
    return true;
  }
  return false;
}
```

```dart
FlutterError.onError = (errorDetails) {
  if (_isRecoverableError(errorDetails.exception, errorDetails.stack)) {
    FirebaseCrashlytics.instance.recordFlutterError(errorDetails);      // non-fatal
  } else {
    FirebaseCrashlytics.instance.recordFlutterFatalError(errorDetails); // fatal
  }
};
```

> 💡 처음엔 `error.runtimeType`만 봤는데, `dart:io`의 `HttpException`/`HandshakeException`이 일부 Flutter 버전에서 `_HttpException` 같은 private 타입으로 노출되면서 타입 매칭에서 새 나갔다. 그래서 `error.toString()` 기반 매칭 + TLS/OS 레벨 패턴(`CERTIFICATE_VERIFY_FAILED`, `Handshake error` 등)을 추가했다.

## 결론

크래시 대응의 절반은 "안 죽게 막기", 나머지 절반은 "죽는 것과 안 죽는 것을 지표에서 구분하기"다. 네이티브 경계(WebView dispose, scheme 누락)에서는 **정리 순서와 사전 검증**으로 죽음을 막고, 어차피 회복되는 에러는 **non-fatal로 분류**해서 진짜 크래시가 묻히지 않게 했다.

