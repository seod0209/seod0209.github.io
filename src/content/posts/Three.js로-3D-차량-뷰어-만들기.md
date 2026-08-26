---
title: "Three.js로 3D 차량 뷰어 만들기"
date: 2026-08-07
categories: ["Three.js"]
tags: ["Three.js", "WebGL", "3D"]
---

데이터를 화면에 잘 보여주는 일에 관심이 많다. 자동차 도메인에서 일하다 보니 "차를 웹에서 3D로 돌려보게 하면 어떨까"가 자연스럽게 떠올랐고, Three.js를 붙잡고 3D 뷰어의 기초를 잡아봤다. 이 글은 Three.js Journey 예제로 잡은 기본기(Scene/Camera/Renderer/애니메이션 루프)에서 출발해, 그걸 3D 차량 뷰어로 확장하는 흐름을 정리한 것이다.

> Three.js는 WebGL 위에 얹힌 라이브러리다. WebGL을 날것으로 쓰면 셰이더·버퍼를 직접 다뤄야 하지만, Three.js는 Scene/Mesh/Camera 같은 개념으로 추상화해준다. 3D를 "장면에 물체를 놓고 카메라로 본다"는 직관으로 다룰 수 있다.

## 1. 최소 구성 — 화면에 뭔가 띄우기

Three.js로 뭔가를 그리려면 최소 세 가지가 필요하다. **Scene**(무대), **Camera**(시점), **Renderer**(그리는 도구).

```js
import * as THREE from 'three'

// Canvas
const canvas = document.querySelector('canvas.webgl')

// Scene — 물체들이 올라갈 무대
const scene = new THREE.Scene()

// Sizes
const sizes = { width: 800, height: 600 }

// Camera — 어디서 볼지 (시야각 75도)
const camera = new THREE.PerspectiveCamera(75, sizes.width / sizes.height)
camera.position.z = 3
scene.add(camera)

// Renderer — 실제로 canvas에 그린다
const renderer = new THREE.WebGLRenderer({ canvas })
renderer.setSize(sizes.width, sizes.height)
```

이 셋만 있으면 무대는 준비된 거다. 이제 무대에 물체를 올린다.

## 2. Mesh와 Group — 물체 올리기

Three.js에서 물체는 **Mesh** = 기하(Geometry) + 재질(Material)이다. 상자 하나는 `BoxGeometry` + `MeshBasicMaterial`로 만든다. 여러 물체를 한 덩어리로 다루고 싶으면 **Group**으로 묶는다. Group을 움직이면 안에 든 물체가 같이 움직인다.

```js
const group = new THREE.Group()
group.position.x = 1
group.scale.y = 2
group.rotation.y = 1
scene.add(group)

const cube1 = new THREE.Mesh(
  new THREE.BoxGeometry(1, 1, 1),
  new THREE.MeshBasicMaterial({ color: 0xff0000 })
)
group.add(cube1)

const cube2 = new THREE.Mesh(
  new THREE.BoxGeometry(1, 1, 1),
  new THREE.MeshBasicMaterial({ color: 0x00ff00 })
)
cube2.position.x = -2
group.add(cube2)
```

이 Group 개념이 나중에 차량 뷰어에서 중요해진다. 차 모델은 보통 바디·바퀴·유리 등 여러 메쉬로 이뤄지는데, 이걸 Group으로 묶으면 "차 전체"를 하나로 회전·이동시킬 수 있다.

방향 감각을 잡으려면 `AxesHelper`를 하나 띄워두면 편하다.

```js
const axesHelper = new THREE.AxesHelper(2)
scene.add(axesHelper)
```

## 3. 애니메이션 루프 — 매 프레임 다시 그리기

3D는 정지 화면이 아니다. 매 프레임 상태를 갱신하고 다시 렌더한다. `requestAnimationFrame`으로 tick 루프를 돈다.

```js
const tick = () => {
  // 매 프레임 물체 상태 갱신
  cube1.position.y += 0.01

  // 다시 그린다
  renderer.render(scene, camera)

  window.requestAnimationFrame(tick)
}
tick()
```

이게 3D의 심장이다. "상태를 바꾸고 → 렌더 → 다음 프레임 예약"의 반복. 차량 뷰어에서 자동 회전이나 사용자 드래그 회전도 결국 이 루프 안에서 회전값을 갱신하는 것이다.

💡 초반엔 크기를 `{ width: 800, height: 600 }`로 고정했지만, 실제 뷰어는 `window.innerWidth/innerHeight`로 잡고 `resize` 이벤트에서 카메라 `aspect`와 renderer 크기를 다시 맞춰줘야 반응형이 된다. `camera.updateProjectionMatrix()` 호출을 잊지 말 것.

## 4. 여기서 "차량 뷰어"로 확장하기

기본기가 잡혔으면 차량 뷰어로 가는 길은 세 가지 추가다. (여기부터는 위 예제 코드를 넘어선 확장 설계다.)

### (1) 실제 3D 모델 로드 — GLTFLoader

상자 대신 실제 차 모델(`.glb`/`.gltf`)을 불러온다. glTF는 웹 3D의 사실상 표준 포맷이다.

```js
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'

const loader = new GLTFLoader()
loader.load('/models/car.glb', (gltf) => {
  scene.add(gltf.scene) // 로드된 차 모델을 무대에 올린다
})
```

로드된 `gltf.scene` 자체가 여러 메쉬를 담은 트리다. 앞서 Group을 이해했다면 이 구조가 낯설지 않다.

### (2) 사용자가 돌려보게 — OrbitControls

뷰어의 핵심은 "사용자가 마우스로 차를 돌려본다"이다. 카메라를 직접 조작하는 대신 `OrbitControls`를 붙인다.

```js
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

const controls = new OrbitControls(camera, canvas)
controls.enableDamping = true // 관성 있는 부드러운 회전
```

그리고 tick 루프에서 매 프레임 `controls.update()`를 호출하면 드래그로 카메라가 대상을 공전한다.

### (3) 조명 — 물체가 보이게

`MeshBasicMaterial`은 조명 없이도 보이지만 밋밋하다. 실제 차 모델은 빛을 받아야 재질이 산다. `MeshStandardMaterial` 계열은 조명이 있어야 보이므로, 앰비언트 + 방향광을 넣어준다.

```js
scene.add(new THREE.AmbientLight(0xffffff, 0.8))
const dirLight = new THREE.DirectionalLight(0xffffff, 1)
dirLight.position.set(3, 5, 3)
scene.add(dirLight)
```

## 정리

Three.js 3D 뷰어의 뼈대는 사실 단순하다.

1. **Scene / Camera / Renderer** 세 가지로 무대를 만든다.
2. **Mesh를 Group으로 묶어** 물체를 올린다 — 차 모델이 여러 메쉬라서 Group 개념이 그대로 쓰인다.
3. **tick 루프**로 매 프레임 갱신·렌더한다 — 자동/드래그 회전이 다 여기서 나온다.
4. 차량 뷰어로 가려면 **GLTFLoader(모델) + OrbitControls(조작) + Light(조명)** 세 개를 얹는다.

기본 예제의 상자 세 개에서 시작해도, 상자를 실제 차 모델로 바꾸고 조작·조명을 얹으면 그게 곧 3D 차량 뷰어다. 데이터를 만지는 일을 하다 보니 이런 시각화 도구를 직접 다뤄보는 게 앞으로 더 필요하겠다는 생각이 든다.

## 관련 작업

- threejs-project: "Initial commit: Three.js Journey exercise" (Scene/Group/PerspectiveCamera/WebGLRenderer + tick 애니메이션 루프 기본 예제) — 본문 1~3절의 기본기 코드 근거. 4절(GLTFLoader·OrbitControls·Light)은 이 위에 얹은 확장 설계.
