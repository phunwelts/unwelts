//
//  Mood+UI.swift
//  Unwelts
//
//  UI attributes for the generated MoodType (MOOD_COLORS / MOOD_TYPES_UI
//  in apps/web/src/types/index.ts).
//

import SwiftUI

typealias MoodType = Components.Schemas.MoodType

extension MoodType {
    // Same display order as the web mood grid.
    static let uiOrder: [MoodType] = [.happy, .calm, .anxious, .sad, .angry, .tired]

    var color: Color {
        switch self {
        case .happy: Color(hex: 0xF5C842)
        case .calm: Color(hex: 0x4ADE80)
        case .anxious: Color(hex: 0xF97316)
        case .sad: Color(hex: 0x60A5FA)
        case .angry: Color(hex: 0xF43F5E)
        case .tired: Color(hex: 0xA78BFA)
        }
    }

    var label: String { rawValue.uppercased() }
}
