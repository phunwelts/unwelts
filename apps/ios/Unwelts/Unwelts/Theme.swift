//
//  Theme.swift
//  Unwelts
//
//  Design tokens ported from apps/web/src/app/globals.css — the web app is
//  the design source of truth.
//

import SwiftUI

extension Color {
    init(hex: UInt32, opacity: Double = 1) {
        self.init(
            .sRGB,
            red: Double((hex >> 16) & 0xFF) / 255,
            green: Double((hex >> 8) & 0xFF) / 255,
            blue: Double(hex & 0xFF) / 255,
            opacity: opacity
        )
    }
}

enum Theme {
    // globals.css @theme
    static let bg = Color(hex: 0x030710)
    static let ocean = Color(hex: 0x040C1B)
    static let surface = Color.white.opacity(0.02)
    static let border = Color.white.opacity(0.04)
    static let borderLight = Color.white.opacity(0.035)
    static let text = Color(hex: 0xCCCCCC)
    static let muted = Color(hex: 0x888888)
    static let dim = Color(hex: 0x555555)

    static let live = Color(hex: 0x06D6A0)
    static let danger = Color(hex: 0xF43F5E)
    static let warn = Color(hex: 0xF97316)
    static let ok = Color(hex: 0x4ADE80)

    // Web is Space Mono at 8–11px; phone sizes bump ~1.2x for readability
    // while keeping the same hierarchy.
    static func mono(_ size: CGFloat, weight: Font.Weight = .regular) -> Font {
        .system(size: size, weight: weight, design: .monospaced)
    }

    // Header wordmark: Playfair Display italic on web → system serif italic.
    static let wordmark: Font = .system(size: 24, weight: .bold, design: .serif)
}
