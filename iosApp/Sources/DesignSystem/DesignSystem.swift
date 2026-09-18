import SwiftUI
import UIKit

enum DesignSystem {
    enum Palette {
        static let violet = Color(red: 0.39, green: 0.12, blue: 0.94)
        static let violetLight = Color(red: 0.64, green: 0.37, blue: 1.00)
        static let lime = Color(red: 0.68, green: 0.96, blue: 0.16)
        static let gold = Color(red: 1.00, green: 0.72, blue: 0.08)
        static let coral = Color(red: 1.00, green: 0.25, blue: 0.43)
        static let ink = Color(uiColor: .label)
        static let canvas = Color(uiColor: .systemGroupedBackground)
        static let surface = Color(uiColor: .secondarySystemBackground)
        static let hairline = Color.primary.opacity(0.10)
    }

    enum Gradient {
        static let primary = LinearGradient(
            colors: [Palette.violetLight, Palette.violet],
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )

        static let celebration = LinearGradient(
            colors: [Palette.gold, Palette.lime],
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )

        static let background = LinearGradient(
            colors: [Palette.canvas, Palette.violet.opacity(0.09)],
            startPoint: .top,
            endPoint: .bottomTrailing
        )
    }

    enum Metric {
        static let spacingXS: CGFloat = 6
        static let spacingS: CGFloat = 10
        static let spacingM: CGFloat = 16
        static let spacingL: CGFloat = 24
        static let spacingXL: CGFloat = 32
        static let cornerRadius: CGFloat = 22
        static let controlHeight: CGFloat = 52
        static let contentMaxWidth: CGFloat = 720
    }

    enum Asset: String {
        case mascotPrincess = "mascot_princess"
        case feedbackSuccess = "feedback_success"
        case feedbackError = "feedback_error"
        case hintIdea = "hint_idea"
        case achievementTrophy = "achievement_trophy"
        case streakFlame = "streak_flame"
    }
}

struct DSCardModifier: ViewModifier {
    var padding: CGFloat = DesignSystem.Metric.spacingM

    func body(content: Content) -> some View {
        content
            .padding(padding)
            .background(DesignSystem.Palette.surface, in: RoundedRectangle(cornerRadius: DesignSystem.Metric.cornerRadius, style: .continuous))
            .overlay {
                RoundedRectangle(cornerRadius: DesignSystem.Metric.cornerRadius, style: .continuous)
                    .stroke(DesignSystem.Palette.hairline, lineWidth: 1)
            }
            .shadow(color: .black.opacity(0.08), radius: 18, y: 8)
    }
}

extension View {
    func dsCard(padding: CGFloat = DesignSystem.Metric.spacingM) -> some View {
        modifier(DSCardModifier(padding: padding))
    }
}

struct PrimaryButtonStyle: ButtonStyle {
    @Environment(\.isEnabled) private var isEnabled
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.headline.weight(.bold))
            .frame(maxWidth: .infinity, minHeight: DesignSystem.Metric.controlHeight)
            .padding(.horizontal, DesignSystem.Metric.spacingL)
            .foregroundStyle(.white)
            .background(DesignSystem.Gradient.primary, in: Capsule())
            .opacity(isEnabled ? (configuration.isPressed ? 0.86 : 1) : 0.45)
            .scaleEffect(configuration.isPressed && !reduceMotion ? 0.98 : 1)
            .animation(reduceMotion ? nil : .snappy(duration: 0.18), value: configuration.isPressed)
            .contentShape(Capsule())
    }
}

struct SecondaryButtonStyle: ButtonStyle {
    @Environment(\.isEnabled) private var isEnabled
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.headline.weight(.bold))
            .frame(maxWidth: .infinity, minHeight: DesignSystem.Metric.controlHeight)
            .padding(.horizontal, DesignSystem.Metric.spacingL)
            .foregroundStyle(DesignSystem.Palette.violet)
            .background(DesignSystem.Palette.surface, in: Capsule())
            .overlay { Capsule().stroke(DesignSystem.Palette.violet.opacity(0.45), lineWidth: 1.5) }
            .opacity(isEnabled ? (configuration.isPressed ? 0.76 : 1) : 0.45)
            .scaleEffect(configuration.isPressed && !reduceMotion ? 0.98 : 1)
            .animation(reduceMotion ? nil : .snappy(duration: 0.18), value: configuration.isPressed)
            .contentShape(Capsule())
    }
}

struct DSStatChip: View {
    let asset: DesignSystem.Asset
    let value: String
    let label: String

    @ScaledMetric(relativeTo: .body) private var iconSize = 34.0

    var body: some View {
        HStack(spacing: DesignSystem.Metric.spacingS) {
            Image(asset.rawValue)
                .resizable()
                .scaledToFit()
                .frame(width: iconSize, height: iconSize)
                .accessibilityHidden(true)

            VStack(alignment: .leading, spacing: 1) {
                Text(value)
                    .font(.headline.weight(.bold))
                    .foregroundStyle(DesignSystem.Palette.ink)
                Text(label)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .fixedSize(horizontal: false, vertical: true)
        .padding(.horizontal, DesignSystem.Metric.spacingM)
        .padding(.vertical, DesignSystem.Metric.spacingS)
        .background(.thinMaterial, in: Capsule())
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("\(label): \(value)")
    }
}

struct DSDecorativeBackground<Content: View>: View {
    let content: Content

    init(@ViewBuilder content: () -> Content) {
        self.content = content()
    }

    var body: some View {
        ZStack {
            DesignSystem.Gradient.background
                .ignoresSafeArea()

            GeometryReader { proxy in
                Circle()
                    .fill(DesignSystem.Palette.lime.opacity(0.18))
                    .frame(width: proxy.size.width * 0.75)
                    .blur(radius: 48)
                    .offset(x: proxy.size.width * 0.48, y: -proxy.size.height * 0.08)

                Circle()
                    .fill(DesignSystem.Palette.violet.opacity(0.13))
                    .frame(width: proxy.size.width * 0.9)
                    .blur(radius: 64)
                    .offset(x: -proxy.size.width * 0.35, y: proxy.size.height * 0.68)
            }
            .ignoresSafeArea()
            .accessibilityHidden(true)

            content
        }
    }
}

struct DSMascotView: View {
    var size: CGFloat = 220
    var accessibilityLabel = "Princesa investigadora, mascote do jogo"

    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var isFloating = false

    var body: some View {
        Image(DesignSystem.Asset.mascotPrincess.rawValue)
            .resizable()
            .scaledToFit()
            .frame(width: size, height: size)
            .offset(y: isFloating && !reduceMotion ? -6 : 0)
            .animation(
                reduceMotion ? nil : .easeInOut(duration: 2.2).repeatForever(autoreverses: true),
                value: isFloating
            )
            .accessibilityLabel(accessibilityLabel)
            .onAppear { isFloating = !reduceMotion }
            .onChange(of: reduceMotion) { _, newValue in
                isFloating = !newValue
            }
    }
}
