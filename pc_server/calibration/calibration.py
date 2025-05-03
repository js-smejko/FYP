import cv2
from output import Trackbars
from ultralytics.engine.results import Results
from typing import List, Dict, Tuple
import pandas as pd
import numpy as np
import time
from interfaces import XYTracks
from capture import LatestResults
from old_tracking import Track2D, Track3D


class CameraCalibrator:
    """
    Position the subjects edges at the boundaries of the camera view.
    Set threshold according to the camera's perspective.
    """
    def __init__(self, resolution):
        width, height = resolution
        params = [("Top", height), ("Bottom", height), ("Left", width), ("Right", width)]
        self.trackbars = [
            Trackbars("Camera 0 Params", params), 
            Trackbars("Camera 1 Params", params)
        ]
        self.threshold = Trackbars("Threshold", [("Heightwise", height)])
        self.width = width
        self.height = height

    def show(self, images):
        cropped = [
            image[trackbar["Top"]:self.height-trackbar["Bottom"], 
            trackbar["Left"]:self.width-trackbar["Right"]] 
            for image, trackbar in zip(images, self.trackbars)
        ]

        if not cropped[0].any() or not cropped[1].any():
            return

        cv2.imshow("Cropped 0", cv2.resize(cropped[0], (640, 640)))
        cv2.imshow("Cropped 1", cv2.resize(cropped[1], (640, 640)))

    def adjust(self, tracks: List[XYTracks]):
        dfs = [
            pd.DataFrame.from_dict(track, orient="index", columns=["x", "y"])
            for track in tracks
        ]
        for trackbar, df in zip(self.trackbars, dfs):
            offset_x = -trackbar["Left"]
            scale_x = self.width / (self.width - trackbar["Left"] - trackbar["Right"])
            offset_y = -trackbar["Top"]
            scale_y = self.height / (self.height - trackbar["Top"] - trackbar["Bottom"])
            df["x"] = (df["x"] + offset_x) * scale_x
            df["y"] = (df["y"] + offset_y) * scale_y

        return dfs
    
    def get_threshold(self):
        thres = self.threshold["Heightwise"]
        return thres if thres is not None else 0
    
def get_projection_matrix(cap, i: int = 0) -> None:
    # Number of object points
    num_intersections_in_x = 7
    num_intersections_in_y = 7
    square_size = 0.035  # Size of square in meters

    # Arrays to store 3D points and 2D image points
    obj_points = []
    img_points = []

    # Prepare expected object 3D object points (0,0,0), (1,0,0), ...
    object_points = np.zeros((7*7, 3), np.float32)
    object_points[:, :2] = np.mgrid[0:7, 0:7].T.reshape(-1, 2)
    object_points = object_points * square_size
    last = time.time()

    while cv2.waitKey(50) != 27 and len(obj_points) < 49:
        img = cap()[i]
        if img is None:
            continue
        cv2.imshow(f"Camera {i}", img)
        if time.time() - last < 0.5:
            continue
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Find chessboard corners
        ret, corners = cv2.findChessboardCorners(gray, (num_intersections_in_x, num_intersections_in_y), None)

        if ret:
            obj_points.append(object_points)
            img_points.append(corners)

            # Draw and display the corners
            cv2.drawChessboardCorners(img, (7, 7), corners, ret)
            cv2.imshow('SUCCESS!', img)

    ret, K, dist, rvecs, tvecs = cv2.calibrateCamera(obj_points, img_points, (640, 640), None, None)

    return ret, K, dist, rvecs, tvecs

def gather_points(calibrator: CameraCalibrator, cap: LatestResults, track2d: Track2D, track3d: Track3D):
    x, y, z1, z2 = [], [], [], []

    while cv2.waitKey(50) != 27 and len(x) < 49:
        imgs = cap()
        if not all(img is not None for img in imgs):
            continue

        results, tracks2d = track2d(imgs)

        for i, result in enumerate(results):
            cv2.imshow(f"frame {i}", result.plot())
        calibrator.show([result.orig_img for result in results])

        tracks3d = track3d(tracks2d)

        if tracks3d.empty:
            continue

        x.append(tracks3d["x"][0])
        y.append(tracks3d["y"][0])
        z1.append(tracks3d["z1"][0])
        z2.append(tracks3d["z2"][0])

    pts1 = np.array([x, z1], dtype=np.float64).T
    pts2 = np.array([y, z2], dtype=np.float64).T

    return pts1, pts2

def position(pts1, pts2, P1, P2):
    homogeneous = cv2.triangulatePoints(P1, P2, pts1.T, pts2.T)
    normalised = homogeneous[:3] / homogeneous[3]

    x_off = min(normalised[0])
    x_scale = max(normalised[0]) - x_off
    y_off = min(normalised[1])
    y_scale = max(normalised[1]) - y_off
    z_off = min(normalised[2])
    z_scale = max(normalised[2]) - z_off

    return (x_off, y_off, z_off), (x_scale, y_scale, z_scale)