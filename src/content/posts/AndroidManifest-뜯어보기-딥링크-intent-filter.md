---
title: "AndroidManifest 뜯어보기: 딥링크 intent-filter"
date: 2026-05-14
categories: ["Flutter"]
tags: ["Flutter", "Android", "AndroidManifest", "딥링크", "intent-filter"]
---

> RN → Flutter 전환 시리즈. 딥링크가 실제로 어떻게 라우팅되는지(cold start 처리 등)는 다른 글에서 다룬다. 이 글은 그 앞단, **AndroidManifest에서 딥링크가 앱으로 들어오는 입구를 어떻게 구성했는가**에 집중한다.

## 딥링크는 Manifest에서 시작한다

앱이 `myapp://...` 같은 링크를 받으려면, 먼저 OS에게 **"이 scheme은 내가 처리한다"**고 선언해야 한다. 그 선언이 `AndroidManifest.xml`의 `intent-filter`다. Flutter든 RN이든 이 부분은 결국 순수 안드로이드 영역이라, 여기가 틀리면 앱 코드가 아무리 완벽해도 링크가 안 들어온다.

## MainActivity의 intent-filter

우리 앱 진입 액티비티(`MainActivity`)에는 intent-filter가 두 개 붙어 있다.

```xml
<activity
    android:name=".MainActivity"
    android:exported="true"
    android:launchMode="singleTask"
    ... >

    <!-- 1) 런처 아이콘으로 앱을 켜는 기본 진입 -->
    <intent-filter>
        <action android:name="android.intent.action.MAIN"/>
        <category android:name="android.intent.category.LAUNCHER"/>
    </intent-filter>

    <!-- 2) myapp:// 커스텀 스킴 딥링크 진입 -->
    <intent-filter>
        <action android:name="android.intent.action.VIEW" />
        <category android:name="android.intent.category.DEFAULT" />
        <category android:name="android.intent.category.BROWSABLE" />
        <data android:scheme="myapp" />
    </intent-filter>
</activity>
```

두 번째 필터가 딥링크의 입구다. 요소 하나하나가 다 이유가 있다.

- `action.VIEW` — "이 URI를 열어라"라는 표준 액션.
- `category.DEFAULT` — 명시적 컴포넌트 지정 없이 이 액티비티가 후보가 되게 한다.
- `category.BROWSABLE` — **브라우저/웹뷰에서 링크를 눌렀을 때** 앱이 뜰 수 있게 한다. 이게 빠지면 웹에서 `myapp://` 링크를 눌러도 앱이 안 열린다. 딥링크에서 제일 자주 빠뜨리는 항목.
- `data android:scheme="myapp"` — 우리가 소유한 커스텀 스킴.

> 💡 `<data>`에 `scheme`만 있고 `host`가 없으면, `myapp://` 로 시작하는 **모든** 링크를 이 앱이 받는다. host별 라우팅(`myapp://community-landing/...` 등)은 Manifest가 아니라 앱 안의 라우터가 판단한다. Manifest는 "문을 여는" 역할, 라우팅은 앱의 몫으로 역할을 나눴다.

## 왜 host를 안 나눴나

`myapp://community/123`, `myapp://invite`, `myapp://community-landing/ownerReview`처럼 host가 제각각이다. Manifest에서 host마다 `<data>`를 늘어놓을 수도 있지만, 그러면 새 딥링크가 생길 때마다 Manifest를 고치고 재배포해야 한다.

그래서 **Manifest는 scheme까지만 받고, 그 다음은 전부 앱 라우터가 결정**하게 했다. 딥링크 종류가 늘어도 Manifest는 그대로다. 유연성 면에서 이게 훨씬 나았다.

## launchMode: singleTop → singleTask

작지만 중요한 변경. 원래 `singleTop`이었던 걸 `singleTask`로 바꿨다.

```xml
<!-- before -->
android:launchMode="singleTop"
<!-- after -->
android:launchMode="singleTask"
```

이유는 딥링크로 앱이 여러 번 진입할 때의 **태스크/인스턴스 관리** 때문이다. `singleTask`는 이 액티비티를 자기 태스크의 루트로 두고, 이미 떠 있으면 새로 만들지 않고 기존 인스턴스로 `onNewIntent`를 통해 인텐트를 전달한다. 딥링크가 이미 실행 중인 앱으로 들어올 때 화면이 중복 생성되거나 백스택이 꼬이는 문제를 줄인다.

## cold start를 위한 pending 캡처

여기서 Manifest와 네이티브 코드가 만난다. 앱이 **완전히 꺼진 상태(cold start)**에서 딥링크로 켜지면, Flutter 엔진이 준비되기 전에 인텐트가 먼저 도착할 수 있다. 이 타이밍을 놓치면 링크가 유실된다.

그래서 `MainActivity`(Kotlin)에서 인텐트를 받자마자 **pending으로 저장**해뒀다가, Flutter가 준비된 뒤 꺼내 쓰게 했다. `singleTask`라서 `onCreate`(최초 진입)와 `onNewIntent`(이미 떠 있을 때) 두 경로 모두 커버해야 한다.

```kotlin
class MainActivity: FlutterActivity() {
    private val PREFS_NAME = "myapp_prefs"
    private val PENDING_KEY = "pending_push_deeplink"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        capturePendingDeeplink(intent)      // cold start
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        capturePendingDeeplink(intent)      // 이미 실행 중일 때
    }

    private fun capturePendingDeeplink(intent: Intent?) {
        val extras = intent?.extras ?: return
        val url = extras.getString("url") ?: extras.getString("data.url")
        if (!url.isNullOrEmpty()) {
            getSharedPreferences(PREFS_NAME, MODE_PRIVATE)
                .edit()
                .putString(PENDING_KEY, url)
                .apply()
        }
    }
}
```

Dart 쪽에서는 `app_links` 플러그인으로 warm/cold 링크 스트림을 받되, 위에서 저장한 native pending 값도 같이 읽어 초기 진입을 처리한다. (이 라우팅 직렬화/중복 방지 로직은 별도 글 주제라 여기선 생략한다.)

## 곁다리: 다른 scheme들도 여기 산다

같은 Manifest에 딥링크 말고도 여러 콜백용 intent-filter가 공존한다. 정리해두면 나중에 헷갈리지 않는다.

```xml
<!-- 카카오 로그인 콜백 (SDK 2.0: AuthCodeHandlerActivity) -->
<activity android:name="com.kakao.sdk.flutter.auth.AuthCodeHandlerActivity" android:exported="true">
  <intent-filter android:label="flutter_web_auth">
      <action android:name="android.intent.action.VIEW" />
      <category android:name="android.intent.category.DEFAULT" />
      <category android:name="android.intent.category.BROWSABLE" />
      <data android:scheme="${kakao_scheme}" android:host="oauth"/>
  </intent-filter>
</activity>

<!-- 애플 로그인 콜백 -->
<activity android:name="com.aboutyou.dart_packages.sign_in_with_apple.SignInWithAppleCallback"
    android:exported="true">
  <intent-filter>
      <action android:name="android.intent.action.VIEW" />
      <category android:name="android.intent.category.DEFAULT" />
      <category android:name="android.intent.category.BROWSABLE" />
      <data android:scheme="myappsigninwithapple" />
      <data android:path="callback" />
  </intent-filter>
</activity>
```

- 카카오 콜백 scheme은 `${kakao_scheme}` **플레이스홀더**로 두고 gradle의 manifestPlaceholders로 주입한다. 키를 Manifest에 하드코딩하지 않는다.
- 이 콜백 액티비티들은 로그인 SDK **전용 진입점**이라 `MainActivity`와 별도 액티비티로 둔다. 딥링크(`myapp`)와 인증 콜백(`kakao`, `myappsigninwithapple`)의 책임을 섞지 않는 게 포인트다.

> 딥링크를 받으려면 `android:exported="true"`가 필요하다. Android 12+에서는 intent-filter를 가진 컴포넌트에 `exported` 명시가 강제되니, 값이 빠지면 아예 빌드가 안 된다.

## 정리

딥링크 구성은 결국 **역할 분담**이다.

- **Manifest** — "누가 문을 여는가": scheme 선언(`myapp`), `BROWSABLE`, `singleTask`.
- **네이티브(MainActivity)** — "cold start 인텐트를 놓치지 않기": `onCreate`/`onNewIntent`에서 pending 캡처.
- **앱 라우터(Dart)** — "어디로 보낼 것인가": host/path 기반 실제 라우팅.

Manifest에 scheme만 받고 host 라우팅은 앱에 맡긴 덕에, 딥링크가 늘어도 Manifest는 손대지 않는다. 그리고 `launchMode`와 `BROWSABLE` 같은 사소해 보이는 속성이 실제로는 "링크가 앱까지 도달하느냐"를 가른다.

