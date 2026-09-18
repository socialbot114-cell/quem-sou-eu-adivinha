import SwiftUI
import UIKit

struct CharacterPortrait: View {
    let person: Person
    var size: CGFloat = 148

    private var image: UIImage? {
        guard let imageName = person.imageName,
              let url = Bundle.main.url(forResource: imageName, withExtension: nil, subdirectory: "Characters") else { return nil }
        return UIImage(contentsOfFile: url.path)
    }

    var body: some View {
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
                        .foregroundStyle(DesignSystem.Palette.violet)
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
