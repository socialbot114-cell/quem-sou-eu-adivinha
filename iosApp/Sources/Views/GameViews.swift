import SwiftUI

struct CategoryView: View {
    private let base = KnowledgeStore.shared.base

    private var categories: [Category] {
        Category.allCases.filter { category in
            category != .all && base.people.filter { $0.categories.contains(category) }.count >= 3
        }
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 18) {
                    Text("Escolha uma categoria").font(.largeTitle.bold()).foregroundStyle(Theme.ink).accessibilityAddTraits(.isHeader)
                    Text("Pense em alguém e eu descubro!").foregroundStyle(.secondary)
                    LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 14) {
                        ForEach(categories) { category in
                            NavigationLink(destination: GameView(category: category)) { CategoryCard(category: category) }.buttonStyle(.plain)
                        }
                    }
                    NavigationLink(destination: GameView(category: .all)) { CategoryCard(category: .all) }.buttonStyle(.plain)
                }
                .padding()
            }
            .background(Theme.soft.ignoresSafeArea())
            .navigationTitle("Categorias")
        }
    }
}

struct CategoryCard: View {
    let category: Category

    var body: some View {
        VStack(spacing: 12) {
            Image(systemName: category.symbol).font(.system(size: 34, weight: .bold)).foregroundStyle(Theme.ink)
            Text(category.rawValue).font(.headline.weight(.bold)).multilineTextAlignment(.center).foregroundStyle(Theme.ink)
        }
        .frame(maxWidth: .infinity).frame(minHeight: 125).padding(10)
        .background(category == .all ? Theme.lime : .white)
        .clipShape(RoundedRectangle(cornerRadius: 22))
        .shadow(color: .black.opacity(0.05), radius: 8, y: 4)
        .accessibilityElement(children: .combine)
    }
}

private enum GamePhase {
    case asking
    case confirming(Person)
    case won(Person)
    case lost(Person?)
    case unavailable
}

struct GameView: View {
    let category: Category
    @Environment(\.dismiss) private var dismiss
    @EnvironmentObject private var progress: ProgressStore
    @State private var engine: GameEngine
    @State private var question: Question?
    @State private var questionNumber = 0
    @State private var phase = GamePhase.asking
    @State private var recordedPlay = false

    init(category: Category) {
        self.category = category
        let base = KnowledgeStore.shared.base
        let people = category == .all ? base.people : base.people.filter { $0.categories.contains(category) }
        let questions = base.questions.filter { $0.categories.contains(.all) || $0.categories.contains(category) || category == .all }
        _engine = State(initialValue: GameEngine(people: people, questions: questions))
    }

    private var questionLimit: Int { min(10, Set(engine.questions.map(\.attribute)).count) }

    var body: some View {
        ZStack {
            Theme.ink.ignoresSafeArea()
            ScrollView {
                VStack(spacing: 18) {
                    header
                    if let error = KnowledgeStore.shared.loadError {
                        Text(error).foregroundStyle(.white).multilineTextAlignment(.center).padding()
                    } else {
                        content
                    }
                }
                .frame(maxWidth: 700)
                .padding(.horizontal)
                .padding(.vertical)
                .frame(maxWidth: .infinity)
            }
        }
        .navigationBarBackButtonHidden(true)
        .onAppear {
            guard !recordedPlay else { return }
            recordedPlay = true
            progress.recordPlayed()
            advance()
        }
    }

    private var header: some View {
        VStack(spacing: 12) {
            HStack {
                Button { dismiss() } label: { Image(systemName: "xmark").font(.headline).foregroundStyle(.white).padding(12).background(.white.opacity(0.12)).clipShape(Circle()) }
                    .accessibilityLabel("Sair da partida")
                Spacer()
                Text("Pergunta \(min(questionNumber + 1, questionLimit)) de \(questionLimit)").foregroundStyle(.white.opacity(0.8)).font(.subheadline.bold())
            }
            ProgressView(value: Double(questionNumber), total: Double(max(questionLimit, 1)))
                .tint(Theme.lime)
                .accessibilityLabel("Progresso da partida")
                .accessibilityValue("\(questionNumber) de \(questionLimit) perguntas")
        }
    }

    @ViewBuilder private var content: some View {
        switch phase {
        case .asking:
            if let question {
                QuestionCard(question: question) { respond($0, to: question) }
                Text("Responda como preferir. “Não sei” não altera o palpite.").foregroundStyle(.white.opacity(0.65)).font(.footnote).multilineTextAlignment(.center)
            } else {
                ProgressView("Preparando perguntas…").tint(Theme.lime).foregroundStyle(.white)
            }
        case .confirming(let person):
            ResultCard(person: person, questions: questionNumber, mode: .confirmation, confirm: confirmGuess, reject: { reject(person) })
        case .won(let person):
            ResultCard(person: person, questions: questionNumber, mode: .won, confirm: dismiss, reject: nil)
        case .lost(let person):
            ResultCard(person: person, questions: questionNumber, mode: .lost, confirm: dismiss, reject: nil)
        case .unavailable:
            UnavailableCard { dismiss() }
        }
    }

    private func respond(_ answer: Answer, to question: Question) {
        engine.apply(answer, to: question)
        questionNumber += 1
        if questionNumber >= 3, engine.confidence >= 0.7 {
            presentBestGuess()
        } else if questionNumber >= questionLimit {
            presentBestGuess()
        } else {
            advance()
        }
    }

    private func advance() {
        guard !engine.people.isEmpty, questionLimit > 0 else { phase = .unavailable; return }
        question = engine.nextQuestion()
        if question == nil { presentBestGuess() }
    }

    private func presentBestGuess() {
        guard let guess = engine.bestGuess else { phase = .unavailable; return }
        phase = .confirming(guess)
    }

    private func confirmGuess() {
        guard case .confirming(let person) = phase else { return }
        progress.recordWin(questions: questionNumber)
        phase = .won(person)
    }

    private func reject(_ person: Person) {
        engine.reject(person)
        if questionNumber >= questionLimit || engine.bestGuess == nil {
            phase = .lost(engine.bestGuess)
        } else {
            phase = .asking
            advance()
        }
    }
}

struct QuestionCard: View {
    let question: Question
    let answer: (Answer) -> Void

    var body: some View {
        VStack(spacing: 20) {
            Mascot().scaleEffect(0.5).frame(height: 90).accessibilityHidden(true)
            Text(question.text).font(.system(.title, design: .rounded).weight(.black)).multilineTextAlignment(.center).foregroundStyle(Theme.ink).padding(.horizontal).accessibilityAddTraits(.isHeader)
            VStack(spacing: 10) {
                ForEach(Answer.allCases) { item in
                    Button { answer(item) } label: { Text(item.rawValue).font(.headline.weight(.bold)).frame(maxWidth: .infinity).padding(.vertical, 14).background(color(for: item)).foregroundStyle(Theme.ink).clipShape(Capsule()) }
                }
            }
            .padding(.horizontal)
        }
        .padding(.vertical, 24).background(.white).clipShape(RoundedRectangle(cornerRadius: 28))
    }

    private func color(for answer: Answer) -> Color {
        switch answer { case .yes: Theme.lime; case .probablyYes: Color.green.opacity(0.25); case .unknown: Color.gray.opacity(0.18); case .probablyNo: Color.pink.opacity(0.18); case .no: Color.red.opacity(0.24) }
    }
}

private enum ResultMode { case confirmation, won, lost }

private struct ResultCard: View {
    let person: Person?
    let questions: Int
    let mode: ResultMode
    let confirm: () -> Void
    let reject: (() -> Void)?

    var body: some View {
        VStack(spacing: 18) {
            Text(title).font(.title2.bold()).foregroundStyle(Theme.ink).accessibilityAddTraits(.isHeader)
            if let person {
                Image(systemName: person.avatarSymbol).font(.system(size: 62)).foregroundStyle(Theme.purple).padding(24).background(Theme.lime).clipShape(Circle()).accessibilityHidden(true)
                Text(person.name).font(.system(.largeTitle, design: .rounded).weight(.black)).multilineTextAlignment(.center).foregroundStyle(Theme.ink)
                Text("\(person.country) • \(person.profession)").multilineTextAlignment(.center).foregroundStyle(.secondary)
            }
            Text(message).font(.headline).multilineTextAlignment(.center).foregroundStyle(Theme.ink)
            Button(action: confirm) { Text(primaryTitle).font(.headline.bold()).frame(maxWidth: .infinity).padding().background(Theme.purple).foregroundStyle(.white).clipShape(Capsule()) }
            if let reject {
                Button("Não, tente outra pessoa", action: reject).font(.headline.weight(.semibold)).foregroundStyle(Theme.purple).padding(.vertical, 4)
            }
        }
        .padding(28).background(.white).clipShape(RoundedRectangle(cornerRadius: 28))
    }

    private var title: String { switch mode { case .confirmation: "Meu palpite"; case .won: "Acertei!"; case .lost: "Quase lá" } }
    private var message: String { switch mode { case .confirmation: "É essa pessoa?"; case .won: "Descobri em \(questions) perguntas."; case .lost: person == nil ? "Não consegui chegar a um palpite confiável." : "Não consegui confirmar o palpite em \(questions) perguntas." } }
    private var primaryTitle: String { switch mode { case .confirmation: "Sim, acertou!"; case .won: "Jogar novamente"; case .lost: "Escolher outra categoria" } }
}

private struct UnavailableCard: View {
    let dismiss: () -> Void
    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "person.2.slash").font(.system(size: 48)).foregroundStyle(Theme.purple)
            Text("Categoria em preparação").font(.title2.bold()).foregroundStyle(Theme.ink)
            Text("Ainda não há pessoas ou perguntas suficientes para uma partida justa.").multilineTextAlignment(.center).foregroundStyle(.secondary)
            Button("Voltar às categorias", action: dismiss).font(.headline.bold()).frame(maxWidth: .infinity).padding().background(Theme.purple).foregroundStyle(.white).clipShape(Capsule())
        }
        .padding(28).background(.white).clipShape(RoundedRectangle(cornerRadius: 28))
    }
}

struct ProgressViewScreen: View {
    @EnvironmentObject private var progress: ProgressStore
    var body: some View {
        NavigationStack {
            VStack(spacing: 20) {
                Text("Meu progresso").font(.largeTitle.bold()).foregroundStyle(Theme.ink)
                HStack { StatCard(icon: "flame.fill", value: "\(progress.streak)", label: "dias", color: .pink); StatCard(icon: "crown.fill", value: "\(progress.points)", label: "pontos", color: Theme.purple) }
                Text("\(progress.wins) acertos confirmados").foregroundStyle(.secondary)
                Spacer()
            }.padding().background(Theme.soft.ignoresSafeArea()).navigationTitle("Conquistas")
        }
    }
}

struct ProfileView: View {
    var body: some View {
        NavigationStack {
            List {
                Section("Sobre o jogo") { Label("Funciona sem internet", systemImage: "wifi.slash"); Label("Nenhum dado coletado", systemImage: "lock.shield.fill"); NavigationLink("Privacidade") { Text("Quem Sou Eu? Adivinha não coleta, transmite ou vende dados pessoais. Todo o progresso fica neste aparelho.").padding() } }
                Section("Conteúdo") { Text("Base inicial com personalidades e fontes editoriais."); Text("Versão 1.0") }
            }.navigationTitle("Perfil")
        }
    }
}
