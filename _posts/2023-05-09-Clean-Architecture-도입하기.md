---
title: 'Clean Architecture: Practice'
author: dongee_seo 
date: 2023-05-09 
categories: [Blogging] 
tags: [Architecture]
---

# Clean Architecture

## 도입 배경

초창기 "회사 관리자 웹서비스"는 `MVVM`패턴을 사용해서 개발을 진행했습니다.
처음 MVVM 패턴을 도입하면서 Activity or Fragment에서 처리되었던 UI + 비즈니스 로직들이
UI(Activity or Fragment) 와 ViewModel(비즈니스 로직) 으로 분리되었습니다.
그 결과 역할 분담이 되어 Activity or Fragemnt의 역할이 많이 줄었습니다.

그 대신 복잡한 비즈니스 로직이 들어가게 되는 경우 ViewModel의 코드가 길어지는 현상이 발생했습니다.
공통으로 사용 되는 부분들을 특정 ViewModel로 묶어서 작업을 진행 하였지만
이 방법은 중복 코드만 줄여 줄 뿐 ViewModel의 역할을 줄여주는 방법은 아니라고 생각 되었습니다.

그 해결 방법을 찾아보던 중 CleanArchitecture의 `UseCase`를 통해서 해결할 수 있다는 생각을 하게 되었습니다.

![https://blog.cleancoder.com/uncle-bob/images/2012-08-13-the-clean-architecture/CleanArchitecture.jpg](https://blog.cleancoder.com/uncle-bob/images/2012-08-13-the-clean-architecture/CleanArchitecture.jpg)

관심사에 따라 계층을 분리하고 계층간의 의존성을 단방향(바깥에서 안쪽)으로 만들어 준다는 점입니다. 간략하게 Entities , UseCases , Presenters 에 대해 설명하자면 다음과 같습니다.

- Entities: 전사적 비즈니스 규칙을 캡슐화 합니다.
- UseCases : 애플리케이션과 관련된 비즈니스 규칙을 포함하고 시스템의 모든 유즈 케이스 구현체들을 캡슐화 합니다.
- Presenters : UseCase 또는 Entities 로부터 얻은 데이터를 가공하는 계층. ViewModel 이 해당 됩니다.

목표

1. 세부 구현이 아닌 **도메인을 중심으로 설계**한다.
2. 도메인은 프레임워크나 DB, UI 등 **외부 요소에 의존하지 않도록** 한다. 그리고 이 아키텍쳐가 동작하기 위해서는 **의존성 규칙**을 지켜야 한다.
   (의존성 규칙은 모든 소스코드의 의존성은 외부에서 내부로, 즉, 고수준에서 저수준으로 향해야 한다는 규칙이다.
   업무의 로직에 해당하는 코드들이 React 같은 프레임워크에 의존해서는 안됨.)

위 목표를 반영하기 위해 프로젝트 폴더구조는 크게 3가지 계층으로 나눠서 CleanArchitecture를 적용했습니다.

- ApplicationLayer ( View, ViewModel, DataModel)
- DomainLayer( Entity, Domain, Interactor)
- DataLayer( API, Repository)

DTO를 Entity로 생각 했기 때문에 의존성 방향은 단방향으로 흘러 가지만
Domain은 독릭적인 모듈이 될 수 없다(Domain은 Data를 바라보기 때문)는 생각이 들었습니다.
그리고 DTO 와 Repository가 중심부에 있기 때문에 처음부터 어떤 통신 라이브러리를 사용할지 정해야 하기 때문에 중심이 아닌 바깥으로 가는게 맞다고 판단 되었습니다.
해당 구조를 설계하면서 가장 크게 고민했던 3가지는 다음과 같습니다.

1. 무엇을 Entity로 생각해야 하는가? 해당 부분은 Domain Layer에 있는 Model을 Entity로 생각 합니다.
2. Domain은 독립적인 Module로 알고 있는데 Data 모듈을 참조하는게 좋은 방향일까? Domain 모듈이 어떤 Denpendency도 가지지 않은 독립적인 모듈이 됩니다.
3. 의존성주입을 어떻게 할것인가? InversifyJS사용으로 생성자 주입으로 객체간의 의존관계를 설정.

# **클린 아키텍쳐 적용 후 느낀 장단점**

### CleanArchitecture 적용 후 느낀 장점

- 의존성 분리
  - 의도하지 않은 의존성을 가지고 있는 부분들을 모듈화 작업을 통해 의존성을 분리 시킬 수 있었습니다.
- ViewModel 역할 감소
  - ViewModel 에서만 담당하던 역할을 UseCase를 통해 나눌수 있습니다.
    ViewModel 생성자에서 어떤 UseCase를 사용하는지 확인 가능 하기 때문에
    어떤 기능들을 사용하는지 바로 알 수 있습니다.
- 모듈 역할 분담
  - 모듈별로 역할 분담이 잘 되어 있어서 CleanArchitecture를 이해 하고 있는 사람이라면 다른 사람이 투입 되어도 이해하기 쉽습니다.
- Nullable DTO
  - DTO 모델을 모두 Nullable Field로 사용하면서 서버측에서 실수로 Null 로 내려주더라도 신경 쓰지 않고 Model로 매핑 작업 시 NotNull 처리를 하기 때문에 안전성 또한 더 올라간 것을 느낄 수 있었습니다.
- 재사용성 증가
  - UseCase가 각 하나의 역할만 하기 때문에 다른 곳에서도 재사용하기 쉽습니다.

### CleanArchitecture 적용 후 느낀 단점

- Learning Curve
  - 아키텍쳐 관점에서 바라보는 구조적 이해가 필요했으며, 이는 높은 러닝 커브를 요구합니다.
    또한 멀티 모듈에 대한 이해도가 필요했습니다.
    그리고 명확한 Best case의 클린 아키텍쳐를 찾기 어려웠습니다.
- 파일 수량 증가
  - 생각보다 많은 클래스를 생성 해야 합니다.(특히 도메인 영역)

[](https://dealicious-inc.github.io/2022/12/13/tech-day_clean_architecture.html)[https://dealicious-inc.github.io/2022/12/13/tech-day_clean_architecture.html
](https://dealicious-inc.github.io/2022/12/13/tech-day_clean_architecture.html)[](https://github.com/falsy/react-with-clean-architecture)[https://github.com/falsy/react-with-clean-architecture
](https://github.com/falsy/react-with-clean-architecture)[](https://woong-jae.com/projects/220818-clean-architecture-refactoring)[https://woong-jae.com/projects/220818-clean-architecture-refactoring
](https://woong-jae.com/projects/220818-clean-architecture-refactoring)[](https://velog.io/@gillog/Entity-DTO-VO-%EB%B0%94%EB%A1%9C-%EC%95%8C%EA%B8%B0)[https://velog.io/@gillog/Entity-DTO-VO-바로-알기
[](https://velog.io/@server30sopt/IoC-Container)https://velog.io/@server30sopt/IoC-Container
