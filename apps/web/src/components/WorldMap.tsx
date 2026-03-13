"use client";

import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { MapboxOverlay } from "@deck.gl/mapbox";
import { ScatterplotLayer } from "@deck.gl/layers";
import { HeatmapLayer } from "@deck.gl/aggregation-layers";
import type { LayersList } from "@deck.gl/core";
import { MOOD_COLORS } from "@/types";
import type { MapDot, MoodType } from "@/types";

const MAP_STYLE =
  "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";

// Below this zoom: only heatmap (organic regional glow).
// Above: heatmap + individual dots + sonar.
const DETAIL_ZOOM = 4;

const DOT_GLOW_PX  = 5;
const DOT_PX       = 3;
const CENTER_PX    = 2;
const SONAR_MIN_PX = 5;
const SONAR_MAX_PX = 32;
const SONAR_FRAMES = 120;

function hexToRgb(hex: string): [number, number, number] {
  return [
    parseInt(hex.slice(1, 3), 16),
    parseInt(hex.slice(3, 5), 16),
    parseInt(hex.slice(5, 7), 16),
  ];
}

const RGB_CACHE = Object.fromEntries(
  Object.entries(MOOD_COLORS).map(([m, hex]) => [m, hexToRgb(hex)])
) as Record<MoodType, [number, number, number]>;

function dotPhase(id: string): number {
  return (id.charCodeAt(0) * 7 + id.charCodeAt(id.length - 1) * 13) % SONAR_FRAMES;
}

/**
 * One HeatmapLayer per mood — smooth Gaussian kernel, scales naturally with zoom.
 * Each mood colors its own density region; overlapping moods blend on the canvas.
 */
function buildHeatmapLayers(dots: MapDot[]): LayersList {
  const moods = [...new Set(dots.map((d) => d.mood_type))];
  return moods.map((mood) => {
    const [r, g, b] = RGB_CACHE[mood];
    return new HeatmapLayer<MapDot>({
      id: `heatmap-${mood}`,
      data: dots.filter((d) => d.mood_type === mood),
      getPosition: (d) => [d.lng, d.lat],
      getWeight: 1,
      radiusPixels: 80,
      intensity: 0.9,
      threshold: 0.03,
      colorRange: [
        [r, g, b,  0],
        [r, g, b, 15],
        [r, g, b, 38],
        [r, g, b, 68],
        [r, g, b, 100],
        [r, g, b, 125],
      ],
    });
  });
}

/** Small individual dots — shown only above DETAIL_ZOOM */
function buildDetailLayers(dots: MapDot[]): LayersList {
  return [
    new ScatterplotLayer<MapDot>({
      id: "dot-glow",
      data: dots,
      getPosition: (d) => [d.lng, d.lat],
      getFillColor: (d) => [...RGB_CACHE[d.mood_type], 60],
      getRadius: DOT_GLOW_PX,
      radiusUnits: "pixels",
      filled: true,
      stroked: false,
      pickable: false,
    }),
    new ScatterplotLayer<MapDot>({
      id: "dots",
      data: dots,
      getPosition: (d) => [d.lng, d.lat],
      getFillColor: (d) => RGB_CACHE[d.mood_type],
      getRadius: DOT_PX,
      radiusUnits: "pixels",
      filled: true,
      stroked: false,
      pickable: false,
    }),
    new ScatterplotLayer<MapDot>({
      id: "center",
      data: dots,
      getPosition: (d) => [d.lng, d.lat],
      getFillColor: [255, 255, 255, 150],
      getRadius: CENTER_PX,
      radiusUnits: "pixels",
      filled: true,
      stroked: false,
      pickable: false,
    }),
  ];
}

function buildSonarLayer(dots: MapDot[], tick: number): ScatterplotLayer<MapDot> {
  return new ScatterplotLayer<MapDot>({
    id: "sonar",
    data: dots,
    getPosition: (d) => [d.lng, d.lat],
    getRadius: (d) => {
      const phase = (tick + dotPhase(d.id)) % SONAR_FRAMES;
      return SONAR_MIN_PX + (phase / SONAR_FRAMES) * (SONAR_MAX_PX - SONAR_MIN_PX);
    },
    radiusUnits: "pixels",
    getLineColor: (d) => {
      const phase = (tick + dotPhase(d.id)) % SONAR_FRAMES;
      const alpha = Math.floor(130 * (1 - phase / SONAR_FRAMES));
      return [...RGB_CACHE[d.mood_type], alpha];
    },
    getLineWidth: 1,
    lineWidthUnits: "pixels",
    filled: false,
    stroked: true,
    pickable: false,
    updateTriggers: { getRadius: tick, getLineColor: tick },
  });
}

interface WorldMapProps {
  dots: MapDot[];
}

export default function WorldMap({ dots }: WorldMapProps) {
  const containerRef  = useRef<HTMLDivElement>(null);
  const overlayRef    = useRef<MapboxOverlay | null>(null);
  const dotsRef       = useRef<MapDot[]>(dots);
  const heatmapsRef   = useRef<LayersList>([]);
  const detailRef     = useRef<LayersList>([]);
  const zoomRef       = useRef(1.5);
  const tickRef       = useRef(0);
  const frameRef      = useRef(0);
  const mapLoadedRef  = useRef(false);

  useEffect(() => {
    dotsRef.current   = dots;
    heatmapsRef.current = buildHeatmapLayers(dots);
    detailRef.current   = buildDetailLayers(dots);
  }, [dots]);

  useEffect(() => {
    if (!containerRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: MAP_STYLE,
      center: [0, 20],
      zoom: 1.5,
      minZoom: 1,
      maxZoom: 10,
      attributionControl: false,
    });

    map.on("load", () => { mapLoadedRef.current = true; });
    map.on("zoom", () => { zoomRef.current = map.getZoom(); });

    const overlay = new MapboxOverlay({ layers: [] });
    map.addControl(overlay);
    overlayRef.current = overlay;

    return () => {
      cancelAnimationFrame(frameRef.current);
      mapLoadedRef.current = false;
      overlayRef.current = null;
      map.remove();
    };
  }, []);

  useEffect(() => {
    const animate = () => {
      tickRef.current = (tickRef.current + 1) % SONAR_FRAMES;
      if (overlayRef.current && mapLoadedRef.current) {
        const detail = zoomRef.current >= DETAIL_ZOOM;
        overlayRef.current.setProps({
          layers: [
            ...heatmapsRef.current,
            ...(detail ? detailRef.current : []),
            ...(detail ? [buildSonarLayer(dotsRef.current, tickRef.current)] : []),
          ],
        });
      }
      frameRef.current = requestAnimationFrame(animate);
    };
    frameRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frameRef.current);
  }, []);

  return <div ref={containerRef} className="w-full h-full" />;
}
