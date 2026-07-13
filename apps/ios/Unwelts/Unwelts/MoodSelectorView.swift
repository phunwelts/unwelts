//
//  MoodSelectorView.swift
//  Unwelts
//
//  Port of MoodSelector.tsx: YOUR SIGNAL caption, 2-column mood grid with
//  glow-on-select, note field with counter, stateful send button, success
//  ring. Haptics added (mobile-native interactivity budget).
//

import SwiftUI

struct MoodSelectorView: View {
    @Bindable var viewModel: SubmitViewModel

    @State private var successRingScale: CGFloat = 1
    @State private var successRingOpacity: Double = 0

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("YOUR SIGNAL")
                .font(Theme.mono(10))
                .tracking(4)
                .foregroundStyle(Theme.muted)

            moodGrid

            noteField

            sendButton

            statusMessage
        }
    }

    private var moodGrid: some View {
        LazyVGrid(columns: [GridItem(.flexible(), spacing: 5), GridItem(.flexible())], spacing: 5) {
            ForEach(MoodType.uiOrder, id: \.self) { mood in
                let active = viewModel.selectedMood == mood
                Button {
                    guard viewModel.canSelect else { return }
                    UIImpactFeedbackGenerator(style: .light).impactOccurred()
                    viewModel.selectedMood = active ? nil : mood
                } label: {
                    Text(mood.label)
                        .font(Theme.mono(11))
                        .tracking(1.5)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 10)
                        .background(Color.white.opacity(0.015))
                        .foregroundStyle(active ? mood.color : Theme.text)
                        .overlay(
                            RoundedRectangle(cornerRadius: 4)
                                .stroke(active ? mood.color : Color.white.opacity(0.05), lineWidth: 1)
                        )
                        .shadow(color: active ? mood.color.opacity(0.33) : .clear, radius: 4)
                }
                .buttonStyle(.plain)
                .disabled(viewModel.submitState == .submitting)
                .animation(.easeOut(duration: 0.15), value: active)
            }
        }
    }

    private var noteField: some View {
        VStack(alignment: .trailing, spacing: 3) {
            TextField("add a note… (optional)", text: $viewModel.note, axis: .vertical)
                .lineLimit(2...2)
                .font(Theme.mono(11))
                .foregroundStyle(Theme.text)
                .padding(8)
                .background(Color.white.opacity(0.015))
                .overlay(
                    RoundedRectangle(cornerRadius: 4)
                        .stroke(Color.white.opacity(0.05), lineWidth: 1)
                )
                .disabled(viewModel.submitState == .submitting)
                .onChange(of: viewModel.note) { _, newValue in
                    if newValue.count > 280 { viewModel.note = String(newValue.prefix(280)) }
                }

            Text("\(viewModel.note.count)/280")
                .font(Theme.mono(9))
                .foregroundStyle(viewModel.note.count > 250 ? Theme.warn : Color(hex: 0x444444))
        }
    }

    private var sendButton: some View {
        Button {
            Task { await viewModel.submit() }
        } label: {
            Text(sendLabel)
                .font(Theme.mono(11))
                .tracking(2)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 10)
                .background(viewModel.canSend ? (viewModel.selectedMood?.color.opacity(0.07) ?? .clear) : .clear)
                .foregroundStyle(sendColor)
                .overlay(
                    RoundedRectangle(cornerRadius: 4)
                        .stroke(
                            viewModel.canSend
                                ? (viewModel.selectedMood?.color.opacity(0.27) ?? Theme.border)
                                : Theme.border,
                            lineWidth: 1
                        )
                )
                .overlay {
                    if viewModel.submitState == .success, let mood = viewModel.selectedMood {
                        RoundedRectangle(cornerRadius: 4)
                            .stroke(mood.color, lineWidth: 1)
                            .scaleEffect(successRingScale)
                            .opacity(successRingOpacity)
                            .onAppear {
                                successRingScale = 1
                                successRingOpacity = 0.7
                                withAnimation(.easeOut(duration: 0.75)) {
                                    successRingScale = 1.9
                                    successRingOpacity = 0
                                }
                            }
                    }
                }
        }
        .buttonStyle(.plain)
        .disabled(!viewModel.canSend)
        .animation(.easeOut(duration: 0.2), value: viewModel.canSend)
    }

    private var sendLabel: String {
        switch viewModel.submitState {
        case .submitting: "SENDING…"
        case .success: "SIGNAL LIVE ✓"
        case .geoDenied: "LOCATION REQUIRED"
        case .rateLimited: "LIMIT REACHED"
        case .error: "ERROR — TRY AGAIN"
        case .idle: "SEND TO MAP →"
        }
    }

    private var sendColor: Color {
        if viewModel.canSend { return Theme.text }
        switch viewModel.submitState {
        case .success: return Theme.ok
        case .geoDenied, .error: return Theme.danger
        default: return Theme.text
        }
    }

    @ViewBuilder
    private var statusMessage: some View {
        switch viewModel.submitState {
        case .rateLimited:
            Text("try again in \(viewModel.retryLabel)")
                .font(Theme.mono(9))
                .tracking(1)
                .foregroundStyle(viewModel.selectedMood?.color ?? Theme.muted)
                .frame(maxWidth: .infinity)
        case .geoDenied:
            Text("Allow location access to send your signal.")
                .font(Theme.mono(9))
                .foregroundStyle(Theme.danger)
        case .error:
            Text("Something went wrong. Please try again.")
                .font(Theme.mono(9))
                .foregroundStyle(Theme.danger)
        default:
            EmptyView()
        }
    }
}
