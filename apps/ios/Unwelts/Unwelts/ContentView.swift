//
//  ContentView.swift
//  Unwelts
//
//  Same composition as the web page.tsx, stacked vertically for the phone:
//  Header / map stage / mood selector / live feed.
//
//  The map and feed only show while the user's own signal is live
//  (SignalGate) — seeing the world costs a signal.
//

import CoreLocation
import SwiftUI

struct ContentView: View {
    @State private var moodsViewModel = MoodsViewModel()
    @State private var submitViewModel = SubmitViewModel()
    @State private var gate = SignalGate()
    @State private var mapFocus: MapFocus?

    var body: some View {
        // Periodic tick so the gate re-locks on expiry without user action.
        TimelineView(.periodic(from: .now, by: 30)) { context in
            let unlocked = gate.isActive(at: context.date)

            VStack(spacing: 0) {
                HeaderView(total: moodsViewModel.total)

                Group {
                    if unlocked {
                        WorldMapView(moods: moodsViewModel.moods, focus: mapFocus)
                    } else {
                        LockedMapView()
                    }
                }
                .frame(maxHeight: .infinity)

                VStack(alignment: .leading, spacing: 16) {
                    MoodSelectorView(viewModel: submitViewModel)
                    Group {
                        if unlocked {
                            LiveFeedView(moods: moodsViewModel.moods, total: moodsViewModel.total)
                        } else {
                            lockedFeed
                        }
                    }
                    .frame(height: 150)
                }
                .padding(16)
                .overlay(alignment: .top) {
                    Theme.border.frame(height: 1)
                }
            }
        }
        .background(Theme.bg)
        .preferredColorScheme(.dark)
        .task {
            submitViewModel.gate = gate
            submitViewModel.onSuccess = { coordinate in
                // The reward moment: the world appears, then dives to you.
                mapFocus = MapFocus(
                    id: UUID(),
                    latitude: coordinate.latitude,
                    longitude: coordinate.longitude
                )
                await moodsViewModel.refresh()
            }
            moodsViewModel.startPolling()
        }
    }

    private var lockedFeed: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("LIVE FEED")
                .font(Theme.mono(10))
                .tracking(4)
                .foregroundStyle(Theme.muted)
            Text("locked — your signal is your ticket in")
                .font(Theme.mono(10))
                .foregroundStyle(Color(hex: 0x666666))
            Spacer()
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

#Preview {
    ContentView()
}
