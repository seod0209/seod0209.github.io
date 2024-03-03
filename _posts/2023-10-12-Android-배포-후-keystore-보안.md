```
title: Android 배포 후 keystore 보안
author: dongee_seo
date: 2023-10-12
categories: [Blogging]
tags: [google analytics, pageviews]
```

# **배경상황**

안드로이드 개발 후 Play Store 에 배포를 하기 위해서는 **키스토어(Key Store)를 이용하여 Signing된** apk 또는 aab(Android App Bundle)이 필요합니다.

디버그 및 릴리즈 빌드할 때 keystore 파일을 잘 관리/사용했어야 하지만 개인 폴더에 스토어 키를 관리한 결과..키를 잃어버리게 되었고…

따라서 관련 파일은 이제 **_프로젝트> android> app_** 내에 저장하여 관리하려 한다.

## **Keystore 정보관리 : gradle.properties**

앱을 release용 aab(android app bundle)로 처음 빌드하려면 **keystore를 생성**하는 작업을 해야 합니다. 그 과정에서

1. key store path
2. key store passward
3. key alias
4. key passward

네 가지가 생성되는데 passward 같은 경우 분실 시 Play Store 에 업데이트가 불가하게 되는 등

잃어버리거나 유출당하면 절대 안되는 중요한 정보입니다.

해당 정보들은 하드코딩으로 기입하지 않고 gradle.properties에 기입하여 keystore 정보를 필요한 곳에 가져다 사용합니다.

### properties 파일이란?

> Java 관련 기술을 사용하는 파일들을 위한 파일확장.
>
> 응용프래그램을 구성가능한 파라미터들을 저장하는데 사용.
>
> 각 줄에 하나의 파라미터를 저장. key = value 형식으로 저장 됨.
>
> 문자열의 일부로 저장되기 때문에 쿼테이션없이 작성.

## **플레이스토어에 배포할 때는 어떻게 할까요?**

1. release용 keystore를 생성 ()
2. Android studio에서 생성한 release용 keystore → release.keystore 를 project/app/keystore 디렉토리로 복사.

   (해당 폴더 내에서 command실행으로 생성했을 경우? 디렉토리에 복사하는 행위 생략)

3. app/build.gradle에 코드 작성.

```
android {
     signingConfigs {
        debug {
            storeFile file('debug.keystore')
            storePassword 'android'
            keyAlias 'androiddebugkey'
            keyPassword 'android'
        }
        release {
            if (project.hasProperty('PROD_UPLOAD_STORE_FILE')) {
                storeFile file(PROD_UPLOAD_STORE_FILE)
                storePassword PROD_UPLOAD_STORE_PASSWORD
                keyAlias PROD_UPLOAD_KEY_ALIAS
                keyPassword PROD_UPLOAD_KEY_PASSWORD
            }
        }
    }
    buildTypes {
        debug {
            signingConfig signingConfigs.debug
        }
        release {
            // Caution! In production, you need to generate your own keystore file.
            // see https://reactnative.dev/docs/signed-apk-android.
            signingConfig signingConfigs.release
            minifyEnabled enableProguardInReleaseBuilds
            proguardFiles getDefaultProguardFile("proguard-android.txt"), "proguard-rules.pro"
        }
    }
}
```

이렇게 하면 debug와 release를 서로 다른 keystore를 이용해서 빌드를 할 수 있습니다.

## **Signed abb 추출하기**

Signed abb를 추출 후 Play Store 에 업로드하기 위해서는 아래의 단계를 수행합니다.

1. Build → Generate Signed APK 선택

2. Android App Bundle 클릭 > Next

3. release.keystore를 적용한 후> Next

4. release 선택 후> create

5. Google Play Store > Production > App Bundle에 해당 abb를 업로드.
   ![](https://velog.velcdn.com/images/seod0209/post/4dc9b92a-0acd-4797-b96f-612afd2e1c67/image.png)

## **Play Store에 배포할 때는 서명키가 다를 경우 어떻게 할까요?**

위 과정을 거친 후 abb 파일을 올렸을 때 다음과 같은 에러가 발생했다면??
![](https://velog.velcdn.com/images/seod0209/post/13780bde-c94a-408c-b5bc-3b4d7e39ad7e/image.png)

**계정 소유주가**

1. 플레이콘솔> 콘설> 해당앱 > 출시설정 > 앱무결성> 앱 서명 페이지에서 PEM 파일 생성.

`keytool -export -rfc -keystore release.keystore -alias upload -file upload_certificate.pem`

1. ‘업로드 키 재설정’ 요청 섹션에서 새 업로드 인증서 요청.
2. 재설정된 인증서로 App Bunddle을 업로드.
