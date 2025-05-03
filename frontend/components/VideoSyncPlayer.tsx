import React, { useRef, useState, useEffect } from "react";
import HlsPlayer from "./HlsPlayer";
import classes from "../modules/VideoPlayer.module.css";
// Adjust to a better placeholder image
import placeholder from '../../public/favicon.ico';

/**
 * VideoSyncPlayer component that synchronizes two HLS video players.
 * It allows for adjusting the delay between the two videos, changing playback speed, and pausing both videos simultaneously.
 * It also provides a "Live" button to reset the delay and set both videos to their end time.
 * @returns {JSX.Element} The VideoSyncPlayer component.
 * */
const VideoSyncPlayer = () => {
  const video1Ref = useRef<HTMLVideoElement>(null);
  const video2Ref = useRef<HTMLVideoElement>(null);

  const [delay, setDelay] = useState(0);
  const [playbackRate, setPlaybackRate] = useState<number>(1);
  const [pause, setPause] = useState(false);

  const videos = [video1Ref, video2Ref];

  useEffect(() => {
    const video1 = video1Ref.current;
    const video2 = video2Ref.current;
    if (video1 && video2 && delay >= 0) {
      const targetTime1 = video1.duration - delay;
      const targetTime2 = video2.duration - delay;
      if (targetTime1 >= 0 && targetTime1 <= video1.duration && targetTime2 >= 0 && targetTime2 <= video2.duration) {
        video1.currentTime = targetTime1;
        video2.currentTime = targetTime2;
      }
    }
  }, [delay]);

  const handleDelayChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newDelay = parseFloat(e.target.value);
    setDelay(newDelay);
  };

  const toggleSpeed = () => {
    let speeds = [0.125, 0.25, 0.5, 1, 1.5, 2, 5, 15]
    const newRate = speeds[(speeds.findIndex(value => value === playbackRate) + 1) % 8];
    videos.forEach(ref => {
      if (ref.current) ref.current.playbackRate = newRate;
    });
    setPlaybackRate(newRate);
  };

  const togglePause = () => {
    videos.forEach(ref => {
      if (ref.current) {
        if (pause) {
          ref.current.play();
        } else {
          ref.current.pause();
        }
      }
    });
    setPause(paused => !paused);
  };

  const handleLive = () => {
    const video1 = video1Ref.current;
    const video2 = video2Ref.current;

    if (video1 && video2) {
      video1.currentTime = video1.duration;
      video2.currentTime = video2.duration;
      setDelay(0);
    } 
  };

  return (
    <div className={classes.container}>
      <div style={{ display: "flex", gap: 10 }}>
        <HlsPlayer
          className={classes.video}
          ref={video1Ref}
          src="http://192.168.2.162:8080/deep/playlist.m3u8"
          controls={false}
          onClick={() => video1Ref.current?.requestFullscreen()}
          poster={placeholder}
        />
        <HlsPlayer
          className={classes.video}
          ref={video2Ref}
          src="http://192.168.2.162:8080/wide/playlist.m3u8"
          controls={false}
          onClick={() => video1Ref.current?.requestFullscreen()}
          poster={placeholder}
        />
      </div>

      <div style={{ display: "flex", marginTop: 20, alignItems: "center", justifyContent: "center", gap: 10 }}>
      Delay:
      <input
          type="range"
          min={0}
          max={56} // Adjust according to how long the playlist is
          value={delay}
          step={4}
          onChange={handleDelayChange}
        />
        {delay}s
        <button onClick={toggleSpeed}>Speed: {playbackRate}x</button>
        <button onClick={togglePause}>
          {pause ? "Play" : "Pause"}
        </button>
        <button onClick={handleLive}>
          Live
        </button>
      </div>
    </div>
  );
};

export default VideoSyncPlayer;
