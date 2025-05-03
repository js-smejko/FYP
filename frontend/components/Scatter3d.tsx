import { useEffect, useRef } from 'react';
import Plotly from 'plotly.js-dist-min';
import { IScatter3d } from '../util/interfaces';

/**
 * 
 * @param data - The data to be plotted. Each item should have an id and coordinates (x, y, z).
 * @param traceColours - The colours to be used for the traces.
 * @param scene - The scene configuration for the 3D plot.
 * @param pause - A boolean to pause the plot updates.
 * @param interactive - A boolean to enable or disable user interactivity.
 * @param onPointClick - A callback function to handle point clicks. NOT YET IMPLEMENTED.
 * @param props - Additional props to be passed to the Plotly chart.
 * @returns {JSX.Element} The Scatter3d component.
 */
const Scatter3d = ({
  data,
  traceColours,
  scene,
  pause,
  interactive,
  onPointClick,
  ...props
}: IScatter3d) => {
  // Connects the <div> element to Plotly
  const chartRef = useRef<HTMLDivElement>(null);
  // Maps the track IDs to Plotly's trace indices
  const traceIndexMap = useRef<Map<number, number>>(new Map());

  // Sets up the Plotly chart when the component mounts
  useEffect(() => {
    const chart = chartRef.current as Plotly.PlotlyHTMLElement | null;
    if (!chart) return;

    const layout: Partial<Plotly.Layout> = {
      margin: { l: 0, r: 0, t: 0, b: 0 },
      scene,
      showlegend: false
    };

    const config: Partial<Plotly.Config> = interactive ? {
      responsive: true
    } : {
      responsive: true,
      displayModeBar: false,
      scrollZoom: false,
      doubleClick: false,
      showAxisDragHandles: false,
    };

    if (chartRef.current) {
      Plotly.newPlot(chartRef.current, [], layout, config);
    }
  }, []);

  // Updates the Plotly chart when the data changes
  useEffect(() => {
    const chart = chartRef.current as Plotly.PlotlyHTMLElement | null;
    if (!data || pause || !chart) return;

    if (chart.data.length !== traceIndexMap.current.size) {
      traceIndexMap.current.clear();
      return;
    }

    const toAdd = data.filter(({ id }) => !traceIndexMap.current.has(id));
    const toUpdate = data.filter(({ id }) => traceIndexMap.current.has(id));

    if (toAdd.length > 0) {
      // New traces are single points by default
      const newTraces = toAdd.map(({ id, coordinates }) => ({
        x: [coordinates.x],
        y: [coordinates.y],
        z: [coordinates.z],
        type: 'scatter3d',
        name: `ID ${id}`,
        mode: 'text+markers',
        text: [id.toString()],
        textposition: 'middle center',
        textfont: { size: 12, color: 'white' },
        marker: { size: 12, color: traceColours[id % 3] }
      }));

      let currentTraceCount = chart.data.length;
      toAdd.forEach((item, index) => {
        traceIndexMap.current.set(item.id, currentTraceCount + index);
      });

      Plotly.addTraces(chart, newTraces as Partial<Plotly.ScatterData>[]);
    }

    if (toUpdate.length > 0) {
      const updateIndices = toUpdate.map(({ id }) => traceIndexMap.current.get(id)!);

      const toTrack = toUpdate.filter(({ track }) => track)
      const lineIndices = toTrack.map(({ id }) => traceIndexMap.current.get(id)!);
      const toMark = toUpdate.filter(({ track }) => !track)
      const markIndices = toMark.map(({ id }) => traceIndexMap.current.get(id)!);

      if (markIndices.length > 0) {
        Plotly.extendTraces(chart, {
          x: toMark.map(({ coordinates }) => [coordinates.x]),
          y: toMark.map(({ coordinates }) => [coordinates.y]),
          z: toMark.map(({ coordinates }) => [coordinates.z]),
        }, markIndices, 1);
      }

      // Keep historical data points for the tracked points
      if (lineIndices.length > 0) {
        Plotly.extendTraces(chart, {
          x: toTrack.map(({ coordinates }) => [coordinates.x]),
          y: toTrack.map(({ coordinates }) => [coordinates.y]),
          z: toTrack.map(({ coordinates }) => [coordinates.z]),
        }, lineIndices);
      }

      Plotly.restyle(chart, {
        mode: toUpdate.map(({ track }) => track ? 'lines' : 'markers+text') as any,
        'marker.opacity': toUpdate.map(({ track }) => track ? 0 : 1),
        'marker.size': toUpdate.map(({ track }) => track ? 0 : 12),
        'marker.color': toUpdate.map((_, i) => traceColours[i]) as any,
        'line.color': toUpdate.map((_, i) => traceColours[i]) as any
      }, updateIndices);
    }
  }, [data, traceColours, pause]);

  return (
    <>
      <div ref={chartRef} {...props} />
    </>
  );
};

export default Scatter3d;
