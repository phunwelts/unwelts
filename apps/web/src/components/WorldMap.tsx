"use client";

import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { MapboxOverlay } from "@deck.gl/mapbox";
import { ScatterplotLayer } from "@deck.gl/layers";
import { HeatmapLayer } from "@deck.gl/aggregation-layers";
import type { LayersList } from "@deck.gl/core";
import { MOOD_COLORS } from "@/types";
import type { MapDot } from "@/types";

const MAP_STYLE =
  "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";

const BASE_RADIUS_M = 8_000;
const SONAR_MAX_M = 80_000;
const SONAR_FRAMES = 120; // ~2 s at 60 fps

function hexToRgb(hex: string): [number, number, number] {
  return [
    parseInt(hex.slice(1, 3), 16),
    parseInt(hex.slice(3, 5), 16),
    parseInt(hex.slice(5, 7), 16),
  ];
}

/** Per-dot phase offset so each ring pulses independently */
function dotPhase(id: string): number {
  return (id.charCodeAt(0) * 7 + id.charCodeAt(id.length - 1) * 13) %
    SONAR_FRAMES;
}

function buildLayers(dots: MapDot[], tick: number): LayersList {
  // Regional heat glow — density-based, blue-white palette on dark navy
  const heatmap = new HeatmapLayer<MapDot>({
    id: "heatmap",
    data: dots,
    getPosition: (d) => [d.lng, d.lat],
    getWeight: 1,
    radiusPixels: 80,
    intensity: 1.2,
    threshold: 0.03,
    colorRange: [
      [0, 30, 80, 0],
      [0, 50, 150, 60],
      [50, 100, 200, 120],
      [100, 150, 255, 180],
      [200, 220, 255, 220],
      [255, 255, 255, 255],
    ],
  });

  // Solid mood-colored dot
  const dots_layer = new ScatterplotLayer<MapDot>({
    id: "dots",
    data: dots,
    getPosition: (d) => [d.lng, d.lat],
    getFillColor: (d) => hexToRgb(MOOD_COLORS[d.mood_type]),
    getRadius: BASE_RADIUS_M,
    radiusUnits: "meters",
    radiusMinPixels: 4,
    radiusMaxPixels: 10,
    filled: true,
    stroked: false,
    pickable: false,
  });

  // Sonar ring — expands outward and fades, each dot on its own phase
  const sonar = new ScatterplotLayer<MapDot>({
    id: "sonar",
    data: dots,
    getPosition: (d) => [d.lng, d.lat],
    getRadius: (d) => {
      const phase = (tick + dotPhase(d.id)) % SONAR_FRAMES;
      return BASE_RADIUS_M + (phase / SONAR_FRAMES) * SONAR_MAX_M;
    },
    getLineColor: (d) => {
      const phase = (tick + dotPhase(d.id)) % SONAR_FRAMES;
      const alpha = Math.floor(200 * (1 - phase / SONAR_FRAMES));
      return [...hexToRgb(MOOD_COLORS[d.mood_type]), alpha];
    },
    getLineWidth: 2,
    lineWidthUnits: "pixels",
    radiusUnits: "meters",
    filled: false,
    stroked: true,
    pickable: false,
    updateTriggers: {
      getRadius: tick,
      getLineColor: tick,
    },
  });

  return [heatmap, dots_layer, sonar];
}

interface WorldMapProps {
  dots: MapDot[];
}

export default function WorldMap({ dots }: WorldMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const overlayRef = useRef<MapboxOverlay | null>(null);
  const dotsRef = useRef<MapDot[]>(dots);
  const tickRef = useRef(0);
  const frameRef = useRef(0);

  // Keep dotsRef current without restarting the animation loop
  useEffect(() => {
    dotsRef.current = dots;
  }, [dots]);

  // Initialize MapLibre + deck.gl overlay once
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

    const overlay = new MapboxOverlay({ layers: [] });
    map.addControl(overlay);
    overlayRef.current = overlay;

    return () => {
      cancelAnimationFrame(frameRef.current);
      overlayRef.current = null;
      map.remove();
    };
  }, []);

  // Animation loop — runs independently of React render cycle
  useEffect(() => {
    const animate = () => {
      tickRef.current = (tickRef.current + 1) % SONAR_FRAMES;
      overlayRef.current?.setProps({
        layers: buildLayers(dotsRef.current, tickRef.current),
      });
      frameRef.current = requestAnimationFrame(animate);
    };
    frameRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frameRef.current);
  }, []);

  return <div ref={containerRef} className="w-full h-full" />;
}
