---
title: App 카메라 최적화
author: dongee_seo
date: 2024-02-03
categories: [React Native]
tags: [react-native-vision-camera]
---

## 얼굴 인식 성능 최적화: App 카메라 최적화 사례

### 프로젝트 개요

 `react-native-vision-camera` 라이브러리를 활용하여 얼굴 인식을 구현하였다. 하지만 전체 화면에서 얼굴 인식을 수행할 때 성능 저하가 발생하여, 이를 해결하기 위한 최적화 작업을 진행하였다.

### 문제점

얼굴 인식을 전체 화면에서 진행할 경우 발생한 문제:

- **연산 부하**: 많은 양의 이미지 데이터를 처리해야 하며, 이로 인해 메모리 사용량이 증가.
- **속도 저하**: 얼굴 인식 속도가 느려지고, 전체 앱 성능이 저하됨.

### 해결 방법

이 문제를 해결하기 위해 다음과 같은 방법을 적용했다:

### 1. 영역 제한

**문제**: 전체 화면에서 얼굴 인식을 수행할 경우 데이터 처리량이 많아 성능이 저하됨.

**해결 방법**: 얼굴 인식을 전체 화면이 아닌 특정 영역에만 수행하도록 최적화. 이 접근 방식으로 데이터 처리량을 줄였다.

**구현 코드**:

1. **카메라 프리뷰에서 ROI 설정**:
    
    ```tsx
    
    import { Camera, useCameraDevices } from 'react-native-vision-camera';
    
    const App = () => {
      const devices = useCameraDevices();
      const device = devices.front;
    
      return (
        device != null && (
          <Camera
            device={device}
            isActive={true}
            style={{ flex: 1, }}
            frameProcessor={frame => {
              // 설정한 영역을 기준으로 얼굴 인식을 수행
              const roi = { x: 100, y: 100, width: 200, height: 200 };
              const croppedFrame = cropFrame(frame, roi);
              detectFace(croppedFrame);
            }}
            frameProcessorFps={5} // 처리 주기를 설정
          />
        )
      );
    };
    
    const cropFrame = (frame, roi) => {
      // ROI에 맞게 이미지를 자르는 함수
      // 하단 코드 참고
    };
    
    const detectFace = (frame) => {
      // 얼굴 인식을 수행하는 함수
      // 하단 코드 참고
    };
    
    ```
 인식할 영역만을 정의하고 해당 영역의 데이터만 처리했다.
    

### 2. 빈도 조절 및 영역 내 인식

**문제**: 얼굴 인식의 빈도가 높아 불필요한 연산이 발생했다.

**해결 방법**: 얼굴 인식 빈도를 조절하고, 얼굴이 지정된 영역 내에 있을 때만 인식을 수행하도록 개선했다.

**구현 코드**:

1. **빈도 조절**:
    
    ```tsx
    
    import { useRef } from 'react';
    import { Camera } from 'react-native-vision-camera';
    
    const App = () => {
      const lastDetectionTime = useRef(Date.now());
    
      return (
        <Camera
          // 카메라 설정
          frameProcessor={frame => {
            const now = Date.now();
            if (now - lastDetectionTime.current > 500) { // 500ms마다 인식
              lastDetectionTime.current = now;
              const roi = { x: 100, y: 100, width: 200, height: 200 };
              const croppedFrame = cropFrame(frame, roi);
              detectFace(croppedFrame);
            }
          }}
        />
      );
    };
    
    ```
    
2. **영역 내 인식**:
    
    ```tsx
    typescriptCopy code
    const detectFace = (frame) => {
      // 얼굴 인식 로직
      const faces = detectFacesInFrame(frame);
      faces.forEach(face => {
        if (isFaceInROI(face, { x: 100, y: 100, width: 200, height: 200 })) {
          // ROI 내의 얼굴만 처리한다.
        }
      });
    };
    
    const isFaceInROI = (face, roi) => {
      // 얼굴이 ROI 내에 있는지 확인
    };
    
    ```
    

### 1. `detectFace` 함수

이 함수는 이미지 프레임에서 얼굴을 인식하고, 인식된 얼굴이 ROI(관심 영역) 내에 있는지 확인하는 역할을 합니다. 아래는 `detectFace` 함수의 자세한 구현 예시입니다:

```tsx

const detectFace = (frame: ImageFrame) => {
  // 얼굴 인식 로직
  // `detectFacesInFrame` 함수는 프레임에서 얼굴을 탐지하여 얼굴 정보 배열을 반환.
  const faces = detectFacesInFrame(frame);

  // ROI 설정 (x, y, width, height)
  const roi = { x: 100, y: 100, width: 200, height: 200 };

  faces.forEach(face => {
    // `isFaceInROI` 함수는 얼굴이 설정한 ROI 내에 있는지 확인
    if (isFaceInROI(face, roi)) {
      // ROI 내의 얼굴만 처리
      // 여기에서 얼굴 인식 후의 추가 작업을 수행할 수 있다.
       console.log("Detected face in ROI:", face);
    }
  });
};

```

- **`detectFacesInFrame(frame)`**: 프레임에서 얼굴을 탐지하여 얼굴 정보가 담긴 배열을 반환하는 함수.  얼굴 인식 라이브러리의 API를 호출하여 구현.
- **`roi`**: 관심 영역을 설정하는 객체입니다. 이 영역 내에서만 얼굴 인식을 수행.
- **`isFaceInROI(face, roi)`**: 각 얼굴이 설정한 ROI 내에 있는지 확인.

### 2. `isFaceInROI` 함수

이 함수는 얼굴이 주어진 ROI 내에 있는지 확인합니다. 다음은 `isFaceInROI` 함수의 자세한 구현 예시입니다:

```tsx

interface Face {
  x: number; // 얼굴의 x 좌표
  y: number; // 얼굴의 y 좌표
  width: number; // 얼굴의 너비
  height: number; // 얼굴의 높이
}

interface ROI {
  x: number; // ROI의 x 좌표
  y: number; // ROI의 y 좌표
  width: number; // ROI의 너비
  height: number; // ROI의 높이
}

const isFaceInROI = (face: Face, roi: ROI): boolean => {
  // 얼굴의 경계
  const faceLeft = face.x;
  const faceRight = face.x + face.width;
  const faceTop = face.y;
  const faceBottom = face.y + face.height;

  // ROI의 경계
  const roiLeft = roi.x;
  const roiRight = roi.x + roi.width;
  const roiTop = roi.y;
  const roiBottom = roi.y + roi.height;

  // 얼굴이 ROI 내에 있는지 확인
  return !(faceRight < roiLeft ||
           faceLeft > roiRight ||
           faceBottom < roiTop ||
           faceTop > roiBottom);
};

```

- **`Face` 인터페이스**: 얼굴의 위치와 크기를 정의다. 이 값들은 얼굴 인식 라이브러리에서 제공하는 데이터에 따라 달라질 수 있음.
- **`ROI` 인터페이스**: 관심 영역의 위치와 크기를 정의.
- **`isFaceInROI` 함수**: 얼굴이 ROI 내에 포함되어 있는지 검사한다. ROI와 얼굴의 경계를 비교하여 얼굴이 ROI의 경계 안에 있는지를 확인.

### 성과

- **속도 개선**: 얼굴 인식 속도가 15fps에서 20fps로 개선되었다.
- **성능 향상**: 전체 앱의 성능이 향상되어, 사용자 경험이 개선되었다.

### 결론

이번 최적화 작업을 통해 성능을 크게 향상시킬 수 있었습니다. ROI 설정, 빈도 조절, 영역 내 인식과 같은 최적화 방법을 통해 데이터 처리의 효율성을 높이고, 사용자 경험을 개선했다. 
