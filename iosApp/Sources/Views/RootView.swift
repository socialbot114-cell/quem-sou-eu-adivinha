import SwiftUI

private enum AppTab: String, CaseIterable, Identifiable {
    case home = "Início"
    case categories = "Jogar"
    case collection = "Coleção"
    case profile = "Perfil"

    var id: String { rawValue }
    var symbol: String {
        switch self {
        case .home: "house.fill"
        case .categories: "sparkles"
        case .collection: "trophy.fill"
        case .profile: "person.fill"
        }
    }
    var identifier: String {
        switch self {
        case .home: "tab.home"
        case .categories: "tab.categories"
        case .collection: "tab.collection"
        case .profile: "tab.profile"
        }
    }
}

struct RootView: View {
    @EnvironmentObject private var progress: ProgressStore
    @AppStorage("onboarding.completed") private var completedOnboarding = false
    @State private var selectedTab = AppTab.home
    @State private var activeCategory: Category?
    @State private var showingOnboarding = false

    var body: some View {
        ZStack {
            switch selectedTab {
            case .home:
                HomeView(
                    play: { selectedTab = .categories },
                    resume: progress.interruptedRound.map { summary in
                        { activeCategory = summary.category }
                    },
                    showCollection: { selectedTab = .collection }
                )
            case .categories:
                CategoryView(onSelect: { activeCategory = $0 })
            case .collection:
                ProgressViewScreen()
            case .profile:
                ProfileView(showOnboarding: { showingOnboarding = true })
            }
        }
        .safeAreaInset(edge: .bottom, spacing: 0) {
            BottomNavigation(selected: $selectedTab)
        }
        .fullScreenCover(item: $activeCategory) { category in
            GameView(category: category, playAnotherCategory: {
                activeCategory = nil
                selectedTab = .categories
            })
        }
        .fullScreenCover(isPresented: Binding(
            get: { !completedOnboarding || showingOnboarding },
            set: { if !$0 { showingOnboarding = false } }
        )) {
            OnboardingView {
                completedOnboarding = true
                showingOnboarding = false
                selectedTab = .categories
            }
        }
    }
}

private struct BottomNavigation: View {
    @Binding var selected: AppTab

    var body: some View {
        HStack(spacing: 4) {
            ForEach(AppTab.allCases) { tab in
                Button {
                    withAnimation(.snappy) { selected = tab }
                } label: {
                    VStack(spacing: 4) {
                        Image(systemName: tab.symbol)
                            .font(.system(size: 19, weight: .bold))
                        Text(tab.rawValue)
                            .font(.caption2.weight(.bold))
                    }
                    .foregroundStyle(selected == tab ? DesignSystem.Palette.violet : .secondary)
                    .frame(maxWidth: .infinity, minHeight: 52)
                    .background {
                        if selected == tab {
                            Capsule().fill(DesignSystem.Palette.violet.opacity(0.1)).padding(.horizontal, 5)
                        }
                    }
                }
                .buttonStyle(.plain)
                .accessibilityAddTraits(selected == tab ? .isSelected : [])
                .accessibilityIdentifier(tab.identifier)
            }
        }
        .padding(.horizontal, 10)
        .padding(.top, 8)
        .background(.ultraThinMaterial)
        .overlay(alignment: .top) { Divider().opacity(0.45) }
    }
}

struct HomeView: View {
    @EnvironmentObject private var progress: ProgressStore
    let play: () -> Void
    let resume: (() -> Void)?
    let showCollection: () -> Void

    var body: some View {
        NavigationStack {
            DSDecorativeBackground {
                ScrollView {
                    VStack(alignment: .leading, spacing: 22) {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("QUEM SOU EU?")
                                .font(.caption.weight(.black))
                                .tracking(2.2)
                                .foregroundStyle(DesignSystem.Palette.violet)
                            Text("Sua próxima investigação começa aqui.")
                                .font(.system(.largeTitle, design: .rounded, weight: .black))
                                .foregroundStyle(DesignSystem.Palette.ink)
                        }

                        HStack(spacing: 8) {
                            DSStatChip(asset: .streakFlame, value: "\(progress.streak)", label: "sequência")
                            DSStatChip(asset: .achievementTrophy, value: "\(progress.wins)", label: "acertos")
                        }

                        VStack(spacing: 8) {
                            DSMascotView(size: 238)
                            Text("Pense em alguém. Eu sigo as pistas!")
                                .font(.title3.weight(.bold))
                                .multilineTextAlignment(.center)
                                .foregroundStyle(DesignSystem.Palette.ink)
                        }
                        .frame(maxWidth: .infinity)
                        .dsCard(padding: 18)

                        Button(action: play) {
                            Label("Jogar agora", systemImage: "arrow.right")
                        }
                        .buttonStyle(PrimaryButtonStyle())
                        .accessibilityIdentifier("home.play")

                        if let resume {
                            Button(action: resume) {
                                Label("Continuar investigação", systemImage: "arrow.clockwise")
                            }
                            .buttonStyle(SecondaryButtonStyle())
                        }

                        Button(action: showCollection) {
                            HStack(spacing: 14) {
                                Image(DesignSystem.Asset.achievementTrophy.rawValue)
                                    .resizable().scaledToFit().frame(width: 54, height: 54)
                                VStack(alignment: .leading, spacing: 3) {
                                    Text("Sua coleção").font(.headline.weight(.bold))
                                    Text("\(progress.discoveredPersonIDs.count) personalidades descobertas")
                                        .font(.subheadline).foregroundStyle(.secondary)
                                }
                                Spacer()
                                Image(systemName: "chevron.right").foregroundStyle(.secondary)
                            }
                            .foregroundStyle(DesignSystem.Palette.ink)
                            .dsCard()
                        }
                        .buttonStyle(.plain)
                    }
                    .frame(maxWidth: DesignSystem.Metric.contentMaxWidth)
                    .padding(20)
                    .frame(maxWidth: .infinity)
                }
            }
            .toolbar(.hidden, for: .navigationBar)
        }
    }
}
