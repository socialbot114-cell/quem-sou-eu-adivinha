import SwiftUI

struct CategoryView: View {
    private let categories = Category.allCases.filter { $0 != .all }
    var body: some View {
        NavigationStack { ScrollView { VStack(alignment: .leading, spacing: 18) {
            Text("Escolha uma categoria").font(.largeTitle.bold()).foregroundStyle(Theme.ink)
            Text("Pense em alguém e eu descubro!").foregroundStyle(.secondary)
            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 14) {
                ForEach(categories) { category in NavigationLink(destination: GameView(category: category)) { CategoryCard(category: category) }.buttonStyle(.plain) }
            }
            NavigationLink(destination: GameView(category: .all)) { CategoryCard(category: .all) }.buttonStyle(.plain)
        }.padding() }.background(Theme.soft.ignoresSafeArea()).navigationTitle("Categorias") }
    }
}

struct CategoryCard: View {
    let category: Category
    var body: some View { VStack(spacing: 12) { Image(systemName: category.symbol).font(.system(size: 34, weight: .bold)).foregroundStyle(Theme.ink); Text(category.rawValue).font(.headline.weight(.bold)).multilineTextAlignment(.center).foregroundStyle(Theme.ink) }.frame(maxWidth: .infinity).frame(minHeight: 125).padding(10).background(category == .all ? Theme.lime : .white).clipShape(RoundedRectangle(cornerRadius: 22)).shadow(color: .black.opacity(0.05), radius: 8, y: 4) }
}

struct GameView: View {
    let category: Category
    @Environment(\.dismiss) private var dismiss
    @EnvironmentObject private var progress: ProgressStore
    @State private var engine: GameEngine
    @State private var question: Question?
    @State private var questionNumber = 0
    @State private var result: Person?
    @State private var finished = false
    @State private var guessedWrong = false

    init(category: Category) {
        self.category = category
        let base = KnowledgeStore.shared.base
        let filtered = category == .all ? base.people : base.people.filter { $0.categories.contains(category) }
        _engine = State(initialValue: GameEngine(people: filtered, questions: base.questions))
    }

    var body: some View {
        ZStack { Theme.ink.ignoresSafeArea()
            VStack(spacing: 18) {
                HStack { Button { dismiss() } label: { Image(systemName: "xmark").font(.headline).foregroundStyle(.white).padding(12).background(.white.opacity(0.12)).clipShape(Circle()) }; Spacer(); Text("Pergunta \(min(questionNumber + 1, 20)) de 20").foregroundStyle(.white.opacity(0.8)).font(.subheadline.bold()) }.padding(.horizontal)
                ProgressView(value: Double(questionNumber), total: 20).tint(Theme.lime).padding(.horizontal)
                Spacer()
                if let question, !finished { QuestionCard(question: question) { answer in respond(answer, to: question) } }
                else if finished, let result { ResultCard(person: result, questions: questionNumber, guessedWrong: guessedWrong) { dismiss() } }
                Spacer()
                if !finished { Text("Dica: pense em alguém conhecido").foregroundStyle(.white.opacity(0.65)).font(.footnote) }
            }.padding(.vertical)
        }.navigationBarBackButtonHidden(true).onAppear { if question == nil { advance() } }
    }

    private func respond(_ answer: Answer, to question: Question) { engine.apply(answer, to: question); questionNumber += 1; if engine.confidence > 0.7 || questionNumber >= 20 { result = engine.bestGuess; finished = true; if engine.confidence > 0.7 { progress.recordWin(questions: questionNumber) } } else { advance() } }
    private func advance() { question = engine.nextQuestion() }
}

struct QuestionCard: View {
    let question: Question; let answer: (Answer) -> Void
    var body: some View { VStack(spacing: 20) { Mascot().scaleEffect(0.5).frame(height: 90); Text(question.text).font(.system(size: 30, weight: .black, design: .rounded)).multilineTextAlignment(.center).foregroundStyle(Theme.ink).padding(.horizontal); VStack(spacing: 10) { ForEach(Answer.allCases) { item in Button { answer(item) } label: { Text(item.rawValue).font(.headline.weight(.bold)).frame(maxWidth: .infinity).padding(.vertical, 14).background(color(for: item)).foregroundStyle(Theme.ink).clipShape(Capsule()) } } }.padding(.horizontal) }.padding(.vertical, 24).background(.white).clipShape(RoundedRectangle(cornerRadius: 28)).padding(.horizontal) }
    private func color(for answer: Answer) -> Color { switch answer { case .yes: Theme.lime; case .probablyYes: Color.green.opacity(0.25); case .unknown: Color.gray.opacity(0.18); case .probablyNo: Color.pink.opacity(0.18); case .no: Color.red.opacity(0.24) } }
}

struct ResultCard: View {
    let person: Person; let questions: Int; let guessedWrong: Bool; let restart: () -> Void
    var body: some View { VStack(spacing: 18) { Text("Acho que descobri!").font(.title2.bold()).foregroundStyle(Theme.ink); Image(systemName: person.avatarSymbol).font(.system(size: 72)).foregroundStyle(Theme.purple).padding(25).background(Theme.lime).clipShape(Circle()); Text(person.name).font(.system(size: 34, weight: .black, design: .rounded)).foregroundStyle(Theme.ink); Text("\(person.country) • \(person.profession)").foregroundStyle(.secondary); Text("Descobri em \(questions) perguntas").font(.headline).foregroundStyle(Theme.ink); Button("Sim, acertou!") { restart() }.font(.headline.bold()).frame(maxWidth: .infinity).padding().background(Theme.purple).foregroundStyle(.white).clipShape(Capsule()) }.padding(28).background(.white).clipShape(RoundedRectangle(cornerRadius: 28)).padding(.horizontal) }
}

struct ProgressViewScreen: View { @EnvironmentObject private var progress: ProgressStore; var body: some View { NavigationStack { VStack(spacing: 20) { Text("Meu progresso").font(.largeTitle.bold()).foregroundStyle(Theme.ink); HStack { StatCard(icon: "flame.fill", value: "\(progress.streak)", label: "sequência", color: .pink); StatCard(icon: "crown.fill", value: "\(progress.points)", label: "pontos", color: Theme.purple) }; Spacer() }.padding().background(Theme.soft.ignoresSafeArea()).navigationTitle("Conquistas") } } }
struct ProfileView: View { var body: some View { NavigationStack { List { Section("Sobre o jogo") { Label("Funciona sem internet", systemImage: "wifi.slash"); Label("Nenhum dado coletado", systemImage: "lock.shield.fill"); NavigationLink("Privacidade") { Text("Quem Sou Eu? Adivinha não coleta, transmite ou vende dados pessoais. Todo o progresso fica neste aparelho.").padding() } } Section("Conteúdo") { Text("Base inicial com personalidades e fontes editoriais."); Text("Versão 1.0") } }.navigationTitle("Perfil") } } }
