//
//  SubmitViewModel.swift
//  Unwelts
//
//  Port of useSubmitMood: same states, same transitions, same 3s reset.
//

import CoreLocation
import Foundation
import Observation
import UIKit

enum SubmitState: Equatable {
    case idle
    case submitting
    case success
    case error
    case rateLimited
    case geoDenied
}

@Observable
@MainActor
final class SubmitViewModel {
    var selectedMood: MoodType?
    var note = ""
    private(set) var submitState: SubmitState = .idle
    private(set) var retryLabel = ""

    private let location = LocationService()
    var onSuccess: (() async -> Void)?

    var canSend: Bool {
        selectedMood != nil && submitState != .submitting && submitState != .success
            && submitState != .rateLimited
    }

    var canSelect: Bool {
        switch submitState {
        case .idle, .error, .geoDenied, .rateLimited: true
        case .submitting, .success: false
        }
    }

    func submit() async {
        guard let mood = selectedMood, submitState != .submitting else { return }
        submitState = .submitting

        let coordinate: CLLocationCoordinate2D
        do {
            coordinate = try await location.currentCoordinate()
        } catch {
            submitState = .geoDenied
            UINotificationFeedbackGenerator().notificationOccurred(.error)
            return
        }

        do {
            let trimmed = note.trimmingCharacters(in: .whitespacesAndNewlines)
            _ = try await UnweltsAPI.shared.submitMood(
                lat: coordinate.latitude,
                lng: coordinate.longitude,
                mood: mood,
                note: trimmed.isEmpty ? nil : trimmed
            )
            submitState = .success
            UINotificationFeedbackGenerator().notificationOccurred(.success)
            await onSuccess?()
            try? await Task.sleep(for: .seconds(3))
            submitState = .idle
            selectedMood = nil
            note = ""
        } catch let error as RateLimitError {
            retryLabel = Self.formatRetryAfter(seconds: error.retryAfterSeconds)
            submitState = .rateLimited
        } catch {
            submitState = .error
        }
    }

    static func formatRetryAfter(seconds: Int) -> String {
        if seconds <= 0 { return "soon" }
        let h = seconds / 3600
        let m = (seconds % 3600) / 60
        if h > 0 { return m > 0 ? "\(h)h \(m)m" : "\(h)h" }
        return "\(max(m, 1))m"
    }
}
