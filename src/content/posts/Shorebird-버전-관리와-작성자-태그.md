---
title: "Shorebird 버전 관리와 작성자 태그"
date: 2026-06-01
categories: ["CI/CD"]
tags: ["Flutter", "Shorebird", "버전관리", "versionCode"]
---

> Shorebird 배포 편에서 이어지는 버전 관리 편. OTA 코드푸시를 굴리다 보면 "이 사용자가 지금 정확히 어떤 버전 + 몇 번 패치를 쓰고 있나"가 미궁이 된다. 버전 문자열을 앱에 노출하고, versionCode를 어떻게 계산하고, Shorebird가 요구하는 Flutter 버전을 어떻게 못박았는지 정리한다.

## OTA는 "버전"을 흐린다

스토어 배포만 있을 땐 버전이 깔끔하다. `9.0.5+123` 하나면 끝. 근데 Shorebird 패치가 끼면 얘기가 달라진다. 같은 `9.0.5+123` 위에 patch #1, #2, #3이 계속 얹힌다. 사용자가 "버그 있어요" 하면 우리는 되묻는다. **"버전이랑 패치 번호 좀 알려주세요."** 그런데 앱 어디에도 그게 안 떠 있으면? 재현이 안 된다.

그래서 버전 관리의 첫걸음은 **버전 문자열을 앱에 정직하게 노출**하는 거였다.

## 앱에 버전 + 패치 번호 표시

설정 화면에 `VersionInfo` 위젯을 뒀다. `package_info_plus`로 base 버전을, `ShorebirdService`로 현재 적용된 patch 번호를 읽어 합친다.

```dart
Future<void> _loadVersion() async {
  final packageInfo = await PackageInfo.fromPlatform();
  final currentPatch = await ShorebirdService.instance.getCurrentPatch();

  final baseVersion = 'v${packageInfo.version}+${packageInfo.buildNumber}';
  final patchSuffix = currentPatch != null
      ? ' (patch ${currentPatch.number})'
      : '';

  if (mounted) {
    setState(() => _versionText = '$baseVersion$patchSuffix');
  }
}
```

그러면 화면에 `v9.0.5+123 (patch 2)` 같은 문자열이 뜬다. **이거 하나로 QA/CS 응대가 확 편해졌다.** patch 번호는 Shorebird 콘솔의 그것과 그대로 매칭된다.

```dart
Future<Patch?> getCurrentPatch() async {
  try {
    return await _updater.readCurrentPatch();
  } catch (_) {
    return null;
  }
}
```

## 숨은 개발자 메뉴 (작성자 태그의 정체)

버전 텍스트에 한 가지를 더 얹었다. **버전 문구를 7번 탭하면 숨겨진 개발자 메뉴**로 들어간다. 여기서 베타 채널(Shorebird의 `beta` track) 토글 같은 걸 켤 수 있게 했다. 실사용자에겐 그냥 회색 버전 텍스트지만, 개발자/QA는 여기로 내부 track을 붙는다.

> ⚠️ 참고로 Shorebird의 `UpdateTrack`에는 `staging`이라는 상수가 따로 없다. 기본 제공되는 건 `UpdateTrack.stable`과 `UpdateTrack.beta`뿐이고, 그 외 이름(예: `staging`)은 `UpdateTrack.custom('staging')`이나 CLI의 `--track` 커스텀 트랙으로 다룬다. 그래서 내부 QA 채널은 `beta` 트랙이나 커스텀 트랙으로 잡는 게 맞다.

```dart
void _handleTap() {
  _tapCount++;
  if (_tapCount >= 7) {
    _tapCount = 0;
    // 7번 탭하면 숨겨진 개발자 메뉴로 이동
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => const HiddenDevMenu()),
    );
  }
}
```

여기에 **꾹 누르기(long press) → 버전 정보 복사**도 붙였다. 사용자가 문의할 때 버전 문자열을 직접 타이핑하지 않고 복사해서 붙여넣을 수 있게. "버전 정보가 복사되었습니다." 토스트까지.

## versionCode: 10만 단위를 걷어내다

Android `versionCode` 얘기. 한동안 이런 코드를 썼었다.

```groovy
// android/app/build.gradle (이전)
versionCode = flutter.versionCode.toInteger() + 100000
```

`+ 100000`을 왜 붙였냐면, RN 시절/초기 빌드와 번호 충돌을 피하려는 임시방편이었다. 근데 이게 Shorebird release-version 매칭이랑 자꾸 어긋났다. Shorebird는 release를 `versionName+versionCode`로 식별하는데, 여기 붙인 오프셋 때문에 "어떤 release에 패치를 붙여야 하는지"가 헷갈렸다.

그래서 오프셋을 없애고 **pubspec의 값을 그대로** 쓰도록 정리했다.

```groovy
// android/app/build.gradle (이후)
versionCode = flutter.versionCode.toInteger()
versionName = flutter.versionName
```

원칙은 하나. **버전의 단일 출처(source of truth)는 `pubspec.yaml`이다.** gradle이나 로컬 properties에서 버전을 따로 만지지 않는다. (`local.properties`에 남아 있던 버전 정보도 이때 같이 제거했다.)

## Shorebird가 요구하는 Flutter 버전 고정

가장 아팠던 교훈. **Shorebird 패치는 release를 만든 Flutter 버전과 정확히 같은 버전으로 만들어야 한다.** 버전이 어긋나면 패치가 안 붙거나, 붙어도 런타임에서 이상하게 논다.

CI에서 Flutter를 `subosito/flutter-action`으로 깔면 캐시나 기본값 때문에 버전이 미묘하게 달라질 수 있었다. 그래서 release 커맨드 자체에 **`--flutter-version`을 명시**해서 못박았다.

```yaml
- name: 🚀 Shorebird Release Android (production)
  run: |
    shorebird release android \
      --flutter-version=3.41.6 \
      --flavor=production -- \
      --build-number=${{ env.NEW_BUILD_NUMBER }} \
      --dart-define-from-file=env.production.json

- name: 🚀 Shorebird Release iOS (production)
  run: |
    shorebird release ios \
      --flutter-version=3.41.6 \
      --flavor=production \
      --export-options-plist=ios/ExportOptions-Production.plist \
      --dart-define-from-file=env.production.json
```

같은 맥락에서 Docker/CI 이미지의 Flutter SDK도 `3.41.6`으로 통일했다. **release와 patch가 같은 Flutter 버전 위에서 만들어진다**는 걸 파이프라인 전체에서 보장하는 게 핵심이다.

> 💡 정리하면 버전 정합성은 세 곳을 맞춰야 한다: ① `pubspec.yaml`의 version(단일 출처), ② Shorebird release-version(= versionName+versionCode, 오프셋 금지), ③ 빌드에 쓴 Flutter 버전(`--flutter-version`으로 고정). 셋 중 하나만 어긋나도 패치가 안 붙는다.

## 결론

OTA를 굴린다는 건 버전이 "스토어 버전 + 패치 번호"의 조합으로 늘어난다는 뜻이다. 우리는 **앱에 `버전(patch N)`을 노출**해 재현 가능성을 확보하고, **versionCode 오프셋을 걷어내 pubspec을 단일 출처로** 만들고, **`--flutter-version`으로 release/patch의 빌드 환경을 고정**해서 패치가 항상 올바른 release에 붙도록 맞췄다. 숨은 개발자 메뉴와 버전 복사는 그 위에 얹은 운영 편의였다.

## 관련 작업
- Shorebird version 정보 추가, 작성자 태그 — `VersionInfo` 위젯(patch 번호 표시) + 7탭 숨은 개발자 메뉴, version 정보 출처 변경
- 꾹 누르기(long press) → 버전 정보 복사 + "버전 정보가 복사되었습니다." 토스트
- versionCode 10만 단위 오프셋 제거, Shorebird flutter version 요구사항 반영(`--flutter-version=3.41.6` 고정)
- local.properties에서 version 정보 제거(pubspec 단일 출처화)
