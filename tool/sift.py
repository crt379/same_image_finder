import hashlib
import cv2
import numpy as np

_DOWN_MAX_WIDTH = 1000
_DOWN_MAX_HEIGHT = 1000
_FLANN_INDEX_KDTREE = 0
_INDEX_PARAMS = dict(algorithm=_FLANN_INDEX_KDTREE, trees=5)
_SEARCH_PARAMS = dict(checks=50)


def count_image_md5(image) -> str:
    return hashlib.md5(image).hexdigest()


def count(image: np.ndarray) -> tuple[np.ndarray, np.ndarray, object]:
    # 灰度图
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  
    # 创建SIFT特征检测器
    sift = cv2.SIFT_create()
    # 特征点提取与描述子生成
    kp, des = sift.detectAndCompute(gray, None)
    # 包含特征点图
    sift_image = cv2.drawKeypoints(image, kp, None)  

    return sift_image, des, kp


def count_by_down(image: np.ndarray) -> tuple[np.ndarray, np.ndarray, object]:
    sp = image.shape
    h = sp[0]
    w = sp[1]

    # 图片过大，降采样
    while w > _DOWN_MAX_WIDTH or h > _DOWN_MAX_HEIGHT:
        image = cv2.pyrDown(image)
        sp = image.shape
        h = sp[0]
        w = sp[1]
    
    return count(image)

def count_images(image_paths: list[str]) -> list[tuple[str, str, tuple[np.ndarray, np.ndarray, object]]]:
    sift_infos = []

    for path in image_paths:
        image_buf = np.fromfile(path, dtype=np.uint8)
        try:
            image = cv2.imdecode(image_buf, cv2.IMREAD_COLOR)
        except Exception:
            image = None

        if image is None:
            continue

        sift_info = count_by_down(image)
        image_md5 = count_image_md5(image)
        sift_infos.append((path, image_md5, sift_info))

    return sift_infos


def sift_good_match(des1, des2):
    flann = cv2.FlannBasedMatcher(_INDEX_PARAMS, _SEARCH_PARAMS)
    matches = flann.knnMatch(des1, des2, k=2)
    good = []
    for m, n in matches:
        if m.distance < 0.4 * n.distance:
            good.append(m)
    
    return good
