//
//  UnweltsAPI.swift
//  Unwelts
//
//  Thin wrapper around the OpenAPI-generated client. All business logic
//  (fingerprinting, fuzzing, rate limiting) is server-side; this stays dumb.
//

import Foundation
import OpenAPIRuntime
import OpenAPIURLSession

struct RateLimitError: Error {
    let retryAfterSeconds: Int
}

struct UnweltsAPI {
    static let shared = UnweltsAPI()

    private let client: Client

    // Debug builds develop against the local stack (docker compose up api)
    // so testing never writes into the production database; Release builds
    // ship pointing at prod. UNWELTS_API_URL (scheme env var) overrides both,
    // e.g. for Debug on a physical device via the Mac's LAN IP.
    static var defaultServerURL: URL {
        if let override = ProcessInfo.processInfo.environment["UNWELTS_API_URL"],
            let url = URL(string: override)
        {
            return url
        }
        #if DEBUG
            return URL(string: "http://localhost:8000")!
        #else
            return URL(string: "https://unwelts-api.fly.dev")!
        #endif
    }

    init(serverURL: URL = UnweltsAPI.defaultServerURL) {
        // FastAPI emits fractional-second timestamps (…T20:02:07.715719Z);
        // the default .iso8601 transcoder rejects them.
        client = Client(
            serverURL: serverURL,
            configuration: Configuration(dateTranscoder: .iso8601WithFractionalSeconds),
            transport: URLSessionTransport()
        )
    }

    func submitMood(lat: Double, lng: Double, mood: MoodType, note: String?) async throws
        -> Components.Schemas.MoodResponse
    {
        let response = try await client.submitMoodApiV1MoodsPost(
            body: .json(.init(lat: lat, lng: lng, moodType: mood, note: note))
        )
        switch response {
        case .created(let created):
            return try created.body.json
        case .undocumented(statusCode: 429, let payload):
            throw RateLimitError(retryAfterSeconds: try await Self.retryAfter(from: payload))
        case .unprocessableContent, .undocumented:
            throw URLError(.badServerResponse)
        }
    }

    func recentMoods(limit: Int = 100) async throws -> Components.Schemas.RecentMoodsResponse {
        let response = try await client.getRecentMoodsApiV1MoodsRecentGet(
            query: .init(limit: limit)
        )
        return try response.ok.body.json
    }

    func map(resolution: Int = 5) async throws -> Components.Schemas.MapResponse {
        let response = try await client.getMapApiV1MapGet(query: .init(resolution: resolution))
        return try response.ok.body.json
    }

    // 429 isn't in the OpenAPI schema, so it arrives as an undocumented payload.
    // Fingerprint limit: {"detail": {"message": ..., "retry_after_seconds": n}}
    // IP limit: {"detail": "Too many requests..."} → no countdown, report 60s.
    private static func retryAfter(from payload: UndocumentedPayload) async throws -> Int {
        guard let body = payload.body else { return 60 }
        let data = try await Data(collecting: body, upTo: 64 * 1024)
        let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any]
        let detail = json?["detail"] as? [String: Any]
        return detail?["retry_after_seconds"] as? Int ?? 60
    }
}
