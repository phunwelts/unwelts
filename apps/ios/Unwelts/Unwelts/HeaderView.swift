//
//  HeaderView.swift
//  Unwelts
//
//  Port of Header.tsx: serif italic wordmark, blinking ● LIVE, signal
//  count, UTC clock.
//

import SwiftUI

struct HeaderView: View {
    let total: Int

    @State private var blinkDimmed = false

    private static let utcFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "EEE, dd MMM HH:mm"
        formatter.timeZone = TimeZone(identifier: "UTC")
        formatter.locale = Locale(identifier: "en_US_POSIX")
        return formatter
    }()

    var body: some View {
        HStack(alignment: .center) {
            Text("Unwelts")
                .font(Theme.wordmark)
                .italic()
                .foregroundStyle(.white)

            Spacer()

            HStack(spacing: 14) {
                Text("● LIVE")
                    .font(Theme.mono(10))
                    .tracking(2)
                    .foregroundStyle(Theme.live)
                    .opacity(blinkDimmed ? 0.12 : 1)
                    .onAppear {
                        withAnimation(.easeInOut(duration: 0.65).repeatForever()) {
                            blinkDimmed = true
                        }
                    }

                (Text("\(total.formatted()) ").foregroundStyle(Theme.text)
                    + Text("SIGNALS").foregroundStyle(Theme.muted))
                    .font(Theme.mono(11))
                    .tracking(1)

                TimelineView(.periodic(from: .now, by: 60)) { context in
                    Text(Self.utcFormatter.string(from: context.date))
                        .font(Theme.mono(9))
                        .tracking(1.5)
                        .foregroundStyle(Theme.text)
                }
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 11)
        .overlay(alignment: .bottom) {
            Theme.border.frame(height: 1)
        }
    }
}
