import SwiftUI

struct OnboardingView: View {
    let finish: () -> Void
    @State private var page = 0

    var body: some View {
        DSDecorativeBackground {
            VStack(spacing: DesignSystem.Metric.spacingL) {
                HStack {
                    Spacer()
                    Button("Pular", action: finish)
                        .font(.subheadline.weight(.bold))
                        .foregroundStyle(DesignSystem.Palette.violet)
                }

                Spacer(minLength: 8)
                DSMascotView(size: 280)

                VStack(spacing: 12) {
                    Text(page == 0 ? "Uma missão para você" : "Pense em alguém")
                        .font(.system(.largeTitle, design: .rounded, weight: .black))
                        .multilineTextAlignment(.center)
                    Text(page == 0
                         ? "Eu sou a Princesa Detetive. Você escolhe uma pessoa e eu tento descobrir quem é."
                         : "Guarde o nome em segredo, escolha o universo da pessoa e responda às minhas pistas.")
                        .font(.title3.weight(.medium))
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                        .lineSpacing(4)
                }
                .accessibilityElement(children: .combine)

                Spacer()

                Button {
                    if page == 0 {
                        withAnimation(.snappy) { page = 1 }
                    } else {
                        finish()
                    }
                } label: {
                    Label(page == 0 ? "Conhecer a missão" : "Escolher categoria", systemImage: "arrow.right")
                }
                .buttonStyle(PrimaryButtonStyle())
                .accessibilityHint(page == 0 ? "Mostra como começar" : "Abre as categorias do jogo")

                HStack(spacing: 8) {
                    Capsule().fill(DesignSystem.Palette.violet).frame(width: page == 0 ? 24 : 8, height: 8)
                    Capsule().fill(DesignSystem.Palette.violet.opacity(page == 1 ? 1 : 0.25)).frame(width: page == 1 ? 24 : 8, height: 8)
                }
                .animation(.snappy, value: page)
                .accessibilityLabel("Etapa \(page + 1) de 2")
            }
            .padding(24)
            .frame(maxWidth: 620)
        }
        .interactiveDismissDisabled()
    }
}
