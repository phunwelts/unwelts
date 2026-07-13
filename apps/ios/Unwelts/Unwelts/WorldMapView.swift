//
//  WorldMapView.swift
//  Unwelts
//
//  Port of WorldMap.tsx: the exact same Carto Dark Matter basemap the web
//  used (MapLibre Native = the web's maplibre-gl), per-mood heatmap glows,
//  and above DETAIL_ZOOM the individual dots, white centers, and the
//  staggered sonar rings.
//

import MapLibre
import SwiftUI

private let mapStyleURL = URL(string: "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json")!
private let detailZoom: Float = 4  // below: heatmap only; above: + dots + sonar
private let sonarFrames = 120

struct WorldMapView: UIViewRepresentable {
    let moods: [Components.Schemas.RecentMoodItem]

    func makeCoordinator() -> Coordinator { Coordinator() }

    func makeUIView(context: Context) -> MLNMapView {
        let mapView = MLNMapView(frame: .zero, styleURL: mapStyleURL)
        mapView.delegate = context.coordinator
        mapView.setCenter(CLLocationCoordinate2D(latitude: 20, longitude: 0), zoomLevel: 1.5, animated: false)
        mapView.minimumZoomLevel = 1
        mapView.maximumZoomLevel = 10
        mapView.allowsRotating = false
        mapView.allowsTilting = false
        mapView.logoView.isHidden = true
        mapView.attributionButton.isHidden = true
        return mapView
    }

    func updateUIView(_ mapView: MLNMapView, context: Context) {
        context.coordinator.update(moods: moods)
    }

    final class Coordinator: NSObject, MLNMapViewDelegate {
        private var source: MLNShapeSource?
        private var sonarLayer: MLNCircleStyleLayer?
        private var displayLink: CADisplayLink?
        private var tick = 0

        private var pendingMoods: [Components.Schemas.RecentMoodItem] = []

        deinit {
            displayLink?.invalidate()
        }

        func update(moods: [Components.Schemas.RecentMoodItem]) {
            pendingMoods = moods
            source?.shape = Self.collection(from: moods)
        }

        func mapView(_ mapView: MLNMapView, didFinishLoading style: MLNStyle) {
            let source = MLNShapeSource(
                identifier: "moods",
                shape: Self.collection(from: pendingMoods),
                options: nil
            )
            style.addSource(source)
            self.source = source

            // One heatmap layer per mood, like buildHeatmapLayers() on web —
            // each mood glows in its own color and they blend where they overlap.
            for mood in MoodType.uiOrder {
                let heatmap = MLNHeatmapStyleLayer(identifier: "heatmap-\(mood.rawValue)", source: source)
                heatmap.predicate = NSPredicate(format: "mood == %@", mood.rawValue)
                heatmap.heatmapRadius = NSExpression(forConstantValue: 80)
                heatmap.heatmapIntensity = NSExpression(forConstantValue: 0.9)
                heatmap.heatmapColor = Self.heatmapRamp(for: UIColor(mood.color))
                style.addLayer(heatmap)
            }

            // Detail dots (glow halo, colored dot, white center) — web shows
            // these only above DETAIL_ZOOM.
            let glow = Self.circleLayer(id: "dot-glow", source: source, radius: 5, opacity: 0.24)
            let dot = Self.circleLayer(id: "dots", source: source, radius: 3, opacity: 1)
            let center = MLNCircleStyleLayer(identifier: "center", source: source)
            center.circleRadius = NSExpression(forConstantValue: 2)
            center.circleColor = NSExpression(forConstantValue: UIColor.white.withAlphaComponent(0.59))
            center.minimumZoomLevel = detailZoom
            for layer in [glow, dot, center] {
                style.addLayer(layer)
            }

            // Sonar: expanding, fading rings staggered per dot (web's
            // buildSonarLayer). A display link advances the shared tick;
            // each feature offsets it by its own "phase" attribute.
            let sonar = MLNCircleStyleLayer(identifier: "sonar", source: source)
            sonar.circleOpacity = NSExpression(forConstantValue: 0)
            sonar.circleStrokeWidth = NSExpression(forConstantValue: 1)
            sonar.circleStrokeColor = Self.moodColorExpression()
            sonar.minimumZoomLevel = detailZoom
            style.addLayer(sonar)
            sonarLayer = sonar
            applySonarFrame()

            let link = CADisplayLink(target: self, selector: #selector(step))
            link.preferredFramesPerSecond = 30
            link.add(to: .main, forMode: .common)
            displayLink = link
        }

        @objc private func step() {
            tick = (tick + 1) % sonarFrames
            applySonarFrame()
        }

        // progress = ((tick + phase) % frames) / frames, per feature.
        private func applySonarFrame() {
            guard let sonar = sonarLayer else { return }
            let progress = "(modulus:by:(phase + \(tick), \(sonarFrames)) / \(Double(sonarFrames)))"
            sonar.circleRadius = NSExpression(format: "5 + \(progress) * 27")
            sonar.circleStrokeOpacity = NSExpression(format: "0.51 * (1 - \(progress))")
        }

        private static func collection(from moods: [Components.Schemas.RecentMoodItem]) -> MLNShapeCollectionFeature {
            let features = moods.map { mood -> MLNPointFeature in
                let feature = MLNPointFeature()
                feature.coordinate = CLLocationCoordinate2D(latitude: mood.lat, longitude: mood.lng)
                feature.attributes = [
                    "mood": mood.moodType.rawValue,
                    "phase": Self.sonarPhase(for: mood.id),
                ]
                return feature
            }
            return MLNShapeCollectionFeature(shapes: features)
        }

        // Web's dotPhase(): stable per-id stagger so rings don't pulse in sync.
        private static func sonarPhase(for id: String) -> Int {
            let first = Int(id.unicodeScalars.first?.value ?? 0)
            let last = Int(id.unicodeScalars.last?.value ?? 0)
            return (first * 7 + last * 13) % sonarFrames
        }

        // Web colorRange: same hue with alphas 0→125/255 across the density
        // ramp, with deck.gl's threshold 0.03 as the transparent floor.
        private static func heatmapRamp(for color: UIColor) -> NSExpression {
            let stops: [NSNumber: UIColor] = [
                0.00: color.withAlphaComponent(0),
                0.03: color.withAlphaComponent(0),
                0.20: color.withAlphaComponent(15 / 255),
                0.40: color.withAlphaComponent(38 / 255),
                0.60: color.withAlphaComponent(68 / 255),
                0.80: color.withAlphaComponent(100 / 255),
                1.00: color.withAlphaComponent(125 / 255),
            ]
            return NSExpression(
                forMLNInterpolating: NSExpression(forVariable: "heatmapDensity"),
                curveType: .linear,
                parameters: nil,
                stops: NSExpression(forConstantValue: stops)
            )
        }

        private static func circleLayer(
            id: String,
            source: MLNShapeSource,
            radius: Double,
            opacity: Double
        ) -> MLNCircleStyleLayer {
            let layer = MLNCircleStyleLayer(identifier: id, source: source)
            layer.circleRadius = NSExpression(forConstantValue: radius)
            layer.circleOpacity = NSExpression(forConstantValue: opacity)
            layer.circleColor = moodColorExpression()
            layer.minimumZoomLevel = detailZoom
            return layer
        }

        // Typed initializer, not a format string: MapLibre 6 renamed its
        // MGL_* expression functions and the format parser throws at
        // style-load time on the old spellings.
        private static func moodColorExpression() -> NSExpression {
            var matches: [NSExpression: NSExpression] = [:]
            for mood in MoodType.uiOrder {
                matches[NSExpression(forConstantValue: mood.rawValue)] =
                    NSExpression(forConstantValue: UIColor(mood.color))
            }
            return NSExpression(
                forMLNMatchingKey: NSExpression(forKeyPath: "mood"),
                in: matches,
                default: NSExpression(forConstantValue: UIColor.gray)
            )
        }
    }
}
