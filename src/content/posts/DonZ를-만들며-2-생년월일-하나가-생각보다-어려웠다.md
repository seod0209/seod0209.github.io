---
title: "DonZ를 만들며 #2 — 생년월일 하나가 생각보다 어려웠다: 음력·야자시·진태양시"
date: 2026-08-31
categories: ["TypeScript"]
tags: ["사주", "일주", "음력변환", "KASI", "날짜계산", "테스트"]
---

> [1편](/posts/DonZ를-만들며-1-LLM을-안-부르기로-한-결정)에서 "생년월일시 → 일주 계산을 브라우저에서 한다"를 한 줄로 넘겼다. 추천 로직보다 이 한 줄이 훨씬 어려웠다. 60갑자 순환, 음력 환산, 시간 보정까지 — 조용히 틀리기 딱 좋은 코드라 정확도부터 못 박았다.

## 60갑자는 그냥 나머지 연산이다

일주(日柱)는 60갑자의 순환이다. 어떤 양력 날짜든 60개 중 하나로 떨어지고, 하루 지나면 다음 갑자로 넘어간다. 규칙적이라는 건, 날짜를 **연속된 정수**로 바꾸면 나머지 연산 하나로 끝난다는 뜻이다. 그 정수가 율리우스일(JDN)이다.

```ts
// (JDN + 49) % 60,  갑자 = 0
const idx = ((jdn(y, m, d) + dayShift + 49) % 60 + 60) % 60;
const g = idx % 10; // 천간(갑을병…)
const j = idx % 12; // 지지(자축인…)
```

`+49`는 앵커를 갑자(0)에 맞추는 오프셋이다. 이게 맞는지는 서로 독립인 기준일 3개로 고정했다.

| 날짜 | 기대 일진 | 검산 |
|---|---|---|
| 1900-01-01 | 甲戌 (갑술) | `(2415021+49)%60 = 10` → 갑(0)·술(10) ✅ |
| 1949-10-01 | 甲子 (갑자) | ✅ |
| 2000-01-01 | 戊午 (무오) | ✅ |

추가로 1,000일을 연속 증가시켜 60갑자가 한 칸도 안 튀고 도는지 확인했다.

### 왜 `Date`를 안 쓰고 JDN 정수 산술인가

이건 1편의 "브라우저에서 계산"과 직결된다. `Date`는 실행 환경의 타임존·DST에 물들어 있어서, 순수한 역법 계산에 끌어들이면 사용자 기기 설정에 따라 답이 흔들린다. JDN은 그냥 정수 산술(Fliegel 알고리즘)이라 환경과 무관하게 결정적이다.

```ts
function jdn(y: number, m: number, d: number): number {
  const a = Math.floor((14 - m) / 12);
  const yy = y + 4800 - a;
  const mm = m + 12 * a - 3;
  return d + Math.floor((153 * mm + 2) / 5) + 365 * yy
    + Math.floor(yy / 4) - Math.floor(yy / 100) + Math.floor(yy / 400) - 32045;
}
```

## 음력이 진짜 일이었다

양력만 받으면 위 계산으로 끝인데, 사람들은 생일을 음력으로 아는 경우가 많다. 문제는 음력엔 규칙이 없다는 거다. 달의 크기가 29일이거나 30일이고, 몇 년에 한 번 윤달이 끼는데 그 패턴을 수식으로 못 뽑는다. 결국 **표를 들고 있어야** 한다.

그래서 표를 최대한 작게 압축했다. 연도당 정수 하나.

```
packed = (윤달 << 13) | 월별 대소 비트
  · 월별 비트: 하위 비트부터 그 해 각 달(윤달 포함 순서대로) 1=30일, 0=29일
  · 윤달: 0=없음, 1~12=해당 월 뒤에 윤달
```

디코딩은 이 비트를 그대로 푸는 것이다. 윤달이 낀 해면 그 자리에 달을 하나 더 끼운다.

```ts
export function lunarMonthsOf(y: number): LunarMonth[] {
  const packed = LUNAR_TABLE.packed[y - LUNAR_TABLE.y0];
  const leapM = packed >> 13;
  const bits = packed & 0x1fff;
  const out: LunarMonth[] = [];
  let i = 0;
  for (let m = 1; m <= 12; m++) {
    out.push({ month: m, leap: false, days: (bits >> i++) & 1 ? 30 : 29 });
    if (leapM === m) out.push({ month: m, leap: true, days: (bits >> i++) & 1 ? 30 : 29 });
  }
  return out;
}
```

정월 초하루 JDN도 연도마다 절대값을 다 들고 있으면 크니까, base 하나에서의 **델타 누적**으로 저장했다.

### 표는 사람이 안 만든다

이 표(1900~2049)는 손으로 못 만든다. 한국천문연구원(KASI) 기준 라이브러리로 양력을 하루씩 훑으며 음력 달의 경계를 뽑아 자동 생성한다.

```python
# build_lunar.py — 양력을 하루씩 훑어 음력 (년,월,윤,일) 런을 수집
cal.setSolarDate(cur.year, cur.month, cur.day)
ly, lm, ld = map(int, iso.split('-'))          # 그날의 음력 연·월·일
...
for i, (m, leap, days) in enumerate(ms):
    assert days in (29, 30), (ly, m, leap, days) # 달은 29/30일뿐
    if days == 30: bits |= (1 << i)
assert len(ms) == (13 if leapm else 12)          # 윤달 있으면 13달
```

생성물엔 `AUTO-GENERATED ... do not edit by hand` 헤더를 박아, 이건 소스가 아니라 산출물임을 못 박았다.

### 그리고 전수로 대조했다

압축·디코딩을 직접 짰으니, 비트 하나 밀리면 조용히 틀린다. 그래서 범위 안의 **모든 유효 음력 날짜**를 라이브러리와 내 JS 구현으로 각각 변환해 맞대봤다.

```python
# verify_lunar.py — 1900~2049 × 12월 × {평/윤} × {1,15,29,30일} 전수
for y in range(1900, 2050):
  for m in range(1, 13):
    for leap in (False, True):
      for d in (1, 15, 29, 30):
        if cal2.setLunarDate(y, m, d, leap):    # 존재하는 날짜만
          cases.append([y, m, d, leap, cal2.SolarIsoFormat()])
```

유효 조합 **6,549건 전수 대조 100% 일치.** 2049년 이후가 필요해지면 `build_lunar.py`로 표만 다시 뽑으면 된다.

## 시간 보정 — 있으면 하고, 없으면 안 한다

일주는 자시(23시) 경계에서 갈리므로, 출생 "시각"이 들어오면 그 시각을 실제 태양·시계 기준으로 되돌린 뒤 날짜 경계를 다시 판정해야 한다. 시각을 안 넣으면 정오로 두고 **보정을 아예 건너뛴다** — 없는 정보를 지어내지 않는다.

보정은 순서가 중요하다. 되돌리기 → 진태양시 → 날짜 이월 → 야자시.

```ts
if (hasTime) {
  // 1) 서머타임 되돌리기: 시행 구간 출생은 시계가 1시간 앞서 있었음
  if (o.useDst !== false && inDst(y, m, d, hh, mi)) {
    totalMin -= 60;
    adjustedNote.push({ kind: 'dst' });
  }
  // 2) 진태양시: 표준자오선과 실제 경도 차이 (1도 = 4분)
  if (o.useTrueSolarTime !== false) {
    const lon = o.longitude ?? 126.978;          // 서울
    const delta = Math.round((lon - standardMeridian(y, m, d)) * 4);
    totalMin += delta;                            // 서울 vs 135° ≈ −32분
    adjustedNote.push({ kind: 'trueSolar', minutes: delta });
  }
}
let dayShift = Math.floor(totalMin / 1440);
const minOfDay = ((totalMin % 1440) + 1440) % 1440;
// 3) 야자시: 23:00 이후는 다음 날 일주로
if (hasTime && rule === 'next' && minOfDay >= 23 * 60) {
  dayShift += 1;
  adjustedNote.push({ kind: 'lateNight' });
}
```

네 가지가 얽혀 있다.

- **서머타임** — 1948~51·1955~60·1987~88 시행 구간. 이 구간 출생은 −1시간. 대부분은 일주가 안 바뀌지만, 늦은 밤이면 자시 경계를 넘나든다.
- **진태양시** — 서울 경도(126.978°)는 한국 표준자오선보다 서쪽이라 약 −32분. `standardMeridian`은 날짜에 따라 값이 바뀐다(아래).
- **표준시 자오선 변경 이력** — 1912·1954·1961년에 자오선이 127.5°↔135°로 오갔다. `standardMeridian(y,m,d)`가 그 구간을 반영하므로, 진태양시 보정량이 시대마다 달라진다.
- **야자시** — 기본은 `next`(23시 이후 = 다음 날 일주). `same`으로 주면 조자시론으로 전환된다.

보정으로 시각이 날짜를 넘나들 수 있어 `dayShift`(일 단위 이월)로 흡수하고, 최종 `idx`가 그 `dayShift`를 반영한다. 어떤 보정이 걸렸는지는 `adjustments`로 돌려줘 결과 화면에 표시한다 — "왜 내가 아는 날짜와 다르지?"에 답하기 위해서다.

> 곁다리로, 사주 여덟 글자의 오행 분포를 세어 **제일 부족한 오행**을 뽑아 행운 아이템 색에 쓴다. 다만 월주는 절기 근사표(±1일 오차 가능)를 쓰므로, 이건 정밀 만세력이 아니라 **재미용 근사**임을 코드 주석에 명시해뒀다.

## 데이터는 파이썬이 낳고, 런타임은 TS가 조회만 한다

정리하면 경계가 이렇게 갈린다.

- **생성 시점(파이썬)** — `build_lunar.py`가 KASI를 훑어 표를 낳고, `verify_lunar.py`가 전수 검증한다. 무겁고, 한 번만 돌리고, 산출물을 커밋한다.
- **런타임(TS `engine.ts`)** — 의존성 0. 표를 조회하고 JDN 나머지 연산과 시간 보정만 한다. 그래서 서버도, 네트워크도 필요 없다(→ 1편의 "브라우저 계산"이 성립하는 이유).

## 마무리

정확도는 눈으로 못 지킨다. 초당 흘러가는 프레임이 아니라 60갑자 한 칸이라도, 비트 하나·오프셋 하나 틀리면 조용히 그른 답을 내놓는다. 그래서 **독립 앵커 3개 + 음력 6,549건 전수 대조**로 못 박고, 보정은 "있으면 하고 없으면 안 하는" 규칙으로 단순화했다. 그 위에서야 1편의 "브라우저에서 계산" 한 줄을 마음 놓고 쓸 수 있었다.

## 관련 작업

- 런타임 엔진: `src/lib/ilju/engine.ts` — JDN 산술(`jdn`/`fromJdn`), `idx=(JDN+49)%60`, 음력 디코딩(`lunarMonthsOf`/`lunarToSolar`), 시간 보정(`calc`: DST·진태양시·야자시·표준시 자오선).
- 음력 표: `src/lib/ilju/lunar-table.ts` (자동 생성, packed 인코딩).
- 생성·검증 도구: `ilju-widget/build_lunar.py`(KASI → 표), `ilju-widget/verify_lunar.py`(전수 대조 6,549건).
- 앞 편: [DonZ를 만들며 #1 — LLM을 안 부르기로 한 결정](/posts/DonZ를-만들며-1-LLM을-안-부르기로-한-결정)
- 다음 편: 「만들고 나니 검색에 안 나왔다 — 사이드 프로젝트 SEO 수정기」
