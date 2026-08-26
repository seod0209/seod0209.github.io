---
title: "배포 후가 더 문제였다: Playwright·유닛 테스트로 엣지 케이스와 QA를 줄이기"
date: 2026-08-21
categories: ["Testing"]
tags: ["Playwright", "Jest", "E2E", "QA", "Next.js"]
---


기획 초안을 받아서 화면을 만든다. 만들면 QA를 돈다. 여기까진 정상인데, 진짜 문제는 항상 **배포하고 난 뒤**에 왔다.

기획서에 안 적혀 있던 상태값, 아무도 상상 못 한 입력, "그 경우엔 뭐가 떠야 하지?" 싶은 분기. 이런 게 개발할 땐 안 보이다가 실제 유저 데이터가 들어오는 순간 배너가 이상하게 뜨거나, 없어야 할 팝업이 뜨거나, 있어야 할 안내가 안 뜨는 식으로 터진다. 그때마다 부랴부랴 핫픽스 치고, QA가 또 전체 리그레션을 돌고... 사람이 눈으로 다 확인하니까 시간은 시간대로 잡아먹고, 그러고도 다음 배포에서 같은 자리가 또 깨진다.

## 요즘 특히 무서운 것

요즘은 AI로 코드 찍어내는 속도가 진짜 빨라졌다. 근데 딱 여기서 불안해진다. **생산 속도는 빨라지는데, 이게 좋은 제품인지 정상 제품인지 검증할 시간과 시각은 그만큼 안 늘어난다.** 오히려 줄었다. 코드가 많아질수록 "이거 원래 어떻게 동작해야 맞지?"를 판단할 사람의 눈은 부족해지고, 리뷰는 대충 통과되고, 문제는 배포 뒤로 밀린다.

> 만드는 속도가 빨라질수록, 만든 게 맞는지 확인하는 비용은 오히려 커진다. 그 간극을 사람 QA로만 메우려니 답이 없었다.

그래서 이 간극을 최소화하려고 테스트 자동화를 도입했다. 핵심은 두 축이다.

- **Playwright E2E** — 핵심 유저 플로우를 사람 대신 클릭하게 만들어서 회귀 가드로 쓴다. "배포 후에 터지던" 그 자리들.
- **유닛 테스트** — 계산·분기 로직처럼 기획 누락과 엣지 케이스가 숨는 곳을 코드로 못 박는다.

사실 이건 갑자기 나온 얘기가 아니다. 예전에 기술부채를 정리하면서 "테스트가 전사적으로 실질 제로다, 도구만 깔려 있고 아무도 안 쓴다"고 지적했던 적이 있다. 실제로 CI 스크립트가 `jest --ci --passWithNoTests`, 그러니까 **테스트 파일이 없어도 그냥 통과**하도록 되어 있었다. 도구는 있는데 테스트가 없으니 게이트가 게이트 역할을 안 한 거다. 이번엔 그 도구를 실제로 쓰는 걸 목표로 잡았다.

## 유닛: 기획 누락이 숨는 계산·분기 로직부터

가장 효과가 컸던 건 "띠배너 우선순위" 같은 순수 로직이었다. 내 차 관리 화면에서 차량 상태에 따라 어떤 안내 배너를 띄울지 정하는 `resolveVehicleStatus` — 보증 임박 > 정기검사 > 주행거리 입력 유도 > 일반 안내 > 폴백 순으로 우선순위가 있는데, 기획서엔 "이 다섯 개가 있다" 정도만 적혀 있었다.

문제는 경계였다. "보증이 이미 만료됐는데 주행거리가 미입력이면?", "보증 데이터 자체가 없으면?", "배터리 보증만 임박하면 보증 배너를 띄워야 하나?" — 기획서엔 없는 케이스들. 이걸 코드로 박아두면 나중에 로직을 건드려도 우선순위가 안 무너진다.

```ts
// apps/web/src/entities/vehicle/lib/vehicleStatus.test.ts
const NOW = new Date(2026, 0, 1);

describe('resolveVehicleStatus (띠배너 우선순위)', () => {
  it('1순위 보증 임박: 기본 보증 만료가 30일 이내면 남은 일수와 함께 노출', () => {
    // 등록 2021-01-29 + 5년 = 2026-01-29 → 28일 남음.
    const status = resolveVehicleStatus(
      buildVehicle({ items: [warrantyItem()] }),
      NOW,
    );
    expect(status.kind).toBe('warranty');
    expect(status.message).toBe('기본 보증 28일 남았어요');
  });

  it('보증 임박은 기본 보증 기간만 본다 (배터리 보증·주행거리는 판정 제외)', () => {
    const status = resolveVehicleStatus(
      buildVehicle({
        spec: { registrationDate: '20200101' },
        items: [
          warrantyItem({ guaranteeYear: 10 }),
          warrantyItem({ name: '배터리 보증', guaranteeYear: 5, isBatteryWarranty: true }),
        ],
      }),
      NOW,
    );
    expect(status.kind).not.toBe('warranty');
  });

  it('보증 만료 시엔 주행거리 미입력이어도 입력 유도하지 않는다', () => {
    // 등록 2020-01-01 + 3년 = 2023 만료(과거) · 주행거리 미입력 · 검사 미대상 → 폴백
    const status = resolveVehicleStatus(
      buildVehicle({
        spec: { registrationDate: '20200101', mileage: 0 },
        items: [warrantyItem({ guaranteeYear: 3 })],
      }),
      NOW,
    );
    expect(status.kind).toBe('none');
  });
});
```

`NOW`를 인자로 주입해서 "오늘 날짜"에 의존하지 않게 만든 게 포인트다. 이렇게 안 하면 시간이 흐를수록 테스트가 저절로 깨진다. 이 파일 하나로 우선순위 5단계 + 만료/데이터 없음 같은 스킵 케이스까지 8개를 못 박았다. 기획 회의에서 "이 경우엔 뭐 뜨죠?"를 말로 하던 걸, 이제 코드가 답을 갖고 있다.

## E2E: "배포 후에 터지던" 플로우를 사람 대신 클릭

로직 밑단을 유닛으로 막았으면, 실제 화면에서 유저가 밟는 경로는 Playwright로 막는다. 대표적인 게 "미스터리 쇼퍼 경고 팝업" — 신차 상담에서 **현금/할부로 들어오면 팝업이 떠야 하고, 리스/렌트로 들어오면 뜨면 안 되는** 조건부 노출이다. 이런 게 딱 배포 후에 조용히 깨지는 자리다. 조건이 반대로 뒤집혀도 QA가 두 경로를 다 안 밟으면 놓친다.

```ts
// apps/web/tests/consulting-mystery-shopper.spec.ts
const POPUP_TITLE = '미스터리 쇼퍼 강력 대응 안내';
const BRAND = '/consulting/new-car/brand';

test.describe('미스터리 쇼퍼 경고 팝업 노출 조건', () => {
  test('현/할(CASH_INSTALLMENT) 진입 시 팝업이 노출된다', async ({ page }) => {
    await page.goto(`${BRAND}?isAll=1&category=CASH_INSTALLMENT`);
    await expect(page.getByText(POPUP_TITLE)).toBeVisible({ timeout: 15000 });
  });

  test('리/렌(LEASE_RENT) 진입 시 팝업이 노출되지 않는다', async ({ page }) => {
    await page.goto(`${BRAND}?isAll=1&category=LEASE_RENT`);
    // 하이드레이션이 끝난 뒤에도 팝업이 없어야 유의미하다.
    await expect(page.getByText('제네시스').first()).toBeVisible({ timeout: 15000 });
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1500);
    await expect(page.getByText(POPUP_TITLE)).toHaveCount(0);
  });
});
```

"안 떠야 한다"를 검증할 때는 그냥 `toHaveCount(0)`만 찍으면 안 된다. 클라이언트 렌더가 끝나기 전이면 원래 아무것도 없으니까 테스트가 무조건 통과한다(= 가짜 초록불). 그래서 화면이 실제로 그려졌다는 신호(`제네시스` 브랜드 노출)를 먼저 기다린 다음, 하이드레이션·네트워크가 잦아든 뒤에 "그래도 없음"을 확인한다.

설정은 앱이 WebView·모바일 중심이라 모바일 뷰포트를 기본으로 뒀다.

```ts
// apps/web/playwright.config.ts (일부)
export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,   // CI에선 test.only 남기면 실패
  retries: process.env.CI ? 2 : 0,
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? 'http://localhost:3000',
    trace: 'on-first-retry',       // 실패 재현용 아티팩트
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    { name: 'Mobile Chrome', use: { ...devices['Pixel 5'] } },
    { name: 'Mobile Safari', use: { ...devices['iPhone 12'] } },
    { name: 'Tablet',        use: { ...devices['iPad (gen 7)'] } },
    { name: 'chromium',      use: { ...devices['Desktop Chrome'] } },
  ],
});
```

`trace: 'on-first-retry'` 랑 `screenshot: 'only-on-failure'` 조합이 실무에서 진짜 유용하다. 성공하면 아무것도 안 남기고, 실패했을 때만 trace/스샷/영상이 남으니까 "로컬에선 되는데 CI에서만 깨지는" 걸 나중에 그대로 재생해서 볼 수 있다.

## 지금 어디까지 왔나

- **apps/web (현행 Next.js 앱)**: 여기가 중심이다. Playwright E2E 스펙 3개(미스터리 쇼퍼 팝업, 로그인 화면, 차량 목록 스모크)와 유닛 테스트 22개 파일을 붙였다. 유닛은 `next/jest` 기반 Jest로 돌고, `testPathIgnorePatterns`로 `tests/`(Playwright)를 제외해서 Jest와 Playwright가 같은 `.spec` 파일을 서로 물지 않게 분리해뒀다. 차량 상태 로직, 전화번호·이미지 유틸, 응답 인터셉터, OTP 에러 처리 같은 "조용히 깨지기 쉬운" 순수 로직 위주로 깔았다.
- **apps/레거시 웹 (Next 13 구버전 앱)**: 여기는 Pascal 맞춤 견적 플로우 하나에 E2E를 집중했다. 9단계짜리 견적 시트라 상태 전이가 복잡해서 유닛으로 쪼개기보다 실제 클릭 시나리오로 회귀를 잡는 게 나았다. 단계 스킵(리스는 연령 건너뜀), 상호 배타 옵션, 견적 만료/확정 표시까지 시나리오를 붙여둔 상태다. Node 버전이 갈려서(Playwright는 Node 20, Next 13 dev는 Node 18) 설정에서 dev 서버만 18로 띄우게 해뒀다. 레거시엔 유닛 테스트는 아직 없고, E2E 회귀 가드 용도로만 유지 중이다.

## 앞으로

지금은 "가장 자주 깨지고, 깨지면 제일 아픈 곳"부터 막은 단계다. 로드맵은 이렇다.

1. **커버리지 확대** — 상담/견적 외에 결제·인증처럼 돈이나 계정이 얽힌 플로우로 E2E를 넓힌다. 계산 로직은 계속 유닛으로 내려서 E2E를 가볍게 유지.
2. **CI 게이트로 승격** — 지금은 `--passWithNoTests`로 통과하던 걸, 핵심 경로는 테스트 실패 시 배포가 막히도록 실제 게이트로 만든다. "도구만 깔려 있던" 상태를 끝내는 게 목표.
3. **시나리오 늘리기 + 픽스처 정리** — 목/픽스처를 공용화해서 새 케이스 추가 비용을 낮춘다. 기획 회의에서 나온 엣지 케이스를 그 자리에서 테스트 케이스로 옮기는 흐름을 만든다.

목표는 사람 QA를 없애는 게 아니라, **사람이 "이게 정상 제품이 맞나"를 볼 수 있게 반복 노동을 기계한테 넘기는 것**이다. AI가 코드를 아무리 빨리 뽑아도, 그게 맞는지 확인하는 초록불은 결국 이 테스트들이 대신 지켜준다.

## 관련 작업

- `playwright config설정` (2026-07-14) — Playwright 도입 초기 설정
- `로그인 화면(Figma Set 1) E2E 테스트 추가` (2026-07-20)
- `test(consulting): Pascal 견적 플로우 E2E 8종 추가` (2026-07-27), 이후 시트 뒤로가기·질문 건너뛰기·caseId 시나리오 순차 확장
- `test(consulting): 견적 만료·확정 e2e 및 픽스처 경로·엔벨로프 갱신` (2026-07-29)
- `test: 견적함/커뮤니티 날짜 정규화 회귀 테스트 추가` (2026-07-28)
- `test: resolveVehicleStatus 띠배너 우선순위 단위테스트` (2026-08-11) — 우선순위 5단계 + 스킵 케이스 8개
- `"test": "jest --ci --passWithNoTests"` / `jest.config.js에서 Playwright 파일 제외` (2026-02-25) — 도구는 있었으나 테스트는 비어 있던 출발점
- 테스트 파일: `apps/web/playwright.config.ts`, `apps/web/tests/consulting-mystery-shopper.spec.ts`, `apps/web/src/entities/vehicle/lib/vehicleStatus.test.ts`, `apps/레거시 웹/e2e/pascal-quote.spec.ts`, `apps/레거시 웹/playwright.config.ts`
