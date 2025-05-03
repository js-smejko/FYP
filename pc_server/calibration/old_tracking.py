from calibration import CameraCalibrator
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
from ultralytics.engine.results import Results
from ultralytics.engine.results import Boxes
from ultralytics import YOLO
import cv2
from interfaces import XYTrack, XYTracks, XYZTrack, XYZTracks, IDPair

class Track2D:
    def __init__(self):
        self.model = YOLO("models/led.pt")
        self.tracks_on_cameras: List[XYTracks] = [{}, {}]
        self.next_id = 0
        print(self.model.info())

    def find_best(self, track1: XYTrack, tracks2: XYTracks, thres = 1000.) -> XYTrack:
        idx, best = -1, thres
        for j, track2 in tracks2.items():
            s =  np.linalg.norm(np.array(track1) - np.array(track2))
            if s <= best:
                idx, best = j, s

        return idx, best

    def track(self, result: Results, tracks: XYTracks) -> XYTracks:
        if result.boxes.xywh is None:
            return
        
        next_tracks = result.boxes.xywh.cpu()#.reshape(-1, 2)
        # print(next_tracks)
        next_tracks = {i: (x[0].item(), x[1].item()) for i, x in enumerate(next_tracks)}

        assigned: XYTracks = {}
        while len(next_tracks) > 0 and len(tracks) > 0:
            for i, track in tracks.items():
                idx, s = self.find_best(track, next_tracks, 1000)
                if idx != -1:
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
        # (1344, 960) full res
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
    Assumes that frames sharing a common second axis are the same
    """
    def __init__(self, calibrator: CameraCalibrator, obj_count = 100):
        self.tracking: XYZTracks = {}
        self.idMap: Dict[int, IDPair] = {}
        self.calibrator = calibrator
        self.ids = [i for i in range(0, obj_count)]
    
    def match_by_location(self, deep_df: pd.DataFrame, wide_df: pd.DataFrame) -> List[IDPair]:
        """
        Lists the IDs of objects that share the same height in both frames
        """
        equalHeight: List[IDPair] = []

        thres = self.calibrator.get_threshold()

        for i, deep in deep_df.iterrows():
            for j, wide in wide_df.iterrows():
                if abs(deep["y"] - wide["y"]) < thres:
                    equalHeight.append((i, j))

        # Append remaining track_ids where the other column has a -1
        for i, _ in deep_df.iterrows():
            if i not in [pair[0] for pair in equalHeight]:
                equalHeight.append((i, -1))

        for i, _ in wide_df.iterrows():
            if i not in [pair[1] for pair in equalHeight]:
                equalHeight.append((-1, i))

        return equalHeight

    def update_internal_ids(self, equalHeight: List[IDPair]):
        """
        Maps the IDs of objects that share the same height in both frames
        """
        newMap = {}
        equalHeight_df = pd.DataFrame(equalHeight, columns=["dim0", "dim1"])
        equalHeight_df["dim0"].replace({-1: -2})
        equalHeight_df["dim1"].replace({-1: -2})
        
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
        deep_id_dict = {v[0]: k for k, v in self.idMap.items()}
        wide_id_dict = {v[1]: k for k, v in self.idMap.items()}
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

    def __call__(self, tracks: List[XYTracks]) -> pd.DataFrame:
        """
        Records the locations of objects 3D where possible
        """
        if tracks[0] is None or tracks[0] is None:
            return None

        deep_df, wide_df = self.calibrator.adjust(tracks)

        equalHeight = self.match_by_location(deep_df, wide_df)
        self.update_internal_ids(equalHeight)
        xzyz_df = self.merge_dataframes(wide_df, deep_df)

        pd.set_option("display.max_rows", None)  # Show all rows
        pd.set_option("display.max_columns", None)  # Show all columns
        pd.set_option("display.width", 1000)  # Expand display width
        pd.set_option("display.max_colwidth", None)  # Prevent column content truncation

        xzyz_df.dropna(inplace=True)
        
        return xzyz_df     

    
    def __getitem__(self, track_id):
        if track_id not in self.tracking:
            if track_id == -1 and len(self.tracking) > 0:
                return list(self.tracking.values())[-1]
            else:
                return None
        return self.tracking[track_id]
    
    def __iter__(self):
        return iter(list(self.tracking.items()))
    
if __name__ == "__main__":
    track2D = Track2D()
    cap = cv2.VideoCapture(0)
    while cv2.waitKey(1) != 27:
        ret, frame = cap.read()
        if not ret:
            break
        result = track2D(frame)[0]
        # cv2.imshow("frame", result.plot())
