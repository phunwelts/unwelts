//
//  LockedMapView.swift
//  Unwelts
//
//  What the map area shows before the user's signal is live: the dark
//  ocean, the scanlines, and the invitation. No world until you're on it.
//

import SwiftUI

struct LockedMapView: View {
    @State private var blinkDimmed = false

    var body: some View {
        GeometryReader { proxy in
            ZStack {
                Theme.ocean

                VStack(spacing: 10) {
                    Text("THE WORLD IS HIDDEN")
                        .font(Theme.mono(11))
                        .tracking(4)
                        .foregroundStyle(Theme.muted)
                        .opacity(blinkDimmed ? 0.35 : 1)
                        .onAppear {
                            withAnimation(.easeInOut(duration: 1.1).repeatForever()) {
                                blinkDimmed = true
                            }
                        }
                    Text("send your signal to see everyone else's")
                        .font(Theme.mono(10))
                        .foregroundStyle(Theme.dim)
                    Text("the map stays open for \(SignalGate.windowHours)h per signal")
                        .font(Theme.mono(9))
                        .foregroundStyle(Color(hex: 0x444444))
                }

                scanlines(size: proxy.size)
            }
        }
        .clipped()
    }

    private func scanlines(size: CGSize) -> some View {
        Canvas { context, _ in
            var y: CGFloat = 0
            while y < size.height {
                context.fill(
                    Path(CGRect(x: 0, y: y, width: size.width, height: 1)),
                    with: .color(.white.opacity(0.007))
                )
                y += 4
            }
        }
        .allowsHitTesting(false)
    }
}
