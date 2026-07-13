//
//  ContentView.swift
//  Unwelts
//
//  Same composition as the web page.tsx, stacked vertically for the phone:
//  Header / map stage / mood selector / live feed.
//

import SwiftUI

struct ContentView: View {
    @State private var moodsViewModel = MoodsViewModel()
    @State private var submitViewModel = SubmitViewModel()

    var body: some View {
        VStack(spacing: 0) {
            HeaderView(total: moodsViewModel.total)

            WorldMapView(moods: moodsViewModel.moods)
                .frame(maxHeight: .infinity)

            VStack(alignment: .leading, spacing: 16) {
                MoodSelectorView(viewModel: submitViewModel)
                LiveFeedView(moods: moodsViewModel.moods, total: moodsViewModel.total)
                    .frame(height: 150)
            }
            .padding(16)
            .overlay(alignment: .top) {
                Theme.border.frame(height: 1)
            }
        }
        .background(Theme.bg)
        .preferredColorScheme(.dark)
        .task {
            submitViewModel.onSuccess = { await moodsViewModel.refresh() }
            moodsViewModel.startPolling()
        }
    }
}

#Preview {
    ContentView()
}
