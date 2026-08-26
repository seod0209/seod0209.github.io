---
title: "Flutter 라우팅 설계기: 바텀시트 컨트롤러를 걷어낸 이야기"
date: 2026-03-26
categories: ["Flutter"]
tags: ["Flutter", "GetX", "Navigator", "라우팅"]
---

> RN에서 Flutter로 넘어오는 시리즈 중 라우팅 편. 초반에 만들어 쓰던 "글로벌 바텀시트 컨트롤러"를 결국 걷어내고 `Navigator` push/pop + `showModalBottomSheet`로 돌아온 과정을 적는다.

## 처음엔 커스텀 컨트롤러였다

Flutter로 앱을 새로 짜면서 바텀시트를 이렇게 관리했다. 앱 최상단에 `AppBottomSheet` 위젯을 하나 깔고, 전역 `AppBottomSheetController`가 `show()` / `hide()`로 그 시트를 제어하는 구조.

```dart
// main_app.dart — 최상단에 바텀시트 레이어를 항상 깔아둔다
GetMaterialApp(
  getPages: AppPages.pages,
  initialRoute: Routes.SPLASH.name,
  builder: (context, child) => Stack(
    children: [child ?? const SizedBox.shrink(), const AppBottomSheet()],
  ),
);
```

```dart
// 컨트롤러를 permanent 로 심어두고 어디서든 호출
Get.put(AppBottomSheetController(), permanent: true);

// 사용하는 쪽
Get.find<AppBottomSheetController>().show(
  (_) => CarComparisonBottomSheet(
    onSelected: (idCargrade, brand, model, modelYear, grade) {
      // 값 세팅...
      Get.find<AppBottomSheetController>().hide();
      Future.delayed(const Duration(milliseconds: 400), () {
        showSecondCarComparisonBottomSheet(); // 다음 시트 체인
      });
    },
  ),
);
```

처음엔 그럴듯해 보였다. 시트를 "상태"로 다루니까 어디서든 열고 닫을 수 있었다.

## 근데 자꾸 어긋났다

문제는 이 구조가 **Flutter의 라우트 스택 바깥에서 논다**는 거였다.

- 시트를 열고 닫을 때 `hide()` 후 `Future.delayed(400ms)`로 다음 시트를 여는, **타이밍에 기대는 코드**가 늘어났다. 딜레이가 짧으면 트랜지션이 겹치고, 길면 사용자가 멍하니 기다린다.
- 결과값을 콜백(`onSelected`)으로 위로 던지니까 콜백 안에 로직이 자꾸 쌓였다. 차량 1차 선택 → 2차 선택 → 결과 페이지 이동이 콜백 중첩으로 표현됐다.
- 뒤로가기(하드웨어 백)와 이 전역 시트의 관계가 애매했다. 라우트 스택에 없으니 OS 백 버튼이 시트를 안 닫았다.

한마디로, **Flutter가 이미 잘 하는 걸 우리가 다시 만들고 있었다.**

## 그래서 걷어냈다

방향은 단순하다. 시트도 그냥 라우트다. `showModalBottomSheet`는 자기 자신이 `Future<T?>`를 반환한다. 이걸 `await`하면 콜백 체인이 통째로 사라진다.

먼저 얇은 래퍼 하나만 뒀다. (모서리 라운드, SafeArea, 최대 높이 같은 공통 껍데기만 담당)

```dart
class AppModal {
  static Future<T?> showSheet<T>({
    required WidgetBuilder builder,
    bool isDismissible = true,
  }) {
    return showModalBottomSheet<T>(
      context: Get.context!,
      isScrollControlled: true,
      isDismissible: isDismissible,
      backgroundColor: Colors.transparent,
      builder: (context) => _AppBottomSheetShell(child: builder(context)),
    );
  }
}
```

그리고 값은 콜백이 아니라 `Navigator.pop(result)`로 돌려받는다. 결과 타입은 그냥 평범한 모델로 정의했다.

```dart
class CarComparisonResult {
  final int? idCargrade;
  final CarBrandItem? brand;
  final CarModelItem? model;
  final CarModelYear? modelYear;
  final CarGrade? grade;
  const CarComparisonResult({
    this.idCargrade, this.brand, this.model, this.modelYear, this.grade,
  });
}
```

이제 차량 비교 플로우가 이렇게 **위에서 아래로 읽히는 코드**가 된다.

```dart
void showFirstCarComparisonBottomSheet() async {
  final result = await AppModal.showSheet<CarComparisonResult>(
    builder: (_) => CarComparisonBottomSheet(buttonText: '첫번째 차량 선택 완료'),
  );
  if (result == null) return; // 사용자가 그냥 닫음

  firstCompareId.value = result.idCargrade;
  firstCompareBrand.value = result.brand;
  firstCompareModel.value = result.model;
  firstCompareGrade.value = result.grade;

  showSecondCarComparisonBottomSheet(); // 딜레이 없이 자연스럽게 다음
}

void showSecondCarComparisonBottomSheet() async {
  final result = await AppModal.showSheet<CarComparisonResult>(
    builder: (_) => CarComparisonBottomSheet(
      buttonText: '두번째 차량 선택 완료',
      disabledGradeId: firstCompareId.value,
    ),
  );
  if (result == null) return;

  secondCompareId.value = result.idCargrade;
  // ...
  WidgetsBinding.instance.addPostFrameCallback((_) {
    Navigation.push(Routes.CAR_MATCH.name, arguments: { /* 비교 결과 */ });
  });
}
```

바텀시트 안에서는 값 세팅 대신 그냥 `pop`으로 돌려준다.

```dart
// 시트 내부의 완료 버튼
onPressed: () => Navigator.of(context).pop(
  CarComparisonResult(idCargrade: id, brand: brand, model: model, grade: grade),
);
```

## 정리하면서 지운 것들

이 작업의 상당 부분은 **삭제**였다.

- 최상단 `Stack`에서 `AppBottomSheet` 레이어 제거 → `builder`가 그냥 `child`를 반환.
- `main.dart`에서 `Get.put(AppBottomSheetController(), permanent: true)` 제거.
- 안 쓰게 된 `app_bottom_sheet.dart`, `app_bottom_sheet_controller.dart` 삭제.
- 각 컨트롤러에서 `AppBottomSheetController` import 제거. (한 번에 다 못 지워서 "미제거 import 삭제" 커밋이 따로 나갔다. 흔한 일이다.)

```dart
// before
builder: (context, child) => Stack(
  children: [child ?? const SizedBox.shrink(), const AppBottomSheet()],
),
// after
builder: (context, child) => child ?? const SizedBox.shrink(),
```

## 곁다리로 잡힌 생명주기 버그

같은 티켓에서 라우팅을 정리하다 보니 GetX 생명주기 문제도 같이 튀어나왔다. 토픽을 바꿀 때마다 `TextEditingController disposed` 에러가 났는데, 폼 컨트롤러 계층을 토픽별 서브컨트롤러로 쪼개서 바인딩 시점을 명확히 하니 정리됐다. 라우팅을 스택 기준으로 되돌리니까 **"언제 만들어지고 언제 죽는지"가 라우트 수명과 일치**하면서 이런 race가 줄었다.

## 결론

교훈은 하나다. **프레임워크가 이미 제공하는 스택/생명주기를 이기려 들지 말자.** `showModalBottomSheet`의 `Future<T?>` 반환 하나만 제대로 써도 콜백 지옥과 `Future.delayed` 땜빵이 통째로 사라진다. 전역 상태로 UI를 흉내 내는 대신, 시트도 화면도 전부 라우트 스택 위에 올려두는 쪽이 결국 디버깅도 쉬웠다.

## 관련 작업
- bottom sheet controller 제거 및 `Navigator.push`/`pop`으로 동작 수정
- bottom sheet controller 미제거 import 삭제
- 커뮤니티 글쓰기 폼 컨트롤러 리팩토링 — 토픽 변경 시 `TextEditingController disposed` / GetX 생명주기 충돌 해결
- 토픽 선택 / 차량선택 바텀시트를 공통 위젯·공통 로직으로 통일
