---
title: ssh로 git clone 하기
author: dongee_seo
date: 2024-02-24
categories: [Blogging]
tags: [google analytics, pageviews]
---

# SSH

SSH 란 Secure Shell 의 줄임말로, 두 컴퓨터 간 통신을 할 수 있게 해주는 하나의 protocol

> Protocol 이란, 서로 다른 통신 장비 간 주고 받는 데이터의 양식과 규칙입니다.

인터넷 연결만 되어있어도 내 컴퓨터의 terminal 을 통해 다른 지역에 있는 컴퓨터 혹은 서버를 관리할 수 있게 해주고, 파일도 공유 가능

ex) HTTP, HTTPS, FTP 등

브라우저가 웹페이지를 보여주기 위해 서버와 통신할 때 HTTPS protocol을 사용하는 것과 같이,
서로 다른 컴퓨터들이 shell 을 통해 통신하기 위한 protocol 이 필요했고, 지금 가장 많이 사용되는 것이 **SSH**

# **SSH 의 장점: 암호화된 통신**

HTTPS 에서 통신 간 데이터가 암호화 되어 있는 것과 같이,
SSH 를 이용한 통신에서는 Client 와 Host 의 통신이 암호화 되어 있다.

> **Client**: Host 에 접속하려고 하는 컴퓨터
>
> **Host**: 접속 대상 (ex. remote 서버)

모든 데이터가 암호화 되어 전송 ⇒ 굉장히 안전

# **SSH 의 Encryption/Decryption 과정**

SSH 통신에서 데이터가 암호화되는 과정: 3 steps

- 대칭 암호화 (Symmetric Encryption)
- 비대칭 암호화 (Asymmetric Encryption)
- 해쉬함수 (Hashing)

## **대칭 암호화 (Symmetric Encryption)**

대칭 암호화란 1개의 공통된 Secret Key 를 가지고 양쪽에서 데이터를 암호화 및 복호화 할 수 있게 하는 방법

![](https://miro.medium.com/v2/resize:fit:700/1*MthiysU9VfG1lHr-_cjjfg.png)

- 서로 같은 Secret Key 만 있으면 데이터를 암호화/복호화 가능
- Secret Key 가 유출 되었을 경우
  암호화된 모든 통신이 노출된다는 치명적인 단점이 존재

⇒ 안전하게 Key 를 exchange 하는 방법으로
비대칭 암호화 (Asymmetric Encryption) 알고리즘이 존재

## **비대칭 암호화 (Asymmetric Encryption)**

- 송신자, 수신자 각각 Public Key 와 Private Key 를 가짐.
- 송신자의 Public Key 로 암호화 된 데이터는
  송신자의 Private Key 를 사용해야만 복호화가 가능
  ⇒ 서로의 Public Key 를 교환하여 암호화하는데 사용

1. 나는 상대방에서 나의 Public Key 를 보내주고, 나는 상대방의 Public Key 를 받는다.
2. 내가 보내고 싶은 데이터를 내가 가진 상대방의 Public Key 로 암호화 한 뒤 전송
3. 상대방이 내가 전송한 암호화된 데이터를 받아
   본인의 Private Key 로 복호화

![](https://miro.medium.com/v2/resize:fit:700/1*U8TaFfN6bLtR79k3t52gwA.png)

- 비대칭 암호화는 송/수신자 간 대칭 암호화에서 필요했던 공통의 Secret Key 를 생성하는 과정에서 사용
- 서로가 서로의 Public Key 를 공유할 때는 해커가 해당 데이터를 가로챌 위험성

⇒ 알고리즘이 **디피-헬먼 키 교환 알고리즘 (Diffie-Hellman Key Exchange Algorithm)**
\*\* 암호화 알고리즘이 아니며, 서로 간 안전하게 키를 공유할 수 있게 해주는 알고리즘

## **해쉬 함수 (Hashing)**

- 대칭 암호화, 비대칭 암호화, 디피-헬먼 키 교환 알고리즘
  ⇒ SSH 에서 송/수신자 간 안전하게 암호화 된 데이터를 주고 받음.
- 하지만, SSH 커넥션이 성공적으로 생기기 전
  이미 누군가 (해커) 송/수신자 (Client 혹은 Host) 를 위장하여 잠입해,
  모든 정보를 조작할 가능성.
  ⇒ 이런 경우 송/수신자는 아무것도 모른채 악의적으로 변화된 데이터를 지속적으로 받아보게 될 수도 있음.

⇒ 이를 방지하기 위해 SSH 에서는 
**MAC (Message Authentication Code)**을 통한 데이터 무결성을 (송신자가 보낸 메세지가 변조되지 않았는지) 확인하는 절차가 존재

- Hash 함수가
  - 전송되는 메세지
  - 송/수신자가 공유하는 Secret Key
  - Packet Sequence Number
    위 정보를 가지고 MAC 값을 출력 → 수신자 (Host) 에게 보냄.
- 수신자도 같은 정보를 가지고 있기때문에,
  같은 정보를 가지고 똑같은 Hash 함수를 돌려 나온 MAC 값이 일치하는지 확인
- 해시 함수는 항상 일정한 크기의 출력을 생성
  ⇒ 입력의 길이가 어떻든지 상관없이 항상 일정한 크기의 해시값을 생성한다는 것을 의미

> Hashing 은 기본적으로 단방향으로 이루어집니다.
> 단방향으로 이루어지는 이유?
> 복호화를 염두해두고 사용하는 암호화 과정이 아니기 때문
> ( 입력으로부터 해시값을 계산할 수 있지만, 해시값으로부터 입력을 복구할 수는 없다. 이는 해시 함수가 데이터의 보안을 강화하는 데 도움)

# **Authentication**

이렇게 해서 송/수신자 간 안전한 connection 이 열리게 되면,
이제 접속을 시도하는 user 가 접속 권한이 있는 사람인지 확인하는 절차가 필요

만약 이런 절차가 없다면 누구나 언제든 서버에 접속할 수 있기 때문

### SSH 에서 User 를 인증하는 방법

- Password (username/password — username 은 보통 root)
- RSA (password 없이 identity 확인)

## **Password**

- 비밀번호를 입력하는 방법
- 이미 여러가지 절차를 통해 secure connection 이 열린 상태이기 때문에 password 를 입력해도 크게 문제 될 건 없겠지만 권장되는 방법은 아님.
  왜냐하면 이 방법은 Brute-force 공격에 취약하다는 단점

> Brute-force Attack: 키 전수조사 또는 무차별 대입 공격을 통해 조합 가능한 모든 문자열을 하나씩 대입해 보는 방식으로 암호를 해독하는 방법

⇒ 비밀번호 입력없이 나의 identity 가 확인되는 방법 필요.

## **[RSA](https://gngsn.tistory.com/96)**

- 내 컴퓨터에 SSH 키를 생성 → 나의 Public Key 를 host 의 인가 목록에 추가 → 자동으로 나를 인증하는 방법
- 해당 Public Key 와 매칭되는 Private Key 가 존재하는 나의 컴퓨터를 사용하는 한 비밀번호 없이 인증이 가능

```
RSA 알고리즘은 소인수분해 문제가 어렵다는 사실에 기반한 알고리즘
```

# **SSH Key 생성 방법 (깃헙 계정 연동 목적)**

**Step 1**: SSH Key 존재유무 확인

```jsx
ls -al ~/.ssh

// id_rsa.pub 이라는 파일이 존재하면 SSH Key 가 이미 있다는 뜻
// 추가로 생성할 필요가 없음
```

**Step 2:** SSH Key 생성

```
ssh-keygen -t rsa -b 4096 -C "GitHub이메일주소"
```

```
> Generating public/private rsa key pair.

> Enter a file in which to save the key (/Users/*you*/.ssh/id_rsa):

> Enter passphrase (empty for no passphrase):

> Enter same passphrase again:
```

> **_passphrase?_**
>
> _RSA 방식의 단점인 누군가 악의적으로 내 컴퓨터를 컨트롤 할 수 있게 된다면, 내 컴퓨터에 있는 SSH Key 를 가진 모든 시스템에 접근 권한이 생기기 때문에 SSH Key 에 추가적으로 비밀번호를 추가하는 보안 레이어_

**Step 3**: GitHub 계정에 SSH Key 추가

SSH Key 복사 (id_rsa.pub 파일 내용 복사 — Public Key)

```
pbcopy < ~/.ssh/id_rsa.pub
```

우측 상단 프로필 사진 버튼 > **Settings**

![](https://velog.velcdn.com/images/seod0209/post/aa9a48b5-b619-43d8-a000-a29b647044a2/image.png)

![](https://velog.velcdn.com/images/seod0209/post/0b954b47-101e-432b-93d1-65f3ce186519/image.png)

![](https://velog.velcdn.com/images/seod0209/post/ece3bfd0-e85d-40d0-be67-4e69577e0be6/image.png)

**Step 4**: 제대로 연결이 되었는지 확인

아래 커맨드를 통해 새로 추가한 SSH 커넥션이 제대로 연결되었는지 확인

```
ssh -T git@github.com
```

![](https://velog.velcdn.com/images/seod0209/post/f15cd460-ea21-47f8-b78a-cce60d8a9940/image.png)

이제 GitHub 에서 repository 를 clone 받거나, 다른 액션을 수행할 때 HTTPS 가 아닌 SSH 방식으로 clone 이 가능!
