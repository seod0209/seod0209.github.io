---
title: "Figma에서 코드까지: 디자인–데이터 브릿지 (데이터브릿지 플러그인)"
date: 2026-06-08
categories: ["Design System"]
tags: ["Figma", "Plugin", "Design System", "자동화"]
---

> 디자인 시스템 시리즈 2편. 1편이 "토큰이라는 값의 파편화"였다면, 이번 편은 "디자인 안에 들어가는 **데이터**의 파편화" 이야기다.

## 카드 하나 만드는데 왜 이렇게 손이 많이 가지

차량 카드 목업을 만들 때마다 반복되는 장면이 있다.

디자이너가 브랜드 텍스트에 "제네시스"를 치고, 모델에 "G80", 가격에 "월 89만원", 이미지엔 어디선가 긁어온 썸네일을 넣는다. 리스 카드는 보증금·월납입금이 따로 있고, 일시불 카드는 그냥 차량가만 있고... 뱃지는 "최저가"짜리랑 "즉시출고"짜리를 상황 따라 켰다 껐다 한다.

문제는 이게 **매번 손으로** 이뤄진다는 거다. 목업 하나에 채워야 할 텍스트가 열 개가 넘는데, 그걸 카드 20개짜리 리스트 화면에 다 깔면?

- 가격 단위 틀리고 (89만원 vs 890,000원)
- 브랜드-모델 조합이 실제로 존재하지 않는 유령 차량이 생기고
- "월 납입금"이라 써놓고 실은 일시불 가격을 넣고
- 오타. 그놈의 오타. "제내시스", "G80 가솔린 2.5T" 대신 "G80 가솔인"

디자인 QA에서 잡히면 그나마 다행인데, 개발까지 넘어가서 "이거 실제 데이터랑 다른데요?" 소리를 듣는 순간 현타가 온다. 디자인과 실데이터가 **완전히 따로 노는** 거다. 목업은 예쁘지만 거짓말을 하고 있고, 그 거짓말을 사람이 매번 손으로 쓴다.

그래서 만든 게 사내 Figma 플러그인, **데이터브릿지(Data Bridge)** 다. 한 줄로 요약하면 이렇다.

> **gradeId 하나만 넣으면 브랜드/모델/가격/이미지까지 카드에 한 번에 꽂힌다.**

## 왜 하필 "플러그인"이었나

디자인–데이터를 잇는 방법이 플러그인만 있는 건 아니다. 후보를 몇 개 놓고 봤다.

1. **누군가 데이터를 CSV/JSON으로 뽑아주고, 디자이너가 복붙** → 결국 사람이 채우는 건 똑같음. 오타만 CSV 단계로 이동.
2. **Figma REST API로 외부에서 프레임에 값 주입** → 파일 토큰·권한 관리가 무겁고, "지금 내가 고르고 있는 이 카드"라는 인터랙션이 안 됨. 배치 성격이라 디자인 작업 흐름과 안 맞음.
3. **Figma 플러그인 (데스크톱 로컬 import)** → 디자이너가 **지금 선택한 레이어**에, **자기 리듬대로**, 원하는 차량을 즉시 꽂을 수 있음.

3번을 골랐다. 이유는 명확하다. 디자인은 배치 작업이 아니라 **인터랙티브한 작업**이기 때문이다. "이 카드엔 제네시스, 저 카드엔 아반떼"를 눌러가며 고르는 흐름을, 플러그인만이 자연스럽게 지원한다. 선택(selection) 컨텍스트를 그대로 쓸 수 있는 게 핵심이었다.

배포도 무겁게 안 갔다. 커뮤니티에 퍼블리시하지 않고 **로컬 import**로 돌린다. Figma 데스크톱 → `Plugins` → `Development` → `Import plugin from manifest…` 로 `manifest.json`을 물려주면 끝. 사내에서만 쓰는 도구라 리뷰·심사 없이 바로 붙이고, 로직 고치면 다시 로드만 하면 된다.

## 느슨한 결합: 왜 "레이어명 컨벤션"인가

여기가 이 플러그인 설계의 진짜 결정이었다.

카드의 어느 텍스트에 "가격"을 넣고 어느 텍스트에 "브랜드"를 넣을지, 플러그인이 어떻게 알까? 방법은 크게 둘이다.

- **강한 결합**: Figma의 컴포넌트 프로퍼티/바인딩을 정의해서 스키마로 묶는다. 정확하지만, 모든 카드가 그 컴포넌트를 정확히 써야 하고, 디자이너가 새 레이아웃을 시도할 때마다 스키마를 건드려야 한다. **디자인 자율성이 죽는다.**
- **느슨한 결합**: 그냥 **레이어 이름**을 규칙으로 삼는다. 레이어명에 `car-price`가 들어있으면 거기에 가격을 채운다. 끝.

우린 느슨한 쪽을 택했다. 디자이너는 평소처럼 자유롭게 레이아웃을 짜되, 값을 자동으로 받고 싶은 레이어에만 **약속된 이름**을 붙이면 된다. 컴포넌트를 안 써도 되고, 프레임을 통째로 새로 그려도 되고, 그냥 텍스트 하나만 골라서 적용해도 된다.

트레이드오프는 안다. 레이어명 오타 나면 매핑이 조용히 실패한다. 그래서 매칭을 **부분 매칭 + 대소문자 무시**로 관대하게 잡았다. `Car Price`, `car-price`, `car_price_main` 다 정규화하면 `car-price`를 포함하는 문자열이 돼서 인식된다. "정확한 스키마" 대신 "관대한 규칙"으로, 자동화와 디자인 자율성을 동시에 챙기는 절충이다.

> 💡 자동화 도구를 만들 때 제일 흔한 실수가 "쓰는 사람한테 완벽한 규율을 요구"하는 거다. 규율을 강제하는 순간 아무도 안 쓴다. 도구가 사람 쪽으로 관대하게 굽혀야 채택된다.

## 플러그인 구조

Figma 플러그인은 딱 세 조각이다.

```
data-bridge/
├─ manifest.json   # 플러그인 메타 + 진입점 선언
├─ code.js         # 샌드박스에서 도는 메인 로직 (Figma 문서 조작)
└─ ui.html         # iframe으로 뜨는 UI (gradeId 입력, 구매타입 선택 등)
```

`manifest.json` 은 이렇게 생겼다.

```json
{
  "name": "회사 데이터브릿지",
  "id": "myapp-data-bridge",
  "api": "1.0.0",
  "main": "code.js",
  "ui": "ui.html",
  "editorType": ["figma"],
  "networkAccess": {
    "allowedDomains": ["https://api.example.internal"]
  }
}
```

핵심은 두 세계가 분리돼 있다는 점이다.

- `ui.html` (iframe) — 사람이 보는 화면. gradeId 입력창, 구매타입(리스/렌트/일시불) 라디오, 뱃지 체크박스, "선택 레이어에 적용" 버튼. 네트워크는 여기서 친다.
- `code.js` (샌드박스) — Figma 문서(노드 트리)를 만질 수 있는 유일한 곳. UI는 문서를 직접 못 만지고, 문서 로직은 화면을 직접 못 그린다.

둘은 `postMessage`로만 대화한다.

```js
// code.js — 플러그인 부팅
figma.showUI(__html__, { width: 320, height: 480 });

figma.ui.onmessage = async (msg) => {
  if (msg.type === "apply") {
    // 1) UI가 넘긴 gradeId로 차량 정보 조회
    const vehicle = await fetchVehicle(msg.gradeId, msg.paymentType);
    // 2) 지금 캔버스에서 선택된 레이어들에 값 주입
    const targets = figma.currentPage.selection;
    for (const node of targets) {
      applyToNode(node, vehicle, msg);
    }
    // 3) "최근 사용" 차량을 클라이언트 스토리지에 저장 → 상단 칩
    await saveRecent(vehicle);
    figma.notify(`${vehicle.brand} ${vehicle.model} 적용 완료`);
  }
};
```

## 레이어명 → 값 매핑 로직

여기가 데이터브릿지의 심장이다. 선택한 프레임을 재귀로 훑으면서, 각 레이어의 **이름**을 보고 무슨 값을 넣을지 결정한다.

```js
// 레이어명 정규화: 소문자 + 공백/언더스코어를 하이픈으로
const norm = (name) => name.toLowerCase().replace(/[\s_]+/g, "-");

// 텍스트 레이어명 → 차량 데이터 필드
const TEXT_FIELD_MAP = {
  "brand":          (v) => v.brand,                    // "제네시스"
  "model":          (v) => v.model,                    // "G80"
  "grade":          (v) => v.gradeName,                // "2.5T AWD"
  "year":           (v) => `${v.year}년형`,
  "car-name":       (v) => `${v.brand} ${v.model}`,    // 합성 필드
  "car-price":      (v) => won(v.price),               // 일시불 차량가
  "monthly-price":  (v) => won(v.monthly),             // 월 납입금
  "deposit-price":  (v) => won(v.deposit),             // 보증금/선납금
  "discount-price": (v) => won(v.discount),
  "discount-rate":  (v) => `${v.discountRate}%`,
  "payment-type":   (v, m) => PAYMENT_LABEL[m.paymentType], // 리스/렌트/일시불
  // "price"는 구매타입에 따라 자동 분기 (아래 참고)
};

// 원(₩) 포매팅 — "89만원" 같은 단위 실수를 원천 차단
const won = (n) => n == null ? "" : `${n.toLocaleString("ko-KR")}원`;

function applyToNode(node, vehicle, msg) {
  const key = norm(node.name);

  // 1) 텍스트 레이어: 이름에 필드 키워드가 "포함"되면 채움 (부분 매칭)
  if (node.type === "TEXT") {
    for (const field in TEXT_FIELD_MAP) {
      if (key.includes(field)) {
        setText(node, TEXT_FIELD_MAP[field](vehicle, msg));
        return;
      }
    }
    // 2) 그냥 "price"만 있으면 구매타입 따라 자동 분기
    if (key.includes("price")) {
      const val = msg.paymentType === "lump"
        ? won(vehicle.price)      // 일시불 → 차량가
        : won(vehicle.monthly);   // 리스/렌트 → 월 납입금
      setText(node, val);
      return;
    }
  }

  // 3) 이미지: Rectangle에 이름 매칭되면 이미지 fill 교체
  if (node.type === "RECTANGLE" &&
      (key.includes("car-image") || key.includes("thumbnail"))) {
    setImageFill(node, vehicle.imageUrl);
    return;
  }

  // 4) 뱃지 프레임: visibility 자동 제어
  if (key.includes("badge-lowest"))  node.visible = !!msg.badgeLowest;
  if (key.includes("badge-instant")) node.visible = !!msg.badgeInstant;

  // 5) 자식이 있으면 재귀
  if ("children" in node) {
    for (const child of node.children) applyToNode(child, vehicle, msg);
  }
}
```

텍스트를 채울 땐 폰트를 먼저 로드해야 한다. Figma는 폰트를 안 불러오면 `characters`를 못 바꾼다. 이게 초보자가 제일 많이 밟는 지뢰다.

```js
async function setText(node, value) {
  if (value == null || value === "") return;
  await figma.loadFontAsync(node.fontName); // 필수! 안 하면 에러
  node.characters = String(value);
}
```

이미지는 URL만 있으면 된다. 현재 Figma Plugin API는 메인 스레드(`code.js`)에서 Fetch API를 공식 지원하고, URL로부터 바로 이미지를 만드는 `figma.createImageAsync(url)`도 제공한다. 그래서 UI에서 바이트를 받아 넘기던 우회 없이, `manifest.json`의 `networkAccess.allowedDomains`에 도메인만 등록하면 샌드박스에서 URL을 그대로 쓸 수 있다.

```js
async function setImageFill(node, imageUrl) {
  // URL에서 바로 이미지 생성 (메인 스레드 Fetch 지원)
  const image = await figma.createImageAsync(imageUrl);
  node.fills = [{ type: "IMAGE", scaleMode: "FILL", imageHash: image.hash }];
}
```

## 구매타입 분기 — 리스/렌트/일시불

차량은 "얼마"가 하나가 아니다. **어떻게 사느냐**에 따라 보여줄 숫자가 달라진다.

- **일시불**: 차량가 하나. `price` 레이어 = 차량가.
- **리스 / 렌트**: 월 납입금이 주인공. `price` 레이어 = 월 납입금, `deposit-price` = 선납금. 월 납입금·선납금 모두 API가 내려주는 확정 값을 쓰고, 프론트에서 되짚어 계산하지 않는다.

그래서 UI에서 구매타입을 고르면, 같은 `price` 레이어라도 다른 값이 들어간다. 위 `applyToNode`의 2번 분기가 그 역할이다. 디자이너는 카드 레이아웃을 바꿀 필요 없이 라디오 버튼만 바꾸면, 리스 카드 ↔ 일시불 카드가 즉시 전환된다.

```js
const PAYMENT_LABEL = { lease: "리스", rent: "렌트", lump: "일시불" };

// 월 납입금(monthly)은 이자·잔존가치·프로모션이 얽혀 있어
// 프론트에서 (차량가 − 선납) ÷ 개월수로 되짚으면 틀린 숫자가 나온다.
// 그래서 직접 계산하지 않고, API가 내려주는 확정 값(vehicle.monthly)을 그대로 쓴다.
// (위 applyToNode의 price 분기가 won(vehicle.monthly)로 이미 그 값을 꽂는다.)
```

## 권장 레이어 구조

디자이너가 이 규칙에 맞춰 카드를 짜면, gradeId 한 번에 전부 자동으로 채워진다. 권장 트리는 이렇다.

```
🔲 car-card (Frame)              ← 이 프레임을 선택하고 "적용"
├─ 🖼  car-image                 ← Rectangle, 차량 썸네일 자동 교체
├─ 📝 brand                      ← "제네시스"
├─ 📝 car-name                   ← "제네시스 G80" (합성)
├─ 📝 grade                      ← "2.5T AWD"
├─ 📝 year                       ← "2026년형"
├─ 🔲 price-box (Frame)
│  ├─ 📝 payment-type            ← "리스" / "렌트" / "일시불"
│  ├─ 📝 price                   ← 구매타입 따라 자동 분기
│  ├─ 📝 deposit-price           ← 리스/렌트일 때 선납금
│  └─ 📝 discount-rate           ← "12%"
└─ 🔲 badges (Frame)
   ├─ 🏷  badge-lowest           ← "최저가", 체크 시에만 visible
   └─ 🏷  badge-instant          ← "즉시출고", 체크 시에만 visible
```

규칙은 딱 세 개만 기억하면 된다.

1. **값 받을 레이어에 약속된 이름을 붙인다** (부분 매칭이라 접두/접미사 자유).
2. **텍스트는 TEXT, 이미지는 RECTANGLE** 타입으로 둔다.
3. **뱃지는 프레임**으로 감싸서 visibility로 켜고 끈다.

이름만 지키면 레이아웃은 마음대로 바꿔도 된다. 이게 "느슨한 결합"의 실제 효용이다.

## 써보니

손으로 채우던 시절과 비교하면 체감이 확실하다.

- **오타 소멸**: 브랜드·모델·가격이 실데이터에서 오니 유령 차량이 안 생긴다. 가격 단위(`toLocaleString` + "원")도 코드가 고정하니 "89만원 vs 890,000원" 실수가 사라졌다.
- **일관성**: 리스트 20장을 gradeId만 바꿔가며 순식간에 채운다. "최근 사용" 차량이 상단 칩으로 남아 재작업도 빠르다.
- **디자인–데이터 정합**: 목업이 더 이상 거짓말을 안 한다. 개발로 넘어갈 때 "이거 실제랑 달라요" 핑퐁이 없어졌다.

무엇보다, 이건 디자인 시스템을 "값의 자동화"로 확장한 첫 시도였다. **토큰이 색·간격·타이포를 자동화했다면, 데이터브릿지는 디자인 안의 콘텐츠를 자동화한다.** 디자인과 실데이터 사이의 다리를, 사람의 손이 아니라 컨벤션이 놓게 한 것.

다음 편에선 이 "값"들이 코드 쪽에서 어떻게 토큰 파이프라인으로 내려가는지를 다룰 예정이다.

## 관련 작업

> 본문 코드는 내부 가이드에 서술된 동작(레이어명 매핑·구매타입 분기·뱃지 제어)을 블로그용으로 재구성한 설계 예시다. 사내 도메인/식별정보는 일반화했다.

## 출처
- [Figma — Making Network Requests](https://www.figma.com/plugin-docs/making-network-requests/)
