from calibration import CameraCalibrator
from old_tracking import Track2D, Track3D
import cv2
import numpy as np
from capture import LatestResults
from calibration import get_projection_matrix, gather_points, position
import json

if __name__ == "__main__":
    calibrator = CameraCalibrator((640, 640))
    track3d = Track3D(calibrator)
    track2d = Track2D()

    cap = LatestResults()
    cap.start()

    # params = [[], []]
    # for i in range(2):
    #     params.append(get_projection_matrix(cap, i))

    pts1, pts2 = gather_points(calibrator, cap, track2d, track3d)

    cap.stop()
    cv2.destroyAllWindows()

    F, mask = cv2.findFundamentalMat(pts1, pts2, method=cv2.FM_RANSAC)

    # K1 = params[0][1]
    # K2 = params[1][1]
    K1 = np.array([
        [1004.6, 0, 335.59],
        [0, 991.47, 273.95],
        [0, 0, 1]
    ])

    K2 = np.array([
        [928.95, 0, 289.87],
        [0, 927.31, 296.52],
        [0, 0, 1]
    ])

    E = K2.T @ F @ K1
    # Inputs: Essential matrix and matching points (normalized coordinates if already undistorted)
    points, R, t, mask = cv2.recoverPose(E, pts1, pts2, K1)

    extrinsic = np.hstack((R, t))  # shape (3, 4)

    print(f"F: {F} R: {R}, t: {t}, extrinsic: {extrinsic}")

    # Build extrinsic matrices
    I = np.eye(3)
    zero_t = np.zeros((3, 1))

    # P1 = K1 * [I | 0]
    P1 = K1 @ np.hstack((I, zero_t))
    print("P1: ", P1)

    # P2 = K2 * [R | t]
    P2 = K2 @ np.hstack((R, t))
    print("P2: ", P2)

    offsets, scales = position(pts1, pts2, P1, P2)
    print("Offsets: ", offsets)
    print("Scales: ", scales)

    params = {
        "F": F.tolist(),
        "mask": mask.tolist(),
        "K1": K1.tolist(),
        "K2": K2.tolist(),
        "P1": P1.tolist(),
        "P2": P2.tolist(),
        "offsets": offsets,
        "scales": scales
    }

    json_str = json.dumps(params, indent=2)

    with open("camera_params.json", "w") as f:
        f.write(json_str)
    print("Parameters saved to camera_params.json")