---
title: "vision-camera 얼굴인식을 Flutter로 재구현 — ROI crop과 throttle"
date: 2026-08-21
categories: ["Flutter"]
tags: ["Flutter", "google-mlkit", "camera", "face-detection", "performance"]
---

예전에 React Native + `react-native-vision-camera`로 얼굴 인식 카메라를 만들면서 성능 최적화를 한 적이 있다. 전체 프레임에서 얼굴을 찾으니까 연산이 너무 무거워서, ROI(관심 영역)로 인식 범위를 잘라내고 프레임 처리 빈도를 500ms로 throttle했더니 15fps에서 20fps로 올라갔던 그 작업. ([App 카메라 최적화](/posts/App-Camera-최적화) 글 참고.)

이번엔 앱을 통째로 Flutter로 옮기게 됐다. 그러면서 "그때 RN에서 손으로 짰던 그 최적화, Flutter에선 어떻게 옮기지?" 하는 게 이 글의 주제다. 결론부터 말하면 아이디어는 그대로인데, **크롭을 실제로 픽셀 단위로 직접 해야 했다**는 게 제일 큰 차이였다. 그리고 그 크롭 기하 로직을 이번엔 단위테스트로 못 박아뒀다.

> 💡 RN 글과 겹치는 "왜 ROI인가 / 왜 throttle인가"는 여기서 다시 반복하지 않는다. 이 글은 **Flutter에선 뭐가 달랐고, 그걸 어떻게 테스트했나**에 집중한다.

## RN이랑 뭐가 다른가

RN 시절엔 `frameProcessorFps={5}` 같은 prop 하나 던지면 프레임 프로세서가 알아서 주기를 맞춰줬고, ROI 크롭도 네이티브 프레임 프로세서 플러그인 안에서 처리했다. 즉 "선언"만 하면 라이브러리가 알아서 해주는 영역이 꽤 있었다.

Flutter에서 `camera` + `google_mlkit_face_detection` 조합으로 가니까 상황이 좀 달랐다.

- `frameProcessorFps` 같은 편의 prop이 없다. `startImageStream` 콜백은 그냥 카메라가 뱉는 프레임을 **전부** 준다. 주기 제한은 내가 직접 시계 재서 걸러야 한다.
- ML Kit에 넘길 때 `InputImage.fromBytes`로 **바이트 버퍼를 직접** 만들어 줘야 한다. 그 말은 ROI 크롭도 남이 안 해주고, Android면 NV21, iOS면 BGRA8888 버퍼를 내가 손으로 잘라야 한다는 뜻이다.
- 카메라 센서 회전(rotation) 보정도 내 몫이다. ROI는 사용자가 보는 "똑바로 선(upright)" 화면 기준인데, 실제 버퍼는 센서 방향대로 눕거나 뒤집혀 있다. 그래서 upright 좌표의 ROI를 native 버퍼 좌표로 **되돌려서** 잘라야 정확한 영역이 나온다.

정리하면 RN에선 개념만 있으면 됐는데, Flutter에선 그 개념을 **픽셀 산수로 전부 구현**해야 했다. 그래서 오히려 로직이 명확해졌고, 테스트하기 좋아졌다.

## 구조

역할별로 파일을 나눴다.

- `lib/src/roi.dart` — ROI 정의(프리뷰 대비 0..1 분수)와 `isFaceInRoi` AABB 판정. RN의 `isFaceInROI` 이식.
- `lib/src/frame_crop.dart` — upright ROI → native crop 사각형 계산(`computeNativeCrop`), NV21/BGRA 크롭 함수.
- `lib/src/face_camera_view.dart` — 카메라 스트림 + throttle + 크롭 + ML Kit 호출.

## 1. ROI는 해상도 독립적으로

RN에선 `{ x: 100, y: 100, width: 200, height: 200 }`처럼 픽셀 절대값으로 ROI를 박았었다. Flutter로 옮기면서 여러 해상도(medium 프리셋이지만 기기마다 실제 버퍼 크기가 다르다)에 대응하려고 **분수(0..1)** 로 바꿨다.

```dart
class Roi {
  const Roi({
    this.left = 0.175,
    this.top = 0.25,
    this.width = 0.65,
    this.height = 0.45,
  });

  final double left;
  final double top;
  final double width;
  final double height;

  Rect toRect(Size canvasSize) => Rect.fromLTWH(
        left * canvasSize.width,
        top * canvasSize.height,
        width * canvasSize.width,
        height * canvasSize.height,
      );
}
```

기본값이 가로 0.65 × 세로 0.45니까, ROI가 프리뷰의 약 **29%** 정도를 덮는다. 나머지 71%는 ML Kit이 아예 안 보게 되는 셈. 이게 연산 절감의 핵심이다.

`isFaceInRoi`는 RN의 그 AABB(축 정렬 경계상자) 겹침 판정을 거의 그대로 옮겼다. 경계가 딱 닿는 경우(`<` 가 아니라 `<=` 의미)를 "안에 있음"으로 치는 것까지 동일하게.

```dart
bool isFaceInRoi(Rect face, Rect roi) {
  return !(face.right < roi.left ||
      face.left > roi.right ||
      face.bottom < roi.top ||
      face.top > roi.bottom);
}
```

이 함수, RN 글에서 인터페이스 정의까지 곁들여 설명했던 바로 그 로직이다. 짧지만 부등호 방향 하나 틀리면 얼굴이 있는데도 "없음"이 되는, 조용히 틀리기 딱 좋은 코드다. 그래서 여기부터 테스트를 깔았다.

## 2. throttle는 직접 시계로

`frameProcessorFps`가 없으니 콜백 안에서 직접 처리했다. 마지막 인식 시각을 들고 있다가 500ms 안 지났으면 그냥 `return`. 게다가 ML Kit 처리는 비동기라, 앞 프레임 처리가 안 끝났는데 다음 프레임이 밀려들면 큐가 터진다. 그래서 `_isBusy` 가드도 같이 걸었다.

```dart
static const Duration _detectionInterval = Duration(milliseconds: 500);

Future<void> _onFrame(CameraImage image) async {
  if (_isBusy) return; // 앞 프레임 처리 중이면 스킵
  final now = DateTime.now().millisecondsSinceEpoch;
  if (now - _lastDetectionMs < _detectionInterval.inMilliseconds) return;
  _lastDetectionMs = now;

  final prepared = _prepare(image); // 여기서 ROI 크롭
  if (prepared == null) return;

  _isBusy = true;
  try {
    final faces = await _faceDetector.processImage(prepared.input);
    if (!mounted) return;
    setState(() => _faces = faces);
  } catch (_) {
    // 일시적 디코드/인식 오류는 무시하고 다음 프레임에서 재시도
  } finally {
    _isBusy = false;
  }
}
```

RN에선 500ms 하나였는데, Flutter에선 **500ms throttle + busy 가드**를 둘 다 둬야 했다. 스트림이 라이브러리 도움 없이 날것으로 들어오기 때문이다.

## 3. ROI 크롭 — 여기가 제일 어려웠다

RN에선 `cropFrame(frame, roi)` 한 줄이었지만, 실제로는 네이티브 플러그인이 회전이랑 버퍼 포맷을 처리해줬던 거다. Flutter에서 직접 하려니 두 가지를 신경 써야 했다.

1. **회전 역변환**: ML Kit은 프레임을 시계방향으로 돌려서 upright로 본다. ROI는 upright 기준이니까, 그걸 native 버퍼 좌표로 되돌려야(inverse) 실제로 그 영역을 자를 수 있다.
2. **짝수 정렬**: NV21은 크로마가 2배 서브샘플링돼서, crop의 원점·크기가 짝수여야 색이 안 깨진다.

```dart
NativeCrop? computeNativeCrop(
  Roi roi,
  int imageWidth,
  int imageHeight,
  InputImageRotation rotation,
) {
  final swap = rotation == InputImageRotation.rotation90deg ||
      rotation == InputImageRotation.rotation270deg;
  final uw = (swap ? imageHeight : imageWidth).toDouble();
  final uh = (swap ? imageWidth : imageHeight).toDouble();

  // upright 좌표의 ROI 두 꼭짓점을 native 버퍼로 역변환
  final p1 = _uprightToNative(roi.left * uw, roi.top * uh, imageWidth, imageHeight, rotation);
  final p2 = _uprightToNative(
      (roi.left + roi.width) * uw, (roi.top + roi.height) * uh, imageWidth, imageHeight, rotation);

  var x = math.min(p1.dx, p2.dx).floor();
  var y = math.min(p1.dy, p2.dy).floor();
  var w = (math.max(p1.dx, p2.dx) - math.min(p1.dx, p2.dx)).round();
  var h = (math.max(p1.dy, p2.dy) - math.min(p1.dy, p2.dy)).round();

  // 원점 짝수 정렬 + 버퍼 안으로 클램프
  x -= x & 1;
  y -= y & 1;
  if (x < 0) x = 0;
  if (y < 0) y = 0;
  if (x >= imageWidth || y >= imageHeight) return null;
  if (x + w > imageWidth) w = imageWidth - x;
  if (y + h > imageHeight) h = imageHeight - y;
  w -= w & 1; // 크기도 짝수로
  h -= h & 1;
  if (w <= 0 || h <= 0) return null; // 퇴화하면 null → 호출부는 전체 프레임 폴백

  return NativeCrop(x, y, w, h);
}
```

회전 역변환은 이렇게 케이스로 나눴다.

```dart
Offset _uprightToNative(double x, double y, int w, int h, InputImageRotation rotation) {
  switch (rotation) {
    case InputImageRotation.rotation0deg:   return Offset(x, y);
    case InputImageRotation.rotation90deg:  return Offset(y, h - x);
    case InputImageRotation.rotation180deg: return Offset(w - x, h - y);
    case InputImageRotation.rotation270deg: return Offset(w - y, x);
  }
}
```

그리고 실제 크롭. NV21은 Y 평면 뒤에 VU가 인터리브로 붙어있어서, 루마는 통째로 행 복사하고 크로마는 절반 높이만 복사한다.

```dart
CroppedFrame cropNv21(Uint8List src, int width, int height, NativeCrop crop) {
  final cw = crop.width, ch = crop.height;
  final out = Uint8List(cw * ch + cw * ch ~/ 2);

  var o = 0;
  for (var row = 0; row < ch; row++) { // 루마
    final srcStart = (crop.y + row) * width + crop.x;
    out.setRange(o, o + cw, src, srcStart);
    o += cw;
  }
  final vuBase = width * height;
  for (var row = 0; row < ch ~/ 2; row++) { // 크로마(절반 높이)
    final srcStart = vuBase + (crop.y ~/ 2 + row) * width + crop.x;
    out.setRange(o, o + cw, src, srcStart);
    o += cw;
  }
  return CroppedFrame(bytes: out, bytesPerRow: cw, width: cw, height: ch);
}
```

크롭에 실패(퇴화 ROI 등)하면 `null`을 돌려주고, 호출부는 전체 프레임으로 폴백한다. "최적화가 안 되더라도 인식은 되게" 안전망을 둔 것.

## 이걸 왜 테스트로 못 박았나

RN 때는 솔직히 이 크롭/판정 로직을 눈으로 보고 "되네" 하고 넘어갔다. 근데 Flutter로 옮기면서 회전 역변환, 짝수 정렬, 버퍼 오프셋 계산 같은 걸 **직접** 짜다 보니, 부등호나 인덱스 하나 틀린 걸 카메라 켜서 눈으로 잡는 건 미친 짓이라는 걸 깨달았다. 프레임은 초당 수십 장 흘러가는데.

그래서 카메라·플랫폼 의존 없이 돌아가는 **순수 로직만 떼어내서** 단위테스트를 붙였다. `roi.dart`에 8개, `frame_crop.dart`에 9개, 총 17개.

ROI 판정은 "안/걸침/닿음/완전 바깥" 경계 케이스를 다 넣었다.

```dart
const roi = Rect.fromLTWH(100, 100, 200, 200); // 100..300

test('face partially overlapping the ROI is detected', () {
  expect(isFaceInRoi(const Rect.fromLTWH(280, 280, 60, 60), roi), isTrue);
});

test('touching edges counts as inside (non-strict inequality)', () {
  // 얼굴 오른쪽 끝 == ROI 왼쪽 끝 → 닿으면 안에 있는 걸로 침
  expect(isFaceInRoi(const Rect.fromLTWH(50, 150, 50, 50), roi), isTrue);
});

test('face fully to the left is rejected', () {
  expect(isFaceInRoi(const Rect.fromLTWH(0, 150, 40, 40), roi), isFalse);
});
```

크롭 기하는 회전별 매핑, 짝수 정렬, 퇴화 ROI 폴백을 검증했다. 특히 rotation90에서 upright의 왼쪽 절반이 native 버퍼의 아래쪽 띠로 돌아가는지 같은 걸 값으로 박아뒀다.

```dart
test('rotation90: partial upright ROI rotates into a native strip', () {
  const roi = Roi(left: 0, top: 0, width: 0.5, height: 1);
  final crop = computeNativeCrop(roi, 480, 640, InputImageRotation.rotation90deg);
  // upright 왼쪽절반/전체높이 → native 아래쪽 띠
  expect(crop, const NativeCrop(0, 320, 480, 320));
});

test('origin and extents are even-aligned for NV21', () {
  // 정렬 전에 홀수 픽셀이 나오도록 일부러 481x641
  const roi = Roi(left: 0.1, top: 0.1, width: 0.3, height: 0.3);
  final crop = computeNativeCrop(roi, 481, 641, InputImageRotation.rotation0deg)!;
  expect(crop.x.isEven, isTrue);
  expect(crop.width.isEven, isTrue);
});
```

버퍼를 실제로 자르는 것도, 작은 손계산 가능한 버퍼로 바이트 단위 검증을 했다. 4×4 NV21이면 결과가 정확히 어떤 바이트여야 하는지 직접 적어놓는 식.

```dart
test('crops Y and interleaved VU planes correctly', () {
  // 4x4 NV21: Y = 0..15, VU = 16..23
  final src = Uint8List.fromList(List<int>.generate(24, (i) => i));
  final out = cropNv21(src, 4, 4, const NativeCrop(2, 2, 2, 2));
  // Y 행 2,3 열 2,3 => 10,11,14,15 ; VU 행 1 열 2,3 => 22,23
  expect(out.bytes, Uint8List.fromList([10, 11, 14, 15, 22, 23]));
});
```

플랫폼 채널 없이 이만큼 검증되니까, 카메라 실기 테스트는 "화면에 오버레이가 잘 그려지나" 정도만 눈으로 보면 됐다. 로직의 정확성은 테스트가 지킨다.

## 마무리

RN 시절에 얻었던 15→20fps 개선(이건 RN 글에서 나온 수치다)을, Flutter에선 같은 세 가지 최적화(ROI 크롭 / 500ms throttle / ROI 내 판정)로 재현하는 게 목표였다. 다만 Flutter 쪽에선 fps를 따로 측정하지 않았다. 그리고 "20fps"와 이 글의 500ms throttle은 다른 축의 숫자다 — 프리뷰 렌더 fps와 달리, 500ms throttle은 초당 약 2회 인식 주기를 뜻한다. 옮기면서 배운 건:

- 선언형 prop이 없으니 throttle·busy 가드·회전 보정·버퍼 크롭을 **전부 직접** 짜야 했지만, 그 덕에 로직이 명확해져서 순수 함수로 떼어내기 쉬웠다.
- ROI를 픽셀 절대값 대신 **분수(0..1)** 로 두니 해상도 독립적이 됐고, 기본 ROI가 프리뷰의 약 29%만 덮어서 ML Kit 입력 픽셀을 크게 줄였다.
- 카메라 로직에서 **순수 판정/기하 로직을 분리**해두면, 프레임을 눈으로 쫓지 않고도 부등호·오프셋 버그를 테스트로 잡을 수 있다. 이게 RN 때와 가장 달라진 작업 방식이었다.

> UI 스트림 로직과 순수 계산을 분리하는 것. 결국 이게 Flutter 재구현에서 얻은 진짜 소득이었다.

## 관련 작업

- `feat: RN에서 Flutter로 마이그레이션 및 얼굴 인식 카메라 구현` (branch `seod0209/flutter-face-camera`)
  - RN(vision-camera) 스캐폴딩 제거 후 Flutter 프로젝트로 재구성, `camera` + `google_mlkit_face_detection` 기반 전면 카메라 얼굴 인식 구현.
  - RN 최적화 3종(ROI 크롭 / 500ms throttle / `isFaceInRoi` ROI 내 판정) 이식.
  - 순수 로직 단위테스트 17개: `test/roi_test.dart`(ROI 판정 8) + `test/frame_crop_test.dart`(크롭 기하·NV21/BGRA 버퍼 9).
- 이 글의 전편(RN vision-camera 최적화, 15→20fps): [App 카메라 최적화](/posts/App-Camera-최적화)
