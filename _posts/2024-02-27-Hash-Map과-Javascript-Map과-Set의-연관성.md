---
title: Hash Map과 Javascript Map과 Set의 연관성
author: dongee_seo
date: 2024-02-27
categories: [Blogging]
tags: [google analytics, pageviews]
---

# Hash Map과 Javascript Map과 Set의 연관성

해시 맵(Hash Map)과 JavaScript의 Set 및 Map은 모두 데이터를 저장하고 관리하는 데 사용되는 자료 구조입니다. 이들 간에는 몇 가지 연관성이 있습니다.

- 해시 기반의 자료구조:
  해시 맵, Set 및 Map은 내부적으로 해시 함수를 사용하여 요소를 저장하고 검색. 이를 통해 요소에 대한 빠른 검색과 접근이 가능.

- 고유한 키와 값의 쌍 저장:

  - Map: 키-값(key-value) 쌍을 저장하고 관리하는 자료구조
  - Set: 고유한 값만을 저장하며, 값은 키와 동일
    - 해시 맵: 키와 값의 쌍을 저장하지만, 키는 고유해야 하지만 값은 고유할 필요가 없음.

- 빠른 검색 및 삽입:
  해시 기반의 자료구조는 해시 함수를 사용하여 요소를 저장하고 검색하기 때문에 매우 빠른 검색 및 삽입 속도를 제공
  => 대량의 데이터를 다루거나 검색이 빈번한 상황에서 유용

- 반복 가능한(iterable) 자료구조:
  JavaScript의 Set 및 Map은 반복 가능한(iterable) 자료구조 - 이는 for...of 루프나 forEach 메서드 등을 사용하여 요소를 반복하고 처리할 수 있음을 의미

- 효율적인 메모리 관리:
  해시 맵, Set, Map은 각 요소에 대해 고유한 해시 값을 사용하여 내부 저장 공간을 효율적으로 관리
  => 중복 요소를 제거하거나 특정 요소에 빠르게 접근할 수 있도록 해줌.

# Set

## 요소순회

Set 객체는 이터러블이다. 따라서 for…of문으로 순회 가능, 스프레드 문법과 배열 디스트럭처링의 대상 가능.

```jsx
const set = new Set([1, 2, 3]);

// Set.prototype 의 Symbol.interator 메서드를 상속받는 이터러블
console.log(Symbol.iterator in set); // true

// for…of문으로 순회 가능
for (const value of set) {
  console.log(value); // 1 2 3
}

// 스프레드 문법의 대상
console.log([...set]); // [1,2,3]

// 배열 디스트럭처링 할당의 대상
const [a, ...rest] = set;
console.log(a, rest); // 1 , [2,3]
---

## 집합 연산

Set객체는 수학적 집합을 구현하기 위한 자료구조
=> 교집합, 합집합, 차집합 등 구현 가능

### 교집합:intersection

```jsx
// 사용자가 직접 intersection 메서드를 정의 후 함수 할당.
Set.prototype.intersection = function (set) {
  const result = new Set();

  for (const value of set) {
    // set의 공통요소가되는 요소이면 교집합의 대상
    // this: 현재객체; setA
    // set: 비교대상; setB
    if (this.has(value)) result.add(value);
  }

  return result;
};

const setA = new Set([1, 2, 3]);
const setB = new Set([1, 2]);

// setA와 setB의 교집합
console.log("교집합", setA.intersection(setB));
```

방안2

```jsx
Set.prototype.intersection = function (set) {
  return new Set([...this].filter((v) => set.has(v)));
};

const setA = new Set([1, 2, 3]);
const setB = new Set([1, 2]);

// setA와 setB의 교집합
console.log("교집합", setA.intersection(setB));
```

### 합집합:union

A와 B의 중복없는 모든요소로 구성

```jsx
Set.prototype.union = function (set) {
  const result = new Set(this);

  for (const value of set) {
    // 2개의 Set객체 모든요소 포함. 단 중복 요소 미포함
    result.add(value);
  }

  return result;
};

const setA = new Set([1, 2, 3]);
const setB = new Set([1, 2, 4]);

// setA와 setB의 합집합
console.log("합집합", setA.union(setB)); // [1,2,3,4]
---

```jsx
Set.prototype.union = function (set) {
  return new Set([...this, ...set]);
};

const setA = new Set([1, 2, 3]);
const setB = new Set([1, 2, 4]);

// setA와 setB의 합집합
console.log("합집합", setA.union(setB));
```

### 차집합

A-B : A집합에는 존재하지만 B집합에는 존재하지 않음.

```jsx
Set.prototype.difference = function (set) {
  // this(Set 객체)를 복사(얕은 복사(shallow copy))
  const result = new Set(this);

  for (const value of set) {
    result.delete(value);
  }

  return result;
};

const setA = new Set([1, 2, 3]);
const setB = new Set([1, 2, 4]);

// setA와 setB의 차집합
console.log("차집합", setA.difference(setB)); // [3]
---

```jsx
Set.prototype.difference = function (set) {
  // this(Set 객체)를 복사(얕은 복사(shallow copy))
  // this를 직접 수정하면 원래의 Set 객체가 변경될 수 있습니다.
  // 하지만 교집합이나 차집합을 계산할 때 원래의 Set 객체를 변경하지 않고 새로운 Set 객체를 반환
  return new Set([...this].filter((v) => !set.has(v)));
};

const setA = new Set([1, 2, 3]);
const setB = new Set([1, 2, 4]);

// setA와 setB의 차집합
console.log("차집합", setA.difference(setB));
```

**얕은 복사(shallow copy)**

- Set 객체의 각 요소에 대한 참조만을 복사하여 새로운 배열을 생성
- 요소가 객체나 배열 등의 참조형 자료일 경우,
  배열에는 해당 요소들에 대한 참조가 복사되며,
  원본 Set 객체와 복사된 배열은 같은 요소를 참조
- 동일한 객체나 배열을 가리키게 되므로
  두 객체나 배열의 변경사항이 서로에게 영향을 미칩니다

=> 따라서 요소가 객체나 배열 등의 참조형 자료일 경우에는 깊은 복사를 수행해야 함

**깊은 복사(deep copy)**

- 객체의 모든 요소를 재귀적으로 복사하여 새로운 객체를 생성
- 원본 객체와는 별개의 새로운 객체를 생성
- 변경사항이 서로에게 영향을 미치지 않습니다.

### 부분집합과 상위 집합

A가 B에 포함되는 경우
A는 B의 부분집합(subset)이며, B는 A의 상위 집합(superset)이다.

```jsx
Set.prototype.isSuperset = function (subset) {
  for (const value of subset) {
    if (!this.has(value)) return false;
  }
  return true;
};

const setA = new Set([1, 2, 3]);
const setB = new Set([1]);

// setA가 setB의 상위 집합인지 확인
console.log("상위집합", setA.isSuperset(setB));
```

```jsx
Set.prototype.isSuperset = function(subset){
  const supersetArr = [...this]

  // every 메서드를 사용하여 subset의 모든 요소를 순회
  // 각 요소가 supersetArr에 포함되는지를 검사
  // 모든 요소가 포함되어 있다면 true 아니면 false

  return [...subset].every(v => supersetArr.includes(v))
}

const setA = new Set([1,2,3])
const setB = new Set([1])

// setA가 setB의 상위 집합인지 확인
console.log('상위집합', setA.isSuperset(setB))






[...subset]은 전개 연산자를 사용하여
subset의 모든 요소를 새로운 배열로 만드는 것을 의미
=> subset의 모든 요소가 배열의 각 요소로 복사되어 들어가게 됩니다.
=> [1]
반면에 [subset]은 배열 리터럴 표기법을 사용하여 배열을 생성하는 것을 의미
=> 하지만 여기서 subset이 Set 객체이므로
배열 리터럴 표기법을 사용하더라도 실제로 배열이 만들어지지 않습니다.
=> 대신에, 이렇게 하면
subset이라는 단일 요소를 가진 배열이 생성됨.
=> [ [1] ]


따라서 [...subset]은 subset의 모든 요소를 복사하여 새로운 배열을 만들지만,
[subset]은 subset 자체를 배열의 첫 번째 요소로 가지는 배열을 만듭니다.
```

# Map

Map 객체는 key-value 쌍으로 이루어진 컬렉션

- key: 객체를 포함한 모든 값
- 이터러블
- 요소갯수 확인: map.size

## Map 객체의 생성

- Map생성자 함수
  - 이터러블을 인수로 전달받아 Map객체를 생성.
    - 인수로 전달되는 이터러블은 key-value의 쌍으로 이루어진 요소로 구성되어야 함.
    - 중복된 키를 갖는 요소가 존재할 경우 갚이 덮어씌워짐
      => 중복된 키를 갖는 요소 존재 불가.

```jsx
const map = new Map([
  ["key1", "value1"],
  ["key2", "value2"]
]);

const map = new Map([
  ["key1", "value1"],
  ["key1", "value2"]
]);
console.log(map); // {key1 => value2}
```

## for...in 문

for...in 문은 객체의 열거 가능한 속성들을 반복하기 위해 사용됩니다. 그러나 배열에 대해서는 for...in을 사용하는 것이 권장되지 않는데, 이는 몇 가지 이유로 인해 그렇습니다:

인덱스 순서 보장 문제: for...in은 객체의 속성을 반복할 때 특정한 순서를 보장하지 않습니다. 이는 배열의 인덱스 순서를 보장하지 않아 예상치 못한 결과를 초래할 수 있습니다.

상속된 속성 문제: 배열 객체에는 상속된 속성이 존재할 수 있습니다. 예를 들어, 배열의 프로토타입인 Array.prototype에도 메서드와 속성이 존재합니다. for...in은 이러한 상속된 속성들도 열거하기 때문에 원치 않는 동작을 초래할 수 있습니다.

배열 요소 외의 속성 문제: for...in은 배열 요소 뿐만 아니라 배열 객체에 추가된 사용자 지정 속성도 열거합니다. 이는 배열 요소가 아닌 속성도 반복하게 되어 의도치 않은 동작을 초래할 수 있습니다.

배열 내장 메서드 사용 권장: 배열을 반복할 때는 for...in 대신 forEach, for...of, map 등의 내장 반복 메서드나 루프 구문을 사용하는 것이 좋습니다. 이러한 메서드들은 배열 요소를 효과적으로 반복하면서 위의 문제들을 피할 수 있습니다.

따라서, 배열을 반복할 때는 for...in 대신에 for...of나 배열의 내장 반복 메서드를 사용하는 것이 좋습니다.

## 배열(Array)과 Map객체 비교

#### 배열 (Array): 순차적인 데이터를 관리

- 순서가 있는 값의 집합
- 각 요소는 인덱스를 통해 접근가능
- 동일한 타입이 아닌 다양한 데이터 타입의 요소를 포함가능.
- 배열의 크기는 동적으로 조절 => 요소를 추가/삭제 가능.
- 반복문을 사용하여 요소에 접근/수정.
- 사용 목적: 순차적인 데이터를 저장하고 관리
  - 리스트나 스택, 큐 등을 구현
  #### 배열의 요소를 정렬하고 조건을 만족하는 요소가 있는지 확인
  - sort() 메서드: 배열의 요소를 정렬. 이때 원본 배열이 변경되며, 정렬된 배열이 반환.
  - some() 메서드: 배열의 각 요소에 대해 주어진 함수를 실행하고, 콜백 함수가 하나라도 true를 반환하면 some() 메서드는 즉시 true를 반환하고 반복을 중지.

#### Map: 키-값 쌍을 저장하고 검색

- 키-값(key-value) 쌍을 저장하는 자료구조
- 각 키는 유일해야 합니다. 키에 해당하는 값에 접근하기 위해 사용.
- 키와 값의 쌍을 연결하여 저장. 순서가 보장되지 않음.
- 다양한 데이터 타입의 키와 값 모두 저장 가능
- Map 객체의 크기는 size 속성을 통해 확인.
- 요소를 추가, 삭제, 수정할 수 있습니다.
- 사용 목적: 특정 키와 연관된 값을 저장하고 검색
- 객체와 유사하지만 객체보다 다양한 데이터 타입의 키를 사용할 수 있고 순서가 보장되는 등의 장점

### 프로그래머스: [전화번호 목록](https://school.programmers.co.kr/learn/courses/30/lessons/42577)

#### 배열 메서드

```jsx
function solution(phoneBook) {

  // !phoneBook.sort(): 항상 true를 반환하게 되어 some() 함수의 콜백 함수가 항상 실행
    return !phoneBook.sort().some((t,i)=> {
      // 배열의 마지막 요소인지를 확인
      // 만약 마지막 요소라면 중복이 없다는 것을 나타내기 위해 false를 반환.

이 구문은 반복문이 마지막 요소까지 도달했을 때, 다음 요소가 없기 때문에 중복이 발생하지 않음을 나타내기 위한 것
        if(i === phoneBook.length -1) return false;
	   // 이웃하는 두 번호가 동일한 접두사를 가지는지 확인
       // 동일한 접두사를 가진다면, some() 함수는 true를 반환
       // 이는 전화번호부에 중복된 접두사를 가진 번호가 있다는 것을 의미
        return phoneBook[i+1].startsWith(phoneBook[i]);
    })
}

```

#### 일반 객체를 사용하여 해시맵을 구현

```jsx
function solution(phone_book) {
  var answer = true;
  const hashMap = {};

  // hashMap의 key를 전화번호로 저장.
  phone_book.forEach((num) => {
    hashMap[num] = true;
  });

  for (const number of phone_book) {
    if (!answer) break;

    let prefix = "";

    // 현재 검사 중인 전화번호(number)의 각 자릿수(digit)에 대해 반복
    for (const digit of number) {
      // 1. 접두사 생성.
      // 현재까지의 접두사에 현재 자릿수를 더한다.
      // 이렇게 하면 접두사가 하나씩 늘어난다.
      // 접두사의 길이에 따라서 점차적으로 전체 전화번호의 자릿수를 확인가능
      prefix += digit;

      // 2. 현재 전화번호가 다른 전화번호의 접두사인지를 확인

      // hashMap[prefix]
      // 현재까지 만들어진 접두사가 해시맵에 존재하는지 확인
      // 만약 존재한다면, 해당 접두사가 이미 다른 전화번호의 접두사임을 의미

      // prefix !== number
      // 현재까지 만들어진 접두사가 현재 검사 중인 전화번호(number)와 같지 않은지 확인
      // 만약 같다면, 이는 자기 자신의 전화번호를 검사하는 것이므로 접두사가 아님.
      if (hashMap[prefix] && prefix !== number) {
        answer = false;
        break;
      }
    }
  }
  return answer;
}
```
