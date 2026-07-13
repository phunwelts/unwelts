//
//  MoodsViewModel.swift
//  Unwelts
//
//  Polls /moods/recent every 30s — the SwiftUI counterpart of useMoods(30_000).
//  limit=100 matches the web client; the server invalidates exactly that
//  cache key on new submissions.
//

import Foundation
import Observation

@Observable
@MainActor
final class MoodsViewModel {
    private(set) var moods: [Components.Schemas.RecentMoodItem] = []
    private(set) var hexes: [Components.Schemas.HexFeature] = []
    private(set) var total = 0

    private var pollTask: Task<Void, Never>?

    func startPolling() {
        guard pollTask == nil else { return }
        pollTask = Task {
            while !Task.isCancelled {
                await refresh()
                try? await Task.sleep(for: .seconds(30))
            }
        }
    }

    func stopPolling() {
        pollTask?.cancel()
        pollTask = nil
    }

    func refresh() async {
        async let recent = UnweltsAPI.shared.recentMoods()
        async let map = UnweltsAPI.shared.map()
        // Keep showing the last good data on failure; next poll retries.
        if let response = try? await recent {
            moods = response.moods
            total = response.total
        }
        if let response = try? await map {
            hexes = response.features
        }
    }
}
