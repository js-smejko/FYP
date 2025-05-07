# from zmq_capture import LatestResults
from capture import LatestResults
from tracking import Track3D, Track2D
from output import HLSEncoder, FPSCounter
import cv2
from server import app, WebSocketServer
import threading

# Resolution of incoming images
RESOLUTION = (640, 640)
# Dimensions of the tank in mm
TANK = (220, 275, 165)
SCALE = (TANK[0] / RESOLUTION[0], TANK[1] / RESOLUTION[0], TANK[2] / RESOLUTION[1])

def main():
    # Uncomment if using 0MQ capture
    # cap = LatestResults([
    #     "tcp://192.168.0.122:5555",
    #     "tcp://192.168.0.122:5556",
    # ], RESOLUTION)
    # Uncomment if using GStreamer capture
    cap = LatestResults()
    # calibrator = CameraCalibrator(RESOLUTION)
    tracker = Track3D(TANK, 2)
    track2D = Track2D()
    # dataset_builder = MultiImageWriter(0, 100)
    encoders = [HLSEncoder(RESOLUTION, dir) for dir in 
                ["C:/Development/Project/var/www/html/deep", 
                 "C:/Development/Project/var/www/html/wide"]]
    websockets = WebSocketServer()
    fps = FPSCounter()
    # point_triangulation = PointTriangulation(TANK)
    # RelationalData(tracker)

    cap.start()
    for encoder in encoders:
        encoder.start()
    websockets.start()
    threading.Thread(target=app.run, args=("0.0.0.0", 8080), daemon=True).start()

    plots = [None, None]

    print("Finished launching all servers")

    while cv2.waitKey(1) != 27:
        frames = cap()

        fps.update(frames)

        if not all(frame is not None for frame in frames):
            continue
        results, tracks_2d = track2D(frames)
        if results is None:
            continue

        for i, (result, video_writer) in enumerate(zip(results, encoders)):
            if result is not None:
                plots[i] = cv2.resize(result.plot(), (640, 640))
                if tracks_2d is not None and tracks_2d[i] is not None:
                    for key, track in tracks_2d[i].items():
                        cv2.putText(plots[i], f"{key}", (int(track[0]), int(track[1])), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.imshow(f"Image {i}", plots[i])
                # if video_writer is not None:
                video_writer.push_frame(plots[i])
        if tracks_2d is None or tracks_2d[0] is None or tracks_2d[1] is None:
            continue

        # calibrator.show([result.orig_img for result in results])

        # dataset_builder.offer_for_write([result.orig_img for result in results])

        tracks_3d = tracker(tracks_2d)

        if tracks_3d is None or tracks_3d.empty:
            continue

        # tracks_3d = point_triangulation.triangulate_points(tracks_3d)

        websockets.send_data({
            "scatter": [
                {
                    "id": i,
                    "coordinates": 
                    { 
                        "x": z,
                        "y": TANK[1] - x,
                        "z": TANK[2] - y
                    }
                } for i, (x, y, z)
                in tracks_3d.iterrows()
            ]
        })
    
    fps.show_fps()
    cv2.destroyAllWindows()
    cap.stop()
    for video_writer in encoders:
        video_writer.stop()

if __name__ == "__main__":
    main()