//
//  SignalGate.swift
//  Unwelts
//
//  The core mechanic: the world map is only visible while your own signal
//  is live (the server's 4h rate-limit window). Sending unlocks it; expiry
//  locks it again — the reason to come back and send another.
//
//  Persisted in UserDefaults. A 429 also unlocks: it proves a signal is
//  already live server-side (e.g. fresh reinstall), with the exact TTL.
//

import Foundation
import Observation

@Observable
@MainActor
final class SignalGate {
    // Mirrors the server's RATE_LIMIT_WINDOW_HOURS.
    static let windowHours = 4

    private static let storageKey = "signalActiveUntil"

    private(set) var activeUntil: Date?

    init() {
        activeUntil = UserDefaults.standard.object(forKey: Self.storageKey) as? Date
    }

    func isActive(at date: Date = .now) -> Bool {
        guard let activeUntil else { return false }
        return activeUntil > date
    }

    func activate(until date: Date) {
        activeUntil = date
        UserDefaults.standard.set(date, forKey: Self.storageKey)
    }

    func activateForFullWindow() {
        activate(until: .now.addingTimeInterval(TimeInterval(Self.windowHours) * 3600))
    }
}
