---
title: "Shorebird로 OTA 코드푸시 배포하기"
date: 2026-06-01
categories: ["CI/CD"]
tags: ["Flutter", "Shorebird", "CodePush", "GitHub-Actions"]
---

> RN → Flutter 전환 시리즈의 배포 편. RN 시절 CodePush로 하던 "스토어 심사 없이 Dart 코드만 갈아끼우는" 배포를 Flutter에서는 Shorebird로 옮겼다. release/patch 분리, dev/production 분리, staging→stable 승격, 그리고 "패치 대기 중" 표시까지의 파이프라인 이야기다.

## 왜 Shorebird인가

Flutter는 기본적으로 컴파일된 네이티브 바이너리라, 코드를 고치면 스토어 재심사가 원칙이다. 근데 급한 버그 하나 고치자고 매번 심사를 기다릴 순 없다. RN에서 CodePush로 하던 그 감성 — **Dart 코드만 OTA로 밀어넣기** — 을 Flutter에서 해주는 게 Shorebird다.

개념은 두 단계로 나뉜다.

- **release**: 스토어에 올라가는 기준 빌드를 Shorebird에 등록한다. 이 버전이 "패치를 붙일 수 있는 베이스"가 된다.
- **patch**: 이미 나간 release 위에, 바뀐 Dart 코드만 얹는다. 사용자는 앱 재시작 시 조용히 받는다.

## release 워크플로부터

처음엔 `workflow_dispatch`로 수동 트리거하는 release/patch 워크플로 두 개를 깔았다. 플랫폼(android/ios/both)을 골라 돌린다.

```yaml
name: Shorebird Release
on:
  workflow_dispatch:
    inputs:
      platform:
        type: choice
        options: [android, ios, both]
        default: both
jobs:
  release-android:
    if: ${{ inputs.platform == 'android' || inputs.platform == 'both' }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: subosito/flutter-action@v2
        with: { flutter-version: '3.41.4', cache: true }
      - uses: shorebirdtech/setup-shorebird@v1
      - uses: actions/setup-java@v3
        with: { java-version: '17', distribution: 'temurin' }
      - name: Shorebird Release Android
        run: shorebird release android --no-confirm
        env:
          SHOREBIRD_TOKEN: ${{ secrets.SHOREBIRD_TOKEN }}
```

patch 쪽은 `release_version` 입력을 받아서, 비어 있으면 최신 release에 붙이고 지정하면 그 버전에 붙인다.

```yaml
- name: Shorebird Patch Android
  env:
    RELEASE_VERSION: ${{ inputs.release_version }}
  run: |
    ARGS="--platforms=android --flavor=development"
    if [ -n "$RELEASE_VERSION" ]; then
      ARGS="$ARGS --release-version $RELEASE_VERSION"
    fi
    echo "Running: shorebird patch $ARGS"
    shorebird patch $ARGS
```

> 💡 `SHOREBIRD_TOKEN`은 CI secret으로만 주입한다. 워크플로 어디에도 토큰 원문을 박지 않는다.

## dev / production 분리

돌려보니 금방 문제가 생겼다. **개발용 패치와 실사용자 패치가 같은 워크플로에서 섞였다.** 내부 QA용으로 급하게 밀어넣은 패치가 실사용자한테 갈 뻔한 아찔한 상황.

그래서 flavor 기준으로 워크플로를 쪼갰다.

- `shorebird-development-*` : `--flavor=development`, Firebase App Distribution으로 내부 배포
- `shorebird-release-production` : `--flavor=production`, 실사용자 대상

이러면서 몇 가지를 같이 정리했다.

- `flutter pub get` step을 명시적으로 넣었다. (setup-shorebird만으로는 의존성이 안 받아져 빌드가 깨졌다.)
- iOS credentials(프로비저닝/서명) step을 release 워크플로에 추가했다. (자세한 건 서명 편에서.)
- Android keystore 이름 오류를 잡았다. `store.keystore`로 복사하던 걸 `myapp.keystore`로. (역시 서명 편에서.)

## staging → stable 승격

dev/prod 분리 다음은 "안전장치"였다. 프로덕션 패치를 바로 실사용자에게 쏘지 않고, **staging 트랙에 먼저 올려 내부 QA → 검증 후 stable로 승격**하는 2단계로 만들었다.

Shorebird의 track 개념을 그대로 쓴다. 앱은 자기가 구독한 track(staging/stable)에서만 패치를 받는다.

```dart
// ShorebirdService — 앱이 구독 중인 track 결정
Future<UpdateTrack> getTrack() async {
  final sp = await SharedPreferences.getInstance();
  final isBeta = sp.getBool(_betaChannelKey) ?? false;
  return isBeta ? UpdateTrack.staging : UpdateTrack.stable;
}
```

승격 워크플로는 patch 번호와 release 버전을 입력받아 `promote`한다. 시작/완료 시 Slack으로 알림도 쐈다. (실사용자 배포 승격은 무서운 작업이라 "지금 누가 뭘 올렸는지"가 채널에 남아야 했다.)

```yaml
# promote (staging → stable) 개념 예시
- run: |
    echo "Promoting Android patch #${{ inputs.patch_number }} for ${{ inputs.release_version }}"
    shorebird patches promote \
      --release-version=${{ inputs.release_version }} \
      # ... track: staging -> stable
```

## 앱 시작 시 업데이트 체크

배포 파이프라인만 있으면 반쪽이다. 앱이 켜질 때 실제로 확인/다운로드를 해야 한다. 이 로직은 앱 시작을 막지 않도록 **실패해도 조용히 넘어가게** 짰다.

```dart
Future<void> checkAndDownloadUpdate() async {
  try {
    if (!_updater.isAvailable) return; // debug 빌드 등에선 false

    final track = await getTrack();
    final status = await _updater.checkForUpdate(track: track);

    switch (status) {
      case UpdateStatus.outdated:
        await _updater.update(track: track); // 다운로드, 재시작 시 적용
        break;
      case UpdateStatus.restartRequired:
      case UpdateStatus.upToDate:
      case UpdateStatus.unavailable:
        break;
    }
  } catch (e) {
    // 네트워크 오류 등은 무시. 앱 시작을 막지 않는다.
    debugPrint('[Shorebird] Update check failed: $e');
  }
}
```

## "재실행 시 업데이트 적용예정" 표시

여기서 UX 디테일 하나. Shorebird 패치는 **다운로드는 즉시, 적용은 다음 재시작**이다. 사용자 입장에선 "최신버전입니다"라고 떠 있는데 실은 뒤에서 이미 새 패치가 대기 중일 수 있다. 이게 헷갈린다.

그래서 다운로드는 됐지만 아직 적용 안 된 패치가 있으면(=`readNextPatch != readCurrentPatch`) 버전 정보 옆 문구를 바꿔줬다.

```dart
// 다운로드됐지만 아직 적용 안 된 patch 가 있는지
Future<bool> hasPendingPatch() async {
  final current = await _updater.readCurrentPatch();
  final next = await _updater.readNextPatch();
  return next?.number != current?.number;
}
```

```dart
// 설정 / 더보기 화면의 버전 행
Text(
  _hasPendingPatch ? '재실행 시 업데이트 적용예정' : '최신버전입니다.',
  style: TextStyles.paragraph11.copyWith(color: ColorStyles.primary.redMyapp),
);
```

이 작은 문구 하나로 "왜 업데이트했는데 그대로예요?" 문의가 줄었다.

## 결론

Shorebird는 "코드만 밀어넣기"라는 편의를 주지만, 그냥 갖다 쓰면 dev/prod가 섞이고 실사용자한테 검증 안 된 패치가 나갈 수 있다. 우리는 **flavor로 워크플로를 쪼개고, staging→stable 승격을 강제하고, 앱 시작 체크는 실패해도 안 죽게, 그리고 사용자에겐 대기 상태를 정직하게 보여주는** 데까지를 하나의 파이프라인으로 묶었다. 버전 관리 쪽 디테일은 다음 글에서 이어간다.

