`title: State and Props author: dongee_seo date: 2023-05-11 categories: [Blogging] tags: [React]`

# 데이터 바인딩

## 데이터 바인딩?

- **화면상에 보여지는 데이터(View)**와 
  **브라우저 메모리에 있는 데이터(Model)**를 묶어서(Binding)
  서로 간의 데이터를 동기화하는 것

=> HTML에서 서버 혹은 스크립트상에서 받아온 데이터를 화면상에 그려주고 있다고 가정을 했을 때, 
**해당 값이 변경이 될 경우** 다시 HTML 상에 데이터(값)를 **변경된 값에 따라서 맞추어 주는 동작.**

- **HTML에서 변경된 내용이 데이터에 영향을 미치는지**에 대한 차이를 기준으로 '양방향', '단방향' 바인딩으로 구분.
- **값을 데이터 바인딩한다/ CSS 값(스타일)을 데이터 바인딩한다.**

## 단방향 데이터 바인딩(One way Data Binding)

![](https://velog.velcdn.com/images/seod0209/post/2254e132-dac3-48ec-8e21-f669a3902cd4/image.gif)

![](https://velog.velcdn.com/images/seod0209/post/264870d8-e88e-4c11-b699-3f3ab5da9972/image.png)

1. 컴포넌트 내에서 '**단방향 데이터 바인딩**': **[JS(Model) -> HTML(View)]
   **Javascript(Model)에서 HTML(View)로 한 방향으로만 데이터를 동기화하는 것을 의미.

**[HTML(View) -> JS(Model)] 가능여부?**
역으로 HTML(View)에서 JS(Model)로의 직접적인 데이터 갱신은 불가능.
 '이벤트 함수(onClick, onChange,...)'를 주고 함수를 호출한 뒤 Javascript에서 HTML로 데이터를 변경해야 함.

2. 컴포넌트 간에서 단방향 데이터 바인딩
   : **부모 컴포넌트에서 자식 컴포넌트로만 데이터가 전달되는 구조.**

자식 컴포넌트에서 event (onChange, onClick, onBlur, …)가 발생할 때
부모 컴포넌트에서 전달한 핸들러를 통해 state를 바꾸는 등의 양방향 바인딩 같은 동작이 일어나도록 하면 된다. 이를 **state 끌어올리기(lifting state up)**를 통해 구현

💡 대표적으로 SPA Framework에서는 React에서 단방향 데이터 바인딩, 리덕스

성능 저하 없이 DOM을 렌더링
변화된 값을 매번 감지하고 바인딩하기 때문에 코드가 길어짐.

## 양방향 데이터 바인딩(Two way Data Binding)

![](https://velog.velcdn.com/images/seod0209/post/a7e18e87-88fb-40dd-88db-d773332ea834/image.gif)

![](https://velog.velcdn.com/images/seod0209/post/081bdf7c-681e-426a-be33-83d432372cca/image.png)

1. 컴포넌트 내에서 **'양방향 데이터 바인딩'**
   : **[HTML(View) <-> ViewModel <-> Javascript(Model)]**

Javascript(Model)와 HTML(View) 사이에 ViewModel이 존재하여 하나로 묶여서(Binding)

⇒ **둘 중 하나만 변경되어도 함께 변경되는 것을 의미**

양방향 바인딩은 데이터의 변경을 감지하고 있다가 데이터가 변경되는 시점에 DOM객체에 렌더링을 해주거나 모델의 변경을 감지해 JavaScript 실행부에서 변경
데이터의 변화를 감지해 템플릿과 결합해 화면을 갱신, 화면의 입력에 따라 데이터를 갱신

컴포넌트 간에서는 부모와 자식 모두 데이터를 직접 변경할 수 있다.
부모 컴포넌트에서 자식 컴포넌트로는 Props를 통해 데이터를 전달,
자식 컴포넌트에서 부모 컴포넌트로는 Emit Event를 통해서 데이터를 전달.

💡 대표적으로 SPA Framework에서는 Vue.js,Angular에서 양방향 데이터 바인딩 가능.

**변화에 따라 DOM 객체 전체를 렌더링 하거나 데이터를 바꿔 성능이 감소**

# Props vs State

> props와 state의 차이🔥
> Props가 컴포넌트간에 전달받는 것이라고 했는데 자식에서 부모로도 전달할 수 있는가 🔥
> 데이터 전달 방식중 단방향, 양방향 장단점. 그럼 리액트는 어떤 방식을 사용?

props와 state를 구분하는 기준은, 어떤 컴포넌트에 입장에서 말하는 지에 따라서 달라집니다.

![](https://velog.velcdn.com/images/seod0209/post/1590a972-3f04-4e05-b956-9f13b5be56a4/image.png)

### **Props**

- React가 사용자 정의 컴포넌트로 작성한 element를 발견하면 JSX attribute를 해당 컴포넌트에 단일 객체로 전달합니다. 이 객체를 “props”라고 합니다.
- **부모로부터 전달되고 상속받음.
  (부모->자식의 일방향성 상속이라는 리액트 특징때문)**
- 읽기 전용: 자식 컴포넌트 내에서 수정이 불가능. 부모 요소에서 설정

> JSX attribute(속성)
> : key, children, ref 등. UI를 구성하는 "클래스" 이므로, 속성을 가질 수 있다.

### **State (상태)**

- 현재 컴포넌트에서 생성, 변할 수 있는 데이터.
  오직 state가 생성된 컴포넌트 내에서만 변경이 가능.
- **컴포넌트 내부에서 선언되기 때문에 외부에 공개하지 않고 컴포넌트가 스스로 관리**
- state가 변경되면 컴포넌트를 다시 렌더링 해야함.
- **반드시 객체 형태로 생성 되거나 아니면 null (state를 정의하지 않음) 타입**

#### 1. 클래스형 컴포넌트: this.setState

- state 업데이트를 하려면 무조건 setState라는 메소드를 사용.
- setState라는 메소드를 클래스 어디에서도 생성한 적이 없지만,
  extends Component라는 구문을 통해서 **리액트 컴포넌트 클래스를 상속** 받고 있기 때문에
  this.setState 사용 가능.
- setState메소드를 사용하지 않고 state property에 접근해서 값을 변경하는 경우
  그 값이 실제 HTML상으로는 업데이트 되지 않게 됨.

> 리액트에서는 효율적으로 "HTML이 업데이트 되어야 할 부분만을 감지해서 업데이트" 한다고 했었습니다. 그렇기 위해서 리액트 개발팀에서 **특정한 작업이 이루어 졌을 때에만 HTML이 업데이트 되도록 만든 규칙 중 하나가 바로 setState실행** 입니다.
> 따라서 다른 방법으로 state를 변경하게 되면 변경된 값을 HTML에서는 볼 수가 없게 됩니다.

setState메소드의 사용방법에는 여러 가지가 있지만,
일반적으로 setState( { 업데이트할 state property: 값 } ) 과 같은 객체 형태로 업데이트.

```jsx
this.setState({
  helloMessage: "Change"
});
```

#### 2. 함수형 컴포넌트: useState

```jsx
const [value, setValue] = useState(0);
```

- useState 함수의 매개변수(parameter)는 초기화할 값을 넣어줌.
- 배열의 첫번째 원소는 현재 상태를 나타내고 두번째 원소는 상태를 변경해주는 역할.
  각각을 getter, setter 함수로 보면 좀 더 쉽게 이해가능.

### **자식에서 부모로 데이터를 전송하는 방법**

→ **함수**를 이용.

자식은 props를 사용해서 부모에게 데이터를 건네줄 수 없다.

따라서 부모가 함수를 넣어 props로 자식에게 넘겨주면,
자식이 데이터를 parameter로 넣어 호출하는 방식으로 동작.

즉,** 부모가 props로 함수를 넣어주면 자식이 그 함수를 이용해 값을 건네주는 방식**.

#### 참고 자료

[https://singa-korean.tistory.com/37](https://singa-korean.tistory.com/37)
[https://freestrokes.tistory.com/156](https://freestrokes.tistory.com/156)
[https://technicolour.tistory.com/56](https://technicolour.tistory.com/56)
[https://youngble.tistory.com/132?category=1242445](https://youngble.tistory.com/132?category=1242445)
[https://adjh54.tistory.com/49](https://adjh54.tistory.com/49)
[https://sihus.tistory.com/37](https://sihus.tistory.com/37)
[https://authorkim0921.tistory.com/13](https://authorkim0921.tistory.com/13)
