import SwiftUI

struct RootView: View {
    @State private var selectedTab = 0
    var body: some View {
        TabView(selection: $selectedTab) {
            HomeView { selectedTab = 1 }.tabItem { Label("Início", systemImage: "house.fill") }.tag(0)
            CategoryView().tabItem { Label("Categorias", systemImage: "square.grid.2x2.fill") }.tag(1)
            ProgressViewScreen().tabItem { Label("Conquistas", systemImage: "trophy.fill") }.tag(2)
            ProfileView().tabItem { Label("Perfil", systemImage: "person.fill") }.tag(3)
        }.tint(Theme.purple)
    }
}

struct Theme {
    static let lime = Color(red: 0.655, green: 0.957, blue: 0.196)
    static let purple = Color(red: 0.424, green: 0.18, blue: 0.996)
    static let ink = Color(red: 0.09, green: 0.08, blue: 0.18)
    static let soft = Color(red: 0.97, green: 0.973, blue: 0.988)
}

struct Mascot: View {
    var body: some View {
        ZStack {
            Circle().fill(Theme.purple).frame(width: 170, height: 170)
            Circle().fill(Color.white).frame(width: 132, height: 132)
            Image(systemName: "questionmark").font(.system(size: 78, weight: .black)).foregroundStyle(Theme.ink)
            Circle().fill(Theme.lime).frame(width: 66, height: 66).overlay(Text("?").font(.system(size: 42, weight: .black)).foregroundStyle(Theme.ink)).offset(x: 58, y: -58)
        }.accessibilityLabel("Mascote investigador")
    }
}

struct HomeView: View {
    @EnvironmentObject private var progress: ProgressStore
    let play: () -> Void
    var body: some View {
        NavigationStack {
            ZStack { Theme.soft.ignoresSafeArea()
                ScrollView {
                    VStack(alignment: .leading, spacing: 22) {
                        Text("Olá!").font(.system(size: 40, weight: .black, design: .rounded)).foregroundStyle(Theme.ink)
                        Text("Pronto para descobrir quem você pensou?").font(.title3.weight(.semibold)).foregroundStyle(Theme.ink)
                        HStack(spacing: 10) { StatCard(icon: "flame.fill", value: "\(progress.streak)", label: "sequência", color: .pink); StatCard(icon: "circle.fill", value: "\(progress.coins)", label: "moedas", color: .orange); StatCard(icon: "crown.fill", value: "\(progress.points)", label: "pontos", color: Theme.purple) }
                        HStack { Spacer(); Mascot(); Spacer() }.padding(.vertical, 4)
                        Button(action: play) { Label("Jogar agora", systemImage: "arrow.right").font(.title2.bold()).frame(maxWidth: .infinity).padding().background(Theme.purple).foregroundStyle(.white).clipShape(Capsule()) }
                        HStack { Shortcut(icon: "gamecontroller.fill", title: "Continuar desafio"); Shortcut(icon: "trophy.fill", title: "Minhas conquistas"); Shortcut(icon: "calendar", title: "Desafios") }
                    }.padding()
                }
            }.navigationBarHidden(true)
        }
    }
}

struct StatCard: View { let icon: String; let value: String; let label: String; let color: Color; var body: some View { VStack(spacing: 6) { Image(systemName: icon).font(.title2).foregroundStyle(color); Text(value).font(.title3.bold()).foregroundStyle(Theme.ink); Text(label).font(.caption).foregroundStyle(.secondary) }.frame(maxWidth: .infinity).padding(.vertical, 12).background(.white).clipShape(RoundedRectangle(cornerRadius: 18)) } }
struct Shortcut: View { let icon: String; let title: String; var body: some View { VStack(spacing: 8) { Image(systemName: icon).font(.title2).foregroundStyle(Theme.purple); Text(title).font(.caption.weight(.bold)).multilineTextAlignment(.center).foregroundStyle(Theme.ink) }.frame(maxWidth: .infinity).frame(height: 76).background(.white).clipShape(RoundedRectangle(cornerRadius: 16)) } }
