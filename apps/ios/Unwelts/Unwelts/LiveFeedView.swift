//
//  LiveFeedView.swift
//  Unwelts
//
//  Port of LiveFeed.tsx: Anonymous rows with glowing mood dot and relative
//  timestamp.
//

import SwiftUI

struct LiveFeedView: View {
    let moods: [Components.Schemas.RecentMoodItem]
    let total: Int

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            (Text("LIVE FEED").tracking(4)
                + Text(total > 0 ? "  — \(total.formatted()) today" : "")
                    .foregroundStyle(Theme.dim))
                .font(Theme.mono(10))
                .foregroundStyle(Theme.muted)

            if moods.isEmpty {
                Text("No signals yet…")
                    .font(Theme.mono(10))
                    .foregroundStyle(Color(hex: 0x666666))
            } else {
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 0) {
                        ForEach(moods.prefix(15), id: \.id) { mood in
                            feedRow(mood)
                        }
                    }
                }
            }
        }
    }

    private func feedRow(_ mood: Components.Schemas.RecentMoodItem) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text("Anonymous")
                    .font(Theme.mono(10))
                    .foregroundStyle(Theme.text)
                Spacer()
                Text(Self.relativeTime(from: mood.submittedAt))
                    .font(Theme.mono(9))
                    .foregroundStyle(Theme.muted)
            }
            HStack(spacing: 6) {
                Circle()
                    .fill(mood.moodType.color)
                    .frame(width: 5, height: 5)
                    .shadow(color: mood.moodType.color, radius: 2)
                Text(mood.moodType.rawValue)
                    .font(Theme.mono(10))
                    .foregroundStyle(mood.moodType.color)
                if let note = mood.note, !note.isEmpty {
                    Text("— \(note)")
                        .font(Theme.mono(9))
                        .foregroundStyle(Theme.muted)
                        .lineLimit(1)
                }
            }
        }
        .padding(.vertical, 8)
        .overlay(alignment: .bottom) {
            Color.white.opacity(0.025).frame(height: 1)
        }
        .transition(.asymmetric(
            insertion: .move(edge: .trailing).combined(with: .opacity),
            removal: .opacity
        ))
    }

    static func relativeTime(from date: Date) -> String {
        let seconds = max(0, Int(Date.now.timeIntervalSince(date)))
        if seconds < 60 { return "\(seconds)s ago" }
        if seconds < 3600 { return "\(seconds / 60)m ago" }
        return "\(seconds / 3600)h ago"
    }
}
