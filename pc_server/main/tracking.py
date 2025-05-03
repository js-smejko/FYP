###
# Track objects in 2D and 3D once cameras are calibrated
###

from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
from ultralytics.engine.results import Results
from ultralytics import YOLO
import cv2
import json
from interfaces import XYTrack, XYTracks, XYZTracks, IDPair

class Track2D:
    """
    Implements direct tracking of objects in 2D
    Can batch process frames from multiple cameras
    """
    def __init__(self):
        # Point to desired model
        self.model = YOLO("models/led.pt")
        self.tracks_on_cameras: List[XYTracks] = [{}, {}]
        self.next_id = 1
        print(self.model.info())

    def find_best(self, track1: XYTrack, tracks2: XYTracks, thres = 1000.):
        """
        Linear search for the shortest distance between a coordinate and a set of coordinates

        Args: 
            track1 (XYTrack): Coordinate of the object in a frame
            tracks2 (XYTracks): All coordinates of the objects in another frame

        Returns:
            int: The ID of the best match in tracks2
            float | floating[Any]: The distance between the two coordinates
        """
        idx, best = -1, thres
        for j, track2 in tracks2.items():
            s =  np.linalg.norm(np.array(track1) - np.array(track2))
            if s <= best:
                idx, best = j, s

        return idx, best

    def track(self, result: Results, tracks: XYTracks) -> XYTracks:
        """
        Searches for the best match between the current frame and the previous frame

        Args:
            result (Results): YOLO results for the current frame
            tracks (XYTracks): ID: (x, y) of the previous frame
        """
        if result.boxes.xywh is None:
            return
        
        next_tracks = result.boxes.xywh.cpu()#.reshape(-1, 2)
        # print(next_tracks)
        next_tracks = {i: (x[0].item(), x[1].item()) for i, x in enumerate(next_tracks)}

        assigned: XYTracks = {}
        while len(next_tracks) > 0 and len(tracks) > 0:
            for i, track in tracks.items():
                # Previous track finds its best match
                idx, s = self.find_best(track, next_tracks, 1000)
                if idx != -1: 
                    # Current track confims that this is the best match
                    confirm, _ = self.find_best(next_tracks[idx], tracks, s)
                    if confirm == i:
                        assigned[i] = (next_tracks[idx][0], next_tracks[idx][1])
                        del next_tracks[idx]

            tracks = {k: v for k, v in tracks.items() if k not in assigned.keys()}

        # print(f"Maintained tracks {assigned}")

        for track in next_tracks.values():
            assigned[self.next_id] = (track[0], track[1])
            # print(f"New track {self.next_id} at {track[0]}, {track[1]}")
            self.next_id += 1

        return assigned

    def __call__(self, frames) -> Tuple[List[Results], List[XYTracks]]:
        """
        Matches current frame to tracks in previous frame
        Returns a list of results and a list of tracks for each camera

        Args:
            frames: Canon frames to be processed
        """
        if not all(frame is not None for frame in frames):
            return
        results: List[Results] = self.model(
            frames, 
            iou=0.7,
            conf=0.25,
            # imgsz=(640, 640),
            device=0,
            verbose=False
            )
        if not all(result is not None for result in results):
            return results
        for i, (tracks, result) in enumerate(zip(self.tracks_on_cameras, results)):
            self.tracks_on_cameras[i] = self.track(result, tracks)
        # print(self.tracks_on_cameras)

        return results, self.tracks_on_cameras


class Track3D:
    """
    Tracks objects in a 3D space using two cameras
    Matches 2D coordinates from two cameras using their Eucilidean plane
    Perform calibration beforehand, save the fundamental matrix to camera_params.json as F
    """
    def __init__(self, bounds: Tuple[int, int, int], obj_count = 100):
        self.tracking: XYZTracks = {}
        self.idMap: Dict[int, IDPair] = {}
        self.ids = [i for i in range(0, obj_count)]
        # Camera calibration
        params = json.load(open("camera_params.json"))
        self.offsets = np.array(params["offsets"])
        # OpenCV's coordinate system is different
        self.scales = [bounds[1], bounds[2], bounds[0]] / np.array(params["scales"])
        self.p1 = np.array(params['P1'])
        self.p2 = np.array(params['P2'])
        self.F = np.array(params["F"])
        self.unassigned = obj_count
        self.obj_count = obj_count
    
    def match_by_location(self, deep_df: pd.DataFrame, wide_df: pd.DataFrame) -> List[IDPair]:
        """
        Lists the IDs of objects that are on the same Eucilidean plane within a threshold
        """
        equalHeight: List[IDPair] = []

        pts1 = np.array([deep_df["x"], deep_df["y"]], dtype=np.float64).T
        pts2 = np.array([wide_df["x"], wide_df["y"]], dtype=np.float64).T
        pts1_h = cv2.convertPointsToHomogeneous(pts1).reshape(-1, 3)
        pts2_h = cv2.convertPointsToHomogeneous(pts2).reshape(-1, 3)

        errors: np.ndarray = np.abs(pts2_h @ self.F @ pts1_h.T)

        # print(f"Errors: {errors}")

        inliers = np.where(errors < 0.05)

        # print(inliers)

        rows, cols = inliers
        for r, c in zip(rows, cols):
            # print(f"Inlier at row {r}, col {c} — pts2[{r}] with pts1[{c}]")
            equalHeight.append((deep_df.index[c], wide_df.index[r]))
            
        # Unassigned IDs should be unique so that they are never maintained across frames
        for i, _ in deep_df.iterrows():
            if i not in [pair[0] for pair in equalHeight]:
                equalHeight.append((i, -self.unassigned))
                self.unassigned += 1

        for i, _ in wide_df.iterrows():
            if i not in [pair[1] for pair in equalHeight]:
                equalHeight.append((-self.unassigned, i))
                self.unassigned += 1

        return equalHeight

    def update_internal_ids(self, equalHeight: List[IDPair]):
        """
        Maps the IDs of objects that share the same height in both frames

        Args:
            equalHeight (List[IDPair]): List of tuples containing the IDs of objects that share the same height in both frames.
        """
        newMap = {}
        equalHeight_df = pd.DataFrame(equalHeight, columns=["dim0", "dim1"])
        
        # Check which mappings were exact across frames, then which maintained some similarity
        for threshold in range(2, 0, -1):
            for i, dims in self.idMap.items():
                if equalHeight_df.empty:
                    break

                scores = equalHeight_df.apply(lambda row: np.sum(np.array(dims) == np.array([row["dim0"], row["dim1"]])), axis=1)

                # Find the best match if it meets the threshold
                best_score = scores.max()
                if best_score >= threshold:
                    best_idx = scores.idxmax()
                    match = equalHeight_df.loc[best_idx]
                    newMap[i] = tuple(match)

                    # Remove rows with the same dim0 or dim1
                    equalHeight_df = equalHeight_df[
                        (equalHeight_df["dim0"] != match["dim0"]) & 
                        (equalHeight_df["dim1"] != match["dim1"])
                    ]
                    # print(f"Matched {dims} with {tuple(match)}")
            
            self.idMap = {k: v for k, v in self.idMap.items() if k not in newMap.keys()}

        unassigned = [i for i in self.ids if i not in newMap.keys()]

        for id in unassigned:
            if equalHeight_df.empty:
                break
            row = equalHeight_df.iloc[0]
            # print(f"New track for {tuple(row)} at {self.next_id}")
            newMap[id] = tuple(row)
            equalHeight_df = equalHeight_df[
                (equalHeight_df["dim0"] != row["dim0"]) & 
                (equalHeight_df["dim1"] != row["dim1"])
            ]
        
        self.idMap = newMap

    def merge_dataframes(self, wide_df: pd.DataFrame, deep_df: pd.DataFrame):
        """
        Merges two DataFrames based on a mapping of track_id pairs while updating x1 and x2.

        Args:
            df1 (pd.DataFrame): First DataFrame containing track_id and box.
            df2 (pd.DataFrame): Second DataFrame containing track_id and box.

        Returns:
            pd.DataFrame: Merged DataFrame with updated box values.
        """
        deep_id_dict = {v[0]: k for k, v in self.idMap.items() if v[0] > 0}
        wide_id_dict = {v[1]: k for k, v in self.idMap.items() if v[1] > 0}
        # print(track_id_dict)

        deep_df = deep_df[deep_df.index.isin(deep_id_dict.keys())]
        wide_df = wide_df[wide_df.index.isin(wide_id_dict.keys())]

        # deep_df = deep_df.rename(columns={"track_id": "track_id_other"})

        # Map the 2D IDs to a single 3D ID
        deep_df.index = deep_df.index.to_series().replace(deep_id_dict)
        wide_df.index = wide_df.index.to_series().replace(wide_id_dict)

        deep_df.columns = deep_df.columns.str.replace("y", "z1")
        wide_df.columns = wide_df.columns.str.replace("y", "z2")
        wide_df.columns = wide_df.columns.str.replace("x", "y")

        # Merge both DataFrames based on track_id
        merged_df = wide_df.merge(
            deep_df[["x", "z1"]], 
            left_index=True, right_index=True, how="outer")

        return merged_df
    
    def triangulate_points(self, xzyz_df: pd.DataFrame) -> pd.DataFrame:
        """
        Uses camera parameters to triangulate points in 3D space
        """
        x = xzyz_df["x"].to_numpy()
        y = xzyz_df["y"].to_numpy()
        z1 = xzyz_df["z1"].to_numpy()
        z2 = xzyz_df["z2"].to_numpy()

        pts1 = np.vstack((x, z1))
        pts2 = np.vstack((y, z2))

        homogeneous = cv2.triangulatePoints(self.p1, self.p2, pts1, pts2)

        scaled = np.array([
            np.maximum(((co / homogeneous[3] - offset) * scale), 0)
            for co, offset, scale 
            in zip(homogeneous[:3], self.offsets, self.scales)
        ])

        xyz_df = pd.DataFrame(scaled.T, columns=["x", "y", "z"])
        xyz_df.set_index(xzyz_df.index)

        return xyz_df

    def __call__(self, tracks: List[XYTracks]) -> pd.DataFrame:
        """
        Records the locations of objects 3D where possible

        Args:
            tracks (List[XYTracks]): List of 2D tracks from two cameras.

        Returns: 
            pd.DataFrame: DataFrame containing 3D coordinates of tracked objects where the index corresponds to the ID
        """
        if len(tracks[0]) == 0 or len(tracks[1]) == 0:
            return None

        deep_df = pd.DataFrame.from_dict(tracks[0], orient="index", columns=["x", "y"])
        wide_df = pd.DataFrame.from_dict(tracks[1], orient="index", columns=["x", "y"])

        equalHeight = self.match_by_location(deep_df, wide_df)
        self.update_internal_ids(equalHeight)
        xzyz_df = self.merge_dataframes(wide_df, deep_df)

        xzyz_df.dropna(inplace=True)

        return self.triangulate_points(xzyz_df)

    def __getitem__(self, track_id):
        """
        Safely retrieves the track by ID, returning the last known position if the ID is not found.
        Args:
            track_id (int): The ID of the track to retrieve.
        Returns:
            XYZTrack: The track corresponding to the given ID, or the last known position if not found.
        """
        if track_id not in self.tracking:
            if track_id == -1 and len(self.tracking) > 0:
                return list(self.tracking.values())[-1]
            else:
                return None
        return self.tracking[track_id]
    
    def __iter__(self):
        return iter(list(self.tracking.items()))