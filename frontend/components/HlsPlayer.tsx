import { useEffect, forwardRef, useImperativeHandle, useRef } from 'react';
import Hls from 'hls.js';
import { IHlsPlayer } from '../util/interfaces';

/**
 * HLS Player component that uses hls.js to play HLS streams in browsers that do not support it natively.
 * @param {string} src - The source URL of the HLS stream.
 * @param {React.Ref} ref - A ref to the video element.
 * @param {React.HTMLProps<HTMLVideoElement>} props - Additional props for the video element.
 * @returns {JSX.Element} The HLS player component.
 */
const HlsPlayer = forwardRef<HTMLVideoElement, IHlsPlayer>(
  ({ src, ...props }, ref) => {
    const videoRef = useRef<HTMLVideoElement>(null);
    useImperativeHandle(ref, () => videoRef.current!);

    useEffect(() => {
      const video = videoRef.current;

      if (!video) return;

      // Check if the browser supports HLS natively
      if (video.canPlayType('application/vnd.apple.mpegurl')) {
        video.src = src;
        video.addEventListener('loadedmetadata', () => {
          video.play();
        });
      // If not, use hls.js to load the stream
      } else if (Hls.isSupported()) {
        const hls = new Hls();
        hls.loadSource(src);
        hls.attachMedia(video);
        hls.on(Hls.Events.MANIFEST_PARSED, () => {
          video.play();
        });

        return () => {
          hls.destroy();
        };
      }
    }, [src]);

    return (
      <video
        ref={videoRef}
        {...props}
      />
    );
  }
);

export default HlsPlayer;