import SwiftUI
import UIKit

struct CharacterPortrait: View {
    let person: Person
    var size: CGFloat = 148

    private var image: UIImage? { loadCharacterImage(person.imageName) }

    var body: some View {
        if person.categories.contains(.animals) {
            AnimalPortrait(person: person, size: size)
        } else {
            Group {
                if let image {
                    Image(uiImage: image)
                        .resizable()
                        .scaledToFill()
                } else {
                    ZStack {
                        DesignSystem.Gradient.celebration
                        Image(systemName: person.avatarSymbol)
                            .font(.system(size: size * 0.35, weight: .bold))
                            .foregroundStyle(DesignSystem.Palette.accent)
                    }
                }
            }
            .frame(width: size, height: size)
            .clipShape(RoundedRectangle(cornerRadius: size * 0.25, style: .continuous))
            .overlay {
                RoundedRectangle(cornerRadius: size * 0.25, style: .continuous)
                    .stroke(.white.opacity(0.8), lineWidth: 3)
            }
            .shadow(color: DesignSystem.Palette.violet.opacity(0.22), radius: 18, y: 10)
            .accessibilityLabel("Retrato de \(person.name)")
        }
    }
}

/// Animals are drawn without a card: a transparent illustration floats over a soft shadow.
/// Without an illustration, the species emoji is shown; the SF Symbol is the last resort.
private struct AnimalPortrait: View {
    let person: Person
    let size: CGFloat

    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var isMoving = false

    var body: some View {
        ZStack {
            Ellipse()
                .fill(DesignSystem.Palette.violet.opacity(0.18))
                .frame(width: size * 0.56, height: size * 0.12)
                .blur(radius: 5)
                .offset(y: size * 0.40)
                .scaleEffect(isMoving && !reduceMotion ? 0.9 : 1)

            artwork
                .frame(width: size, height: size)
                .offset(y: isMoving && !reduceMotion ? -size * 0.05 : 0)
                .rotationEffect(.degrees(isMoving && !reduceMotion ? 2.5 : -2.5))
        }
        .frame(width: size, height: size)
        .animation(reduceMotion ? nil : .easeInOut(duration: 1.8).repeatForever(autoreverses: true), value: isMoving)
        .onAppear { isMoving = !reduceMotion }
        .onChange(of: reduceMotion) { _, newValue in isMoving = !newValue }
        .accessibilityLabel("Ilustração de \(person.name)")
    }

    @ViewBuilder private var artwork: some View {
        if let image = loadCharacterImage(person.imageName) {
            Image(uiImage: image)
                .resizable()
                .scaledToFit()
        } else if let emoji = person.emoji {
            Text(emoji)
                .font(.system(size: size * 0.66))
        } else {
            Image(systemName: person.avatarSymbol)
                .font(.system(size: size * 0.5, weight: .bold))
                .foregroundStyle(DesignSystem.Palette.accent)
        }
    }
}

private func loadCharacterImage(_ imageName: String?) -> UIImage? {
    guard let imageName,
          let url = Bundle.main.url(forResource: imageName, withExtension: nil, subdirectory: "Characters") else { return nil }
    return UIImage(contentsOfFile: url.path)
}
