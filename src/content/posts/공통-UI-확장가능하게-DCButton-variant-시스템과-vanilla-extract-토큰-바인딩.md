---
title: "공통 UI를 확장 가능하게: DCButton variant 시스템과 vanilla-extract 토큰 바인딩"
date: 2026-08-12
categories: ["Design System"]
tags: ["Design System", "vanilla-extract", "React", "Storybook", "Design Token"]
---

> 디자인 시스템 시리즈의 한 편. 앞선 글에서 흩어진 토큰을 빌드 파이프라인으로 세운 얘기를 했다면, 이번엔 그 토큰을 **실제 컴포넌트**로 소비하는 첫 실물, 공통 버튼 `DCButton` 얘기다.

## 버튼 하나 만드는 게 왜 이렇게 어렵나

버튼이다. 세상에서 제일 흔한 컴포넌트. 근데 디자인 시스템에서 버튼을 "제대로" 하나 만들려고 앉으니까 조합이 순식간에 폭발했다.

- **frame**: solid(꽉 찬 사각), round(꽉 찬 알약), line(테두리만), text(글자만)
- **variant(색)**: primary / secondary / assistive / tertiary
- **size**: x-small / small / medium / large / x-large
- **state**: 기본 / disabled / (앱에선) loading
- 거기에 왼/오른쪽 아이콘, line 버튼의 배경 채움 여부, text 버튼의 밑줄까지...

곱해보면 solid 계열만 `4 variant × 5 size × 상태` 라 우습게 수십 개다. 여기서 흔히 하는 실수가 두 가지다.

1. `<Button primary large solid />` 처럼 **불리언 프롭을 우수수 뿌리는 것.** `primary`랑 `secondary`를 동시에 켜면? 타입은 통과하는데 스타일은 지옥이다.
2. 색이랑 간격을 **컴포넌트 안에 하드코딩**하는 것. `#0064AA`, `padding: 13px 12px` 이런 게 컴포넌트마다 박히면, 디자인이 바뀔 때 grep 지옥에 빠진다. (실제로 우리 레포는 tailwind·emotion·styled-components·MUI가 한 앱에 7종씩 섞여 있어서 색 하나 바꾸는 게 고고학 발굴이었다.)

그래서 두 가지를 목표로 잡았다.
- **프롭 몇 개로 조합을 다 담기** — 불리언 난사 말고, 유한한 문자열 유니온으로.
- **색·간격·타이포를 하드코딩 없이 토큰에 묶기** — 그것도 런타임 비용 없이.

## 왜 styled-components/emotion이 아니라 vanilla-extract인가

처음엔 익숙한 emotion이나 styled-components를 떠올렸다. 근데 이번엔 안 골랐다. 이유가 있다.

- **런타임 비용.** styled-components/emotion은 브라우저에서 렌더링될 때 스타일 객체를 직렬화하고 `<style>` 태그를 주입한다. 버튼 수십 종 × 화면 여기저기면 그 비용이 계속 쌓인다.
- **SSR.** Next 기반이라 서버에서 스타일을 뽑아야 하는데, 런타임 CSS-in-JS는 SSR 설정이 은근 까다롭고 하이드레이션 미스매치도 잘 난다.
- **토큰 일관성.** 무엇보다, 나는 토큰을 "**타입이 붙은 계약**"으로 쓰고 싶었다.

그래서 [vanilla-extract](https://vanilla-extract.style/)를 골랐다. 얘의 핵심은 **zero-runtime**이다. `.css.ts` 파일에 타입스크립트로 스타일을 쓰면, **빌드 타임에 순수 CSS로 컴파일**된다. 런타임에 남는 건 클래스 이름 문자열뿐. styled-components처럼 브라우저에서 스타일을 만들어내지 않는다.

덤으로 `.css.ts`는 그냥 TS라, 토큰을 `import` 해서 자동완성 받으며 쓸 수 있다. 오타 내면 빌드가 깨진다. 이게 "타입된 계약"의 실체다.

## 토큰을 CSS 변수로 — `createGlobalTheme`

먼저 토큰이 CSS 변수로 심어지는 지점. `theme/globalTheme.css.ts`가 Figma에서 동기화된 `designTokens`를 받아 `:root`에 CSS 커스텀 프로퍼티로 깐다.

```ts
// theme/globalTheme.css.ts
import { createGlobalTheme, globalStyle } from '@vanilla-extract/css';
import { designTokens } from './designTokens';

const primitive = designTokens.color.primitive;
const semantic = designTokens.color.semantic;

// spacing/radius는 숫자 → "px" 문자열로 승격
function withPx<T extends Record<string, number>>(obj: T): Record<keyof T, string> {
  const out = {} as Record<keyof T, string>;
  for (const [k, v] of Object.entries(obj)) out[k as keyof T] = `${v}px`;
  return out;
}
const space = withPx(designTokens.spacing);
const radius = withPx(designTokens.radius);

export const globalStyles = createGlobalTheme(':root', {
  color: {
    // ...primitive 팔레트(red/blue/coolGray...)
    // 신규 스타일은 아래 semantic(text/bg/border/icon/action)을 우선 쓴다.
    // design-tokens.json 의 color.semantic 을 그대로 미러링 → tokens:sync 하면 자동 반영
    semantic,
  },
  space,
  radius,
  typography,
  mediaQuery: { /* mobile/tablet/laptop/desktop/wide */ },
});
```

`createGlobalTheme(':root', {...})`가 하는 일은 두 가지다.

1. 넘긴 객체 구조 그대로 `--...` CSS 변수를 `:root`에 정의한다.
2. **같은 구조의 타입된 접근 객체**(`globalStyles`)를 돌려준다. 그래서 컴포넌트에선 `globalStyles.color.semantic.action.button.primary` 라고 쓰면 그게 컴파일 시점에 `var(--color-semantic-action-button-primary-...)` 로 치환된다.

핵심은 **하드코딩된 색이 컴포넌트에 안 들어간다**는 것. 값은 전부 `:root`의 CSS 변수 한 군데에 모여 있고, 컴포넌트는 그걸 참조만 한다. Figma 토큰이 바뀌면 `tokens:sync`로 JSON을 미러링하고, semantic 경로가 같으니 사용처는 손 안 대도 반영된다.

> 💡 `semantic`을 통째로 스프레드해서 미러링하는 게 포인트. JSON에 새 semantic 토큰이 추가돼도 수동 매핑을 안 해도 된다. (`JSON을 통째로 미러링` 커밋에서 이 방식으로 정리했다.)

## 타이포는 preset 조각으로 — `typographyPreset`

색만 토큰이 아니다. 폰트 크기/굵기/행간/자간도 전부 토큰이어야 한다. 근데 이걸 매번 4줄씩 쓰면 그것도 하드코딩이나 다름없다. 그래서 Figma의 "Title / Label / Paragraph" 스타일을 **스프레드 가능한 조각**으로 만들어 뒀다.

```ts
// theme/typographyPreset.ts
function toPreset(token: TypographyToken): TypographyPreset {
  return {
    fontSize: `${token.fontSize}px`,
    fontWeight: String(token.fontWeight),
    lineHeight: `${token.lineHeight}px`,
    letterSpacing: letterSpacingToCss(token.letterSpacing, token.fontSize),
  };
}

export const typographyPreset = {
  title: mapGroup(ty.title),
  label: mapGroup(ty.label),
  paragraph: mapGroup(ty.paragraph),
};
```

여기 `letterSpacingToCss`가 은근 중요하다. Figma는 자간을 **폰트 크기 대비 퍼센트**(`"-0.5%"`)로 뽑아주는데, 이건 CSS `letter-spacing` 속성엔 못 넣는다. 그래서 px로 환산한다.

```ts
// "-0.5%" 처럼 %로 온 자간을 px로 환산
function letterSpacingToCss(ls: number | string, fontSize: number): string {
  if (typeof ls === 'number') return `${ls}px`;
  if (ls.trim().endsWith('%')) {
    const px = (parseFloat(ls) / 100) * fontSize;   // 14px * -0.5% = -0.07px...
    return `${Number(px.toFixed(2))}px`;
  }
  return ls;
}
```

실제로 이 근처에서 디자인 정합 작업을 한 번 했다. label `14B` 토큰의 lineHeight를 20에서 18로 조이고, letterSpacing을 `-0.5%`(비율)에서 tight한 `-0.5px`(절대값)로 바꾼 동기화 커밋(`Figma 최신 label 타이포 토큰 동기화`)이 그거다. 이렇게 preset을 통해 한 군데서 바꾸니까, 이 타이포를 쓰는 모든 버튼·칩·인풋이 한 번에 조여졌다.

그럼 컴포넌트에서 쓸 땐 이렇게 한 줄이다.

```ts
size: {
  medium: {
    height: '44px',
    ...typographyPreset.label['14B'],   // fontSize/weight/lineHeight/letterSpacing 한 방에
    padding: '13px 12px',
    borderRadius: globalStyles.radius[8],
    gap: globalStyles.space[6],
  },
}
```

> `fontFamily`는 일부러 preset에서 뺐다. body 전역 폰트 스택(Pretendard + fallback)을 상속받게 두려고. 조각이 폰트 패밀리를 덮어쓰면 안 되니까.

## 조합 폭발을 재우는 법 — `recipe`

이제 본론. 조합을 어떻게 프롭 몇 개로 담느냐. vanilla-extract의 `recipe`가 답이었다. `recipe`는 **base(공통) + variants(축별 스타일) + compoundVariants(축 조합별 예외)** 를 선언하면, `Wrapper({ variant, size })` 처럼 **골라 부르는 클래스 팩토리**를 만들어준다.

solid 사각 버튼 레시피의 뼈대다.

```ts
// components/buttons/SolidRectangleButton/index.css.ts
import { recipe } from '@vanilla-extract/recipes';
import { globalStyles } from '../../../theme/globalTheme.css';
import { overlayEffects } from '../../../theme/hoverUtils.css';
import { typographyPreset } from '../../../theme/typographyPreset';

export const Wrapper = recipe({
  base: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: globalStyles.color.semantic.text.inverse,
    position: 'relative',
    width: 'fit-content',
    selectors: {
      '&:disabled': {
        backgroundColor: globalStyles.color.semantic.action.button.disable,
        color: globalStyles.color.semantic.text.disabled,
        pointerEvents: 'none',
      },
    },
  },
  variants: {
    // 축 1: 색
    variant: {
      primary:   { color: globalStyles.color.semantic.text.inverse,  backgroundColor: globalStyles.color.semantic.action.button.primary },
      secondary: { color: globalStyles.color.semantic.text.primary,  backgroundColor: globalStyles.color.semantic.action.button.secondary },
      assistive: { color: globalStyles.color.semantic.text.inverse,  backgroundColor: globalStyles.color.semantic.action.button.assistive },
      tertiary:  { color: globalStyles.color.semantic.text.primary,  backgroundColor: globalStyles.color.semantic.action.button.tertiary },
    },
    // 축 2: 크기 (높이/타이포/패딩/라운드/gap을 통째로)
    size: {
      'x-small': { height: '32px', ...typographyPreset.label['12SB'], padding: '6px 10px',  borderRadius: globalStyles.radius[8],  gap: globalStyles.space[4] },
      small:     { height: '36px', ...typographyPreset.label['13SB'], padding: '8px 10px',  borderRadius: globalStyles.radius[8],  gap: globalStyles.space[6] },
      medium:    { height: '44px', ...typographyPreset.label['14B'],  padding: '13px 12px', borderRadius: globalStyles.radius[8],  gap: globalStyles.space[6] },
      large:     { height: '48px', ...typographyPreset.label['14B'],  padding: '14px 16px', borderRadius: globalStyles.radius[8],  gap: globalStyles.space[8] },
      'x-large': { height: '56px', ...typographyPreset.title['16B'],  padding: '18px 16px', borderRadius: globalStyles.radius[12], gap: globalStyles.space[8] },
    },
  },
  // 축 조합별 예외: hover/press 오버레이는 색+라운드에 따라 흰/검을 다르게
  compoundVariants: [
    { variants: { variant: 'primary', size: 'medium' },
      style: { selectors: { ...overlayEffects.white({ borderRadius: globalStyles.radius[8] }) } } },
    { variants: { variant: 'secondary', size: 'x-small' },
      style: { selectors: { ...overlayEffects.dark({ borderRadius: globalStyles.radius[8] }) } } },
    // ...색×크기 조합만큼
  ],
});
```

여기서 조합 폭발이 어떻게 잡히는지가 보인다.

- **곱셈이 아니라 덧셈.** `4 variant × 5 size = 20`을 다 나열하는 게 아니라, `variant` 4개 + `size` 5개를 **따로** 선언한다. 실제 조합은 `Wrapper({ variant: 'primary', size: 'medium' })` 호출 시 클래스 두 개가 합쳐지며 만들어진다.
- **정말 조합에 의존하는 것만 `compoundVariants`로.** 예를 들어 hover/press 오버레이 색(밝은 버튼엔 검은 오버레이, 어두운 버튼엔 흰 오버레이)이나, x-large만 라운드가 12px인 예외 같은 것. 이건 어쩔 수 없이 축 조합을 알아야 해서 여기 둔다.
- **모든 값이 토큰 참조.** `#색상`이나 매직넘버 대신 `globalStyles.color.semantic.*`, `globalStyles.radius[8]`, `globalStyles.space[6]`. `disabled`도 `:disabled` 셀렉터에서 semantic 토큰으로.

round 버튼도 같은 구조인데, `borderRadius: '100px'`(알약) 하나 다르고, 오버레이를 아예 `variant` 안에서 처리한다.

```ts
// components/buttons/SolidRoundButton/index.css.ts (발췌)
variant: {
  primary: {
    color: globalStyles.color.semantic.text.inverse,
    backgroundColor: globalStyles.color.semantic.action.button.primary,
    selectors: { ...overlayEffects.white({ borderRadius: '100px' }) },
  },
  secondary: {
    color: globalStyles.color.semantic.text.primary,
    backgroundColor: globalStyles.color.semantic.action.button.secondary,
    selectors: { ...overlayEffects.dark({ borderRadius: '100px' }) },
  },
  // ...
},
```

line 버튼은 배경 채움(`backgroundColor: true`)이라는 축이 하나 더 붙고, 색 대신 `border`를 토큰으로 그린다.

```ts
// components/buttons/LineButton/index.css.ts (발췌)
variants: {
  backgroundColor: {
    true: { backgroundColor: globalStyles.color.semantic.bg.primary },
  },
  variant: {
    primary:   { color: globalStyles.color.semantic.text.primary,   border: `1.4px solid ${globalStyles.color.semantic.icon.primary}` },
    secondary: { color: globalStyles.color.semantic.text.secondary, border: `1.4px solid ${globalStyles.color.semantic.border.default}` },
    assistive: { color: globalStyles.color.semantic.text.primary,   border: `1.4px solid ${globalStyles.color.semantic.text.accent}` },
  },
  // size는 solid와 동일 패턴
},
```

text 버튼은 색 variant가 아예 없고(글자 버튼이라), `size`(small/medium)와 `bottomLine`(밑줄) 축만 있다.

```ts
// components/buttons/TextButton/index.css.ts (발췌)
variants: {
  size: {
    small:  { height: '16px', fontSize: globalStyles.typography.fontSize[2], fontWeight: globalStyles.typography.fontWeight.medium, lineHeight: globalStyles.typography.lineHeight[18], gap: globalStyles.space[2] },
    medium: { height: '20px', fontSize: globalStyles.typography.fontSize[4], fontWeight: globalStyles.typography.fontWeight.medium, lineHeight: globalStyles.typography.lineHeight[13], gap: globalStyles.space[4] },
  },
  bottomLine: {
    true: { borderBottom: '1px solid currentColor' },
  },
},
```

## 타입으로 잘못된 조합을 막는다

프롭이 폭발하지 않게 하는 두 번째 장치는 **판별 유니온(discriminated union)** 이다. `frame`을 판별자로 두고, frame마다 허용되는 프롭을 다르게 묶었다.

```ts
// types/Button.ts
export type SolidRectangleButtonProps = {
  frame: 'solid';
  variant: 'primary' | 'secondary' | 'assistive' | 'tertiary';
  size: Size;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  children?: React.ReactNode;
};

export type LineButtonProps = {
  frame: 'line';
  variant: 'primary' | 'secondary' | 'assistive'; // line엔 tertiary 없음
  size: Size;
  backgroundColor?: boolean;                       // line에만 있는 축
  // ...
};

export type TextButtonProps = {
  frame: 'text';
  size: Extract<Size, 'small' | 'medium'>;         // text는 small/medium만
  bottomLine?: boolean;                            // text에만 있는 축
  // variant 없음
  // ...
};

export type ButtonProps =
  | SolidRectangleButtonProps
  | SolidRoundButtonProps
  | LineButtonProps
  | TextButtonProps;
```

이렇게 하면 `frame="text"`인데 `variant="primary"`를 주면 **컴파일 에러**다. line 버튼에 `tertiary`도 못 준다. text 버튼에 `size="x-large"`도 막힌다. "될 수 없는 조합"이 타입에서 원천 차단된다. 불리언 난사 방식으론 절대 못 얻는 안전성이다.

디스패치는 단순하다. 하나의 `DCButton`이 `frame`으로 갈래를 탄다.

```tsx
// components/buttons/button.tsx
const DCButton = (props: ButtonProps & ComponentPropsWithRef<'button'>) => {
  const { frame } = props;
  if (frame === 'solid') return <SolidRectangleButton {...props} />;
  if (frame === 'round') return <SolidRoundButton {...props} />;
  if (frame === 'line')  return <LineButton {...props} />;
  if (frame === 'text')  return <TextButton {...props} />;
};
```

그리고 각 하위 컴포넌트는 recipe가 만들어준 클래스 팩토리를 `className`에 꽂기만 하면 끝이다.

```tsx
// components/buttons/SolidRectangleButton/index.tsx
const SolidRectangleButton = (props: SolidButtonProps) => {
  const { onClick, children, variant, size, leftIcon, rightIcon, ...rest } = props;
  return (
    <button className={Wrapper({ variant, size })} onClick={onClick} {...rest}>
      {leftIcon && <div className={IconWrapper({ size })}>{leftIcon}</div>}
      {children}
      {rightIcon && <div className={IconWrapper({ size })}>{rightIcon}</div>}
    </button>
  );
};
```

`...rest`로 네이티브 `<button>` 속성(`disabled`, `type`, `aria-*` 등)을 그대로 흘려보내는 것도 포인트다. 그래서 `disabled`를 주면 위 recipe의 `&:disabled` 셀렉터가 알아서 disable 토큰 색으로 바뀐다. 상태를 위한 별도 프롭을 안 만들어도 된다.

> loading은 DS 버튼 자체 프롭이 아니라 **앱 쪽에서 조합**한다. 실제로 조회 CTA를 `DCButton`으로 전환하면서 loading 상태를 앱 스텝에서 얹은 커밋(`조회하기 버튼 DCButton(loading)로 전환`)이 있다. 상태 표현을 컴포넌트에 다 우겨넣지 않고, disabled 같은 표준 상태만 DS가 책임지는 선택.

## 확장성은 Storybook이 증명한다

"확장 가능하다"는 말은 문서로 증명돼야 한다. 그래서 frame별로 스토리를 **파일 단위로 분리**하고, 모든 축을 Storybook Controls 패널에 노출했다. 개발자가 코드 안 열고도 variant×size×상태를 실시간으로 돌려볼 수 있다.

```tsx
// apps/web/stories/DCButton/SolidRectangle.stories.tsx
import DCButton from '@shared/DesignSystem/buttons/button';
import type { Meta, StoryObj } from '@storybook/react';

type Args = {
  variant: 'primary' | 'secondary' | 'assistive' | 'tertiary';
  size: 'x-small' | 'small' | 'medium' | 'large' | 'x-large';
  disabled: boolean;
  children: string;
  showLeftIcon: boolean;
  showRightIcon: boolean;
};

const meta: Meta<Args> = {
  title: 'DCButton/Solid Rectangle',
  component: DCButton,
  argTypes: {
    variant: { control: 'select', options: ['primary', 'secondary', 'assistive', 'tertiary'], description: '색상 variant' },
    size:    { control: 'select', options: ['x-small', 'small', 'medium', 'large', 'x-large'], description: '버튼 크기' },
    disabled: { control: 'boolean', description: '비활성화 상태' },
    children: { control: 'text', description: '버튼 텍스트' },
    showLeftIcon:  { control: 'boolean', description: '왼쪽 아이콘' },
    showRightIcon: { control: 'boolean', description: '오른쪽 아이콘' },
  },
  args: { variant: 'primary', size: 'medium', disabled: false, children: 'Label', showLeftIcon: false, showRightIcon: false },
  render: ({ variant, size, disabled, children, showLeftIcon, showRightIcon }) => (
    <DCButton
      frame="solid"
      variant={variant}
      size={size}
      disabled={disabled}
      leftIcon={showLeftIcon ? iconEl : undefined}
      rightIcon={showRightIcon ? iconEl : undefined}
    >
      {children}
    </DCButton>
  ),
};

export default meta;
export const Playground: StoryObj<Args> = {};
```

line 스토리는 여기에 `backgroundColor` 컨트롤이 붙고 variant 옵션에서 tertiary가 빠진다(`variant: '... (line은 tertiary 없음)'`). text 스토리는 variant가 통째로 없고 `bottomLine`과 `size: small/medium`만 노출된다. **스토리의 Args가 곧 그 frame의 실제 표면적**이라, 타입 정의와 문서가 한 몸으로 움직인다.

이 "프레임별 파일 분리 + Controls 기반" 전환은 실제 리팩터링 커밋(`버튼 스토리를 프레임별 파일로 분리 + Controls 기반 전환`)으로 정리했고, 같은 패턴을 IconButton·ActionChip·Navigation 등 다른 공통 컴포넌트로도 확장했다.

## 정리

- **조합 폭발**은 불리언 난사가 아니라 **유한한 문자열 유니온 + `frame` 판별 유니온**으로 잡는다. 될 수 없는 조합은 타입에서 컴파일 에러.
- **스타일 조합**은 vanilla-extract `recipe`의 base + variants(덧셈) + compoundVariants(진짜 예외만)로 관리한다.
- **색·간격·타이포는 하드코딩 금지.** `createGlobalTheme`로 토큰을 `:root` CSS 변수로 깔고, 컴포넌트는 `globalStyles.*`와 `typographyPreset.*`로 참조만. Figma가 바뀌면 `tokens:sync` 한 번.
- **zero-runtime.** 빌드 타임에 CSS로 컴파일되니 SSR도 깔끔하고 런타임 스타일 주입 비용이 없다.
- **확장성은 Storybook Controls로 문서화**해서 눈으로 증명한다.

버튼 하나에 이 짓을 다 해두면, 다음 컴포넌트(칩·인풋·네비게이션)는 같은 레일 위를 달린다. 실제로 `DCTextField`, `ActionChip`, `SegmentedControl`도 전부 동일하게 `globalStyles` + `typographyPreset` + `recipe` 조합으로 붙였다. 첫 발은 전편에서 토큰으로 뗐고, 이번 편은 그 토큰을 실제 컴포넌트가 소비하게 만든 단계다. 이렇게 컴포넌트를 하나씩 같은 레일에 올리면서 디자인 시스템을 점차 넓혀가는 중이다.

## 관련 작업

- `feat(ds-button): Solid/Line/Text 버튼 최신 Figma 스펙 정합 — typographyPreset·action.button 토큰·disabled 색상`
- `refactor(ds-button): 버튼 스토리를 프레임별 파일로 분리 + Controls 기반 전환 (SolidRectangle/SolidRound/Line/Text)`
- `fix(design-system): Figma 최신 label 타이포 토큰 동기화 (14B lineHeight 20→18, label letterSpacing -0.5% → tight -0.5px)`
- `fix: 조회하기 버튼 DCButton(loading)로 전환 + CTA 바 1px 라인 제거`
- `JSON을 통째로 미러링 — tokens:sync로 semantic 토큰 자동 반영`
- `typography 프리셋(title/label/paragraph) 노출` · `DX: vanilla-extract CSS 변수 식별성 개선`
- 코드 근거: `packages/design-system/web/src/components/buttons/{button.tsx, SolidRectangleButton, SolidRoundButton, LineButton, TextButton}`, `theme/{globalTheme.css.ts, typographyPreset.ts}`, `types/Button.ts`, `apps/web/stories/DCButton/*.stories.tsx`, `apps/web/src/shared/DesignSystem/buttons/button.tsx`
