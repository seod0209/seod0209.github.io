```
title: Android Studio Keystore 생성하기
author: dongee_seo
date: 2023-10-11
categories: [Blogging]
tags: [google analytics, pageviews]
```

**Command로 Keystore 생성하기**

# keytool은 jdk 설치 폴더의 bin에 위치해 있기 때문에 Java를 환경변수설정으로 지정해주었다면 위치와 상관없이 command창에서 실행이 가능하지만, 환경변수설정을 지정 하지 않았다면 keytool의 경로로 가서 아래의 커맨드를 입력하도록 한다.

1. Go terminal at the project root directory

```
cd android/app
keytool -genkey -v -keystore release.keystore -alias upload -keyalg RSA -keysize 2048 -validity 10000
```

```perl
Enter keystore password: Entre123!
Re-enter new password: Entre123!
What is your first and last name: your name
  [Unknown]: your name
What is the name of your organizational unit?
  [Unknown]: zippu
What is the name of your organization?
  [Unknown]: zippu
What is the name of your City or Locality?
  [Unknown]:  SEOUL
What is the name of your State or Province?
  [Unknown]:  SEOUL
What is the two-letter country code for this unit?
  [Unknown]:  KR
Is CN=your name, OU=entre-reality, O=twinit, L=SEOUL, ST=SEOUL, C=KR?
  [no]: yes
```

1. Then replace the following field in the `gradle.properties`

```
cd..
```

to the `android` folder, then run

```
./gradlew signingReport
```

1. After that find the corresponding key inside that,

   copy the SHA-1 of the key and add into the [Firebase](https://console.firebase.google.com/u/1/project/twinit-dev/settings/general/android:com.twinit).

**Android Studio에서 keystore 생성하기 (.jks : Java Key Store)**

1. Build - Genderate Signed APK
2. Click Abb and Next
3. click Create New and then write
   - password는 6자리 이상 입력.
   - 키저장소 password와 키 password는 다른것이다.
     (같은 비밀번호를 입력해도 되고 다르게 입력해도 상관없이 진행된다.)
   - 생성후 **Key store password, Key password 를** 입력하는 부분에 입력.
   - 입력할 내용은 상단에 command로 진행할 때 기입 하였던 정보들과 동일하다.
