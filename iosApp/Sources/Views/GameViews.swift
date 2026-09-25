import SwiftUI

struct CategoryView: View {
    private let base = KnowledgeStore.shared.base
    let onSelect: (Category) -> Void

    private var categories: [Category] {
        Category.allCases.filter { $0 != .all && count(for: $0) >= 12 }
    }

    var body: some View {
        NavigationStack {
            DSDecorativeBackground {
                ScrollView {
                    VStack(alignment: .leading, spacing: 20) {
                        VStack(alignment: .leading, spacing: 5) {
                            Text("ESCOLHA SEU UNIVERSO")
                                .font(.caption.weight(.black)).tracking(1.8)
                                .foregroundStyle(DesignSystem.Palette.violet)
                            Text("Quem está na sua cabeça?")
                                .font(.system(.largeTitle, design: .rounded, weight: .black))
                            Text("Categorias menores deixam minhas pistas mais certeiras.")
                                .font(.body.weight(.medium)).foregroundStyle(.secondary)
                        }

                        LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 14) {
                            ForEach(categories) { category in
                                Button { onSelect(category) } label: {
                                    CategoryCard(category: category, count: count(for: category))
                                }
                                .buttonStyle(.plain)
                            }
                        }

                        Button { onSelect(.all) } label: {
                            HStack(spacing: 16) {
                                Image(systemName: Category.all.symbol)
                                    .font(.system(size: 28, weight: .black))
                                    .frame(width: 56, height: 56)
                                    .background(DesignSystem.Palette.lime, in: Circle())
                                VStack(alignment: .leading, spacing: 3) {
                                    Text("Modo livre").font(.title3.weight(.black))
                                    Text("Todas as \(base.people.count) personalidades")
                                        .font(.subheadline).opacity(0.78)
                                }
                                Spacer()
                                Image(systemName: "arrow.right.circle.fill").font(.title2)
                            }
                            .foregroundStyle(.white)
                            .padding(18)
                            .background(DesignSystem.Gradient.primary, in: RoundedRectangle(cornerRadius: 24, style: .continuous))
                        }
                        .buttonStyle(.plain)
                        .accessibilityIdentifier("category.all")
                    }
                    .frame(maxWidth: DesignSystem.Metric.contentMaxWidth)
                    .padding(20)
                    .frame(maxWidth: .infinity)
                }
            }
            .toolbar(.hidden, for: .navigationBar)
        }
    }

    private func count(for category: Category) -> Int {
        base.people.filter { $0.categories.contains(category) }.count
    }
}

private struct CategoryCard: View {
    let category: Category
    let count: Int

    private var colors: [Color] {
        switch category {
        case .creators: [Color.pink, DesignSystem.Palette.violet]
        case .football: [Color.green, Color.teal]
        case .artists: [DesignSystem.Palette.gold, Color.orange]
        case .politicians: [Color.indigo, DesignSystem.Palette.violet]
        case .history: [Color.brown, Color.orange]
        case .world: [Color.blue, Color.cyan]
        case .otherSports: [Color.green, Color.teal]
        case .internationalMusic: [Color.pink, DesignSystem.Palette.violet]
        case .kpop: [Color.pink, Color.purple]
        case .cinema: [Color.indigo, Color.blue]
        case .fashion: [Color.orange, Color.pink]
        case .technology: [Color.cyan, DesignSystem.Palette.violet]
        case .all: [DesignSystem.Palette.violet, DesignSystem.Palette.violetLight]
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack {
                Image(systemName: category.symbol)
                    .font(.system(size: 28, weight: .black))
                Spacer()
                Text("\(count)")
                    .font(.caption.weight(.black))
                    .padding(.horizontal, 9).padding(.vertical, 5)
                    .background(.white.opacity(0.22), in: Capsule())
            }
            Spacer(minLength: 8)
            Text(category.rawValue)
                .font(.system(.headline, design: .rounded, weight: .black))
                .multilineTextAlignment(.leading)
                .lineLimit(2)
            Text("Começar investigação")
                .font(.caption.weight(.semibold)).opacity(0.8)
        }
        .foregroundStyle(.white)
        .frame(maxWidth: .infinity, minHeight: 142, alignment: .leading)
        .padding(16)
        .background(LinearGradient(colors: colors, startPoint: .topLeading, endPoint: .bottomTrailing), in: RoundedRectangle(cornerRadius: 24, style: .continuous))
        .shadow(color: colors.last!.opacity(0.22), radius: 12, y: 7)
        .accessibilityElement(children: .combine)
        .accessibilityHint("Inicia uma partida")
        .accessibilityIdentifier("category.\(category.rawValue)")
    }
}

private enum GamePhase {
    case loading
    case asking
    case confirming(Person)
    case won(Person)
    case lost(Person?)
    case unavailable
}

struct GameView: View {
    let category: Category
    let playAnotherCategory: () -> Void
    @Environment(\.dismiss) private var dismiss
    @EnvironmentObject private var progress: ProgressStore
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var engine: GameEngine
    @State private var question: Question?
    @State private var questionNumber = 0
    @State private var phase = GamePhase.loading
    @State private var answers: [RecordedAnswer] = []
    @State private var rejectedPersonIDs: [String] = []
    @State private var didLoad = false
    @State private var completed = false
    @State private var isTransitioning = false
    @State private var showingHelp = false
    @State private var successFeedback = 0
    @State private var failureFeedback = 0

    private static let maxRejected = 4

    init(category: Category, playAnotherCategory: @escaping () -> Void) {
        self.category = category
        self.playAnotherCategory = playAnotherCategory
        let base = KnowledgeStore.shared.base
        let people = category == .all ? base.people : base.people.filter { $0.categories.contains(category) }
        let questions = base.questions.filter { $0.categories.contains(.all) || $0.categories.contains(category) || category == .all }
        _engine = State(initialValue: GameEngine(people: people, questions: questions))
    }

    private var questionLimit: Int { min(14, Set(engine.questions.map(\.attribute)).count) }

    var body: some View {
        ZStack {
            DesignSystem.Gradient.primary.ignoresSafeArea()
            Circle().fill(DesignSystem.Palette.lime.opacity(0.13)).frame(width: 340).blur(radius: 50).offset(x: 180, y: -320)

            ScrollView {
                VStack(spacing: 18) {
                    header
                    if let error = KnowledgeStore.shared.loadError {
                        Text(error.localizedDescription).foregroundStyle(.white).multilineTextAlignment(.center).padding()
                    } else {
                        content
                    }
                }
                .frame(maxWidth: DesignSystem.Metric.contentMaxWidth)
                .padding(18)
                .frame(maxWidth: .infinity)
            }
        }
        .onAppear(perform: loadRound)
        .sensoryFeedback(.success, trigger: successFeedback)
        .sensoryFeedback(.warning, trigger: failureFeedback)
        .sheet(isPresented: $showingHelp) { GameHelpView() }
        .interactiveDismissDisabled(!completed && !answers.isEmpty)
    }

    private var header: some View {
        VStack(spacing: 12) {
            HStack {
                Button {
                    persistRound()
                    dismiss()
                } label: {
                    Image(systemName: "xmark").font(.headline.weight(.black))
                        .frame(width: 44, height: 44).background(.white.opacity(0.16), in: Circle())
                }
                .accessibilityLabel("Sair e salvar partida")
                Spacer()
                VStack(spacing: 2) {
                    Text(category.rawValue).font(.caption.weight(.bold)).opacity(0.75)
                    Text("Pergunta \(max(1, questionNumber + 1))").font(.headline.weight(.black))
                }
                Spacer()
                Button { showingHelp = true } label: {
                    Image(systemName: "questionmark").font(.headline.weight(.black))
                        .frame(width: 44, height: 44).background(.white.opacity(0.16), in: Circle())
                }
                .accessibilityLabel("Como jogar")
            }
            .foregroundStyle(.white)

            ProgressView(value: Double(questionNumber), total: Double(max(questionLimit, 1)))
                .tint(DesignSystem.Palette.lime)
                .accessibilityLabel("Progresso da investigação")
                .accessibilityValue("\(questionNumber) perguntas respondidas")
        }
    }

    @ViewBuilder private var content: some View {
        switch phase {
        case .loading:
            ProgressView("Organizando as pistas…").tint(DesignSystem.Palette.lime).foregroundStyle(.white).padding(50)
        case .asking:
            if let question {
                QuestionCard(question: question, answer: { respond($0, to: question) })
                    .transition(reduceMotion ? .opacity : .asymmetric(insertion: .move(edge: .trailing).combined(with: .opacity), removal: .move(edge: .leading).combined(with: .opacity)))
                Text("Não existe resposta errada. Use “Não sei” quando tiver dúvida.")
                    .foregroundStyle(.white.opacity(0.78)).font(.footnote.weight(.medium)).multilineTextAlignment(.center)
            } else {
                ProgressView("Organizando as pistas…").tint(DesignSystem.Palette.lime).foregroundStyle(.white).padding(50)
            }
        case .confirming(let person):
            ResultCard(person: person, questions: questionNumber, mode: .confirmation, confirm: confirmGuess, reject: { reject(person) }, playAgain: resetRound, otherCategory: playAnotherCategory)
        case .won(let person):
            ResultCard(person: person, questions: questionNumber, mode: .won, confirm: nil, reject: nil, playAgain: resetRound, otherCategory: playAnotherCategory)
        case .lost(let person):
            ResultCard(person: person, questions: questionNumber, mode: .lost, confirm: nil, reject: nil, playAgain: resetRound, otherCategory: playAnotherCategory)
        case .unavailable:
            UnavailableCard(dismiss: playAnotherCategory)
        }
    }

    private func loadRound() {
        guard !didLoad else { return }
        didLoad = true
        if let saved = progress.interruptedRound,
           saved.category == category,
           !saved.answers.isEmpty,
           isRoundStillValid(saved) {
            answers = saved.answers
            rejectedPersonIDs = saved.rejectedPersonIDs
            questionNumber = saved.answers.count
            engine.restore(saved.answers)
            for personID in saved.rejectedPersonIDs {
                if let person = engine.people.first(where: { $0.id == personID }) { engine.reject(person) }
            }
            if questionNumber >= questionLimit || shouldPresentGuess {
                presentBestGuess()
                return
            }
        }
        advance()
    }

    private var shouldPresentGuess: Bool {
        guard questionNumber >= 4 else { return false }
        return engine.confidence >= 0.68 && engine.margin >= 0.10
    }

    private func isRoundStillValid(_ saved: InterruptedRoundSummary) -> Bool {
        if let fingerprint = saved.knowledgeFingerprint, !fingerprint.isEmpty {
            guard fingerprint == KnowledgeStore.shared.fingerprint else { return false }
        }
        guard saved.updatedAt.addingTimeInterval(7 * 86_400) > Date() else { return false }
        return true
    }

    private func respond(_ answer: Answer, to question: Question) {
        guard !completed, !isTransitioning else { return }
        guard case .asking = phase else { return }
        guard self.question?.id == question.id else { return }
        isTransitioning = true
        engine.apply(answer, to: question)
        answers.append(RecordedAnswer(questionID: question.id, answer: answer))
        questionNumber = answers.count
        persistRound()
        if questionNumber >= questionLimit || shouldPresentGuess {
            presentBestGuess()
        } else {
            withAnimation(.snappy) { advance() }
        }
        isTransitioning = false
    }

    private func advance() {
        guard !engine.people.isEmpty, questionLimit > 0 else { phase = .unavailable; return }
        question = engine.nextQuestion()
        if question == nil { presentBestGuess() } else { phase = .asking }
    }

    private func presentBestGuess() {
        question = nil
        guard let guess = engine.bestGuess, engine.confidence >= 0.18 else {
            finishLoss(person: nil)
            return
        }
        phase = .confirming(guess)
    }

    private func confirmGuess() {
        guard !completed else { return }
        guard case .confirming(let person) = phase else { return }
        completed = true
        progress.recordWin(questions: questionNumber, category: category, discoveredPersonID: person.id)
        successFeedback += 1
        phase = .won(person)
    }

    private func reject(_ person: Person) {
        guard !completed else { return }
        guard case .confirming = phase else { return }
        guard !rejectedPersonIDs.contains(person.id) else { return }
        engine.reject(person)
        rejectedPersonIDs.append(person.id)
        persistRound()
        if rejectedPersonIDs.count >= Self.maxRejected || questionNumber >= questionLimit || engine.bestGuess == nil {
            finishLoss(person: engine.bestGuess)
        } else {
            phase = .asking
            advance()
        }
    }

    private func finishLoss(person: Person?) {
        question = nil
        guard !completed else { return }
        completed = true
        progress.recordLoss(questions: questionNumber, category: category)
        failureFeedback += 1
        phase = .lost(person)
    }

    private func persistRound() {
        guard !completed, !answers.isEmpty else { return }
        progress.saveInterruptedRound(InterruptedRoundSummary(
            category: category,
            questionsAnswered: answers.count,
            currentQuestionID: question?.id,
            bestGuessPersonID: engine.bestGuess?.id,
            answers: answers,
            rejectedPersonIDs: rejectedPersonIDs,
            knowledgeFingerprint: KnowledgeStore.shared.fingerprint
        ))
    }

    private func resetRound() {
        let base = KnowledgeStore.shared.base
        let people = category == .all ? base.people : base.people.filter { $0.categories.contains(category) }
        let questions = base.questions.filter { $0.categories.contains(.all) || $0.categories.contains(category) || category == .all }
        engine = GameEngine(people: people, questions: questions)
        answers = []
        rejectedPersonIDs = []
        questionNumber = 0
        completed = false
        phase = .asking
        progress.clearInterruptedRound()
        advance()
    }
}

private struct QuestionCard: View {
    let question: Question
    let answer: (Answer) -> Void

    private let columns = [GridItem(.flexible()), GridItem(.flexible())]

    var body: some View {
        VStack(spacing: 22) {
            Image(DesignSystem.Asset.hintIdea.rawValue)
                .resizable().scaledToFit().frame(height: 104).accessibilityHidden(true)
            Text(question.text)
                .font(.system(.title, design: .rounded, weight: .black))
                .multilineTextAlignment(.center)
                .foregroundStyle(DesignSystem.Palette.ink)
                .padding(.horizontal, 6)
                .accessibilityAddTraits(.isHeader)
                .accessibilityIdentifier("question.\(question.attribute)")

            LazyVGrid(columns: columns, spacing: 10) {
                AnswerButton(title: "Sim", symbol: "checkmark", color: DesignSystem.Palette.lime) { answer(.yes) }
                AnswerButton(title: "Provavelmente", symbol: "hand.thumbsup.fill", color: .green.opacity(0.28)) { answer(.probablyYes) }
                AnswerButton(title: "Não sei", symbol: "questionmark", color: .gray.opacity(0.2)) { answer(.unknown) }
                AnswerButton(title: "Acho que não", symbol: "hand.thumbsdown.fill", color: .orange.opacity(0.25)) { answer(.probablyNo) }
            }
            Button { answer(.no) } label: {
                Label("Não", systemImage: "xmark").frame(maxWidth: .infinity, minHeight: 48)
            }
            .font(.headline.weight(.bold))
            .foregroundStyle(.red)
            .background(.red.opacity(0.11), in: Capsule())
        }
        .padding(24)
        .background(.white, in: RoundedRectangle(cornerRadius: 30, style: .continuous))
        .shadow(color: .black.opacity(0.2), radius: 24, y: 12)
    }
}

private struct AnswerButton: View {
    let title: String
    let symbol: String
    let color: Color
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: 7) {
                Image(systemName: symbol).font(.title3.weight(.black))
                Text(title).font(.subheadline.weight(.bold)).multilineTextAlignment(.center)
            }
            .foregroundStyle(DesignSystem.Palette.ink)
            .frame(maxWidth: .infinity, minHeight: 72)
            .background(color, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
        }
        .buttonStyle(.plain)
    }
}

private enum ResultMode: Hashable { case confirmation, won, lost }

private struct ResultCard: View {
    let person: Person?
    let questions: Int
    let mode: ResultMode
    let confirm: (() -> Void)?
    let reject: (() -> Void)?
    let playAgain: () -> Void
    let otherCategory: () -> Void

    var body: some View {
        VStack(spacing: 17) {
            Image(assetName).resizable().scaledToFit().frame(height: mode == .confirmation ? 76 : 96).accessibilityHidden(true)
            Text(title).font(.system(.title, design: .rounded, weight: .black)).foregroundStyle(DesignSystem.Palette.ink)
            if let person {
                CharacterPortrait(person: person)
                Text(person.name).font(.system(.largeTitle, design: .rounded, weight: .black)).multilineTextAlignment(.center)
                Text("\(person.country) • \(person.profession)").multilineTextAlignment(.center).foregroundStyle(.secondary)
            }
            Text(message).font(.headline).multilineTextAlignment(.center).foregroundStyle(DesignSystem.Palette.ink)

            if let confirm {
                Button("Acertou!", action: confirm).buttonStyle(PrimaryButtonStyle())
                if let reject {
                    Button("Não foi dessa vez", action: reject).buttonStyle(SecondaryButtonStyle())
                }
            } else {
                if mode == .won, let person {
                    HStack(spacing: 8) {
                        Label("\(questions) pistas", systemImage: "questionmark.circle.fill")
                        Label("+20 moedas", systemImage: "sparkles")
                    }
                    .font(.caption.weight(.bold)).foregroundStyle(DesignSystem.Palette.violet)

                    ShareLink(item: "A Princesa Detetive descobriu \(person.name) em \(questions) pistas no Quem Sou Eu? Adivinha!") {
                        Label("Compartilhar resultado", systemImage: "square.and.arrow.up")
                    }
                    .buttonStyle(SecondaryButtonStyle())
                }
                Button("Jogar novamente", action: playAgain).buttonStyle(PrimaryButtonStyle())
                Button("Escolher outra categoria", action: otherCategory)
                    .font(.subheadline.weight(.bold)).foregroundStyle(DesignSystem.Palette.violet)
            }
        }
        .padding(24)
        .background(.white, in: RoundedRectangle(cornerRadius: 30, style: .continuous))
        .shadow(color: .black.opacity(0.2), radius: 24, y: 12)
    }

    private var assetName: String {
        switch mode {
        case .confirmation: DesignSystem.Asset.hintIdea.rawValue
        case .won: DesignSystem.Asset.feedbackSuccess.rawValue
        case .lost: DesignSystem.Asset.feedbackError.rawValue
        }
    }
    private var title: String { switch mode { case .confirmation: "Já tenho um palpite!"; case .won: "ACERTEI!"; case .lost: "Quase!" } }
    private var message: String {
        switch mode {
        case .confirmation: "É essa pessoa?"
        case .won: "Descobri em \(questions) pistas. Essa investigação entrou para sua coleção."
        case .lost: "Cada resposta me deixa mais esperta. Vamos tentar outra vez?"
        }
    }
}

private struct UnavailableCard: View {
    let dismiss: () -> Void
    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "person.2.slash").font(.system(size: 48)).foregroundStyle(DesignSystem.Palette.violet)
            Text("Categoria em preparação").font(.title2.bold())
            Text("Ainda não há pistas suficientes para uma partida justa.").multilineTextAlignment(.center).foregroundStyle(.secondary)
            Button("Voltar às categorias", action: dismiss).buttonStyle(PrimaryButtonStyle())
        }
        .padding(28).background(.white, in: RoundedRectangle(cornerRadius: 28, style: .continuous))
    }
}

private struct GameHelpView: View {
    @Environment(\.dismiss) private var dismiss
    var body: some View {
        NavigationStack {
            VStack(spacing: 20) {
                DSMascotView(size: 190)
                Text("Como investigar").font(.system(.title, design: .rounded, weight: .black))
                VStack(alignment: .leading, spacing: 14) {
                    HelpRow(number: "1", text: "Pense em alguém da categoria escolhida.")
                    HelpRow(number: "2", text: "Responda com sinceridade. Não existe resposta errada.")
                    HelpRow(number: "3", text: "Use “Não sei” quando estiver em dúvida.")
                    HelpRow(number: "4", text: "Espere o palpite da Princesa Detetive.")
                }.dsCard()
                Button("Continuar jogando") { dismiss() }.buttonStyle(PrimaryButtonStyle())
                Spacer()
            }
            .padding(22)
            .background(DesignSystem.Gradient.background.ignoresSafeArea())
            .toolbar { ToolbarItem(placement: .topBarTrailing) { Button("Fechar") { dismiss() } } }
        }
        .presentationDetents([.large])
    }
}

private struct HelpRow: View {
    let number: String
    let text: String
    var body: some View {
        HStack(spacing: 12) {
            Text(number).font(.headline.weight(.black)).foregroundStyle(.white)
                .frame(width: 34, height: 34).background(DesignSystem.Palette.violet, in: Circle())
            Text(text).font(.body.weight(.medium))
        }
    }
}

struct ProgressViewScreen: View {
    @EnvironmentObject private var progress: ProgressStore
    private let people = KnowledgeStore.shared.base.people

    private var discovered: [Person] {
        people.filter { progress.discoveredPersonIDs.contains($0.id) }
    }

    var body: some View {
        NavigationStack {
            DSDecorativeBackground {
                ScrollView {
                    VStack(alignment: .leading, spacing: 20) {
                        Text("Sua coleção").font(.system(.largeTitle, design: .rounded, weight: .black))
                        HStack(spacing: 10) {
                            MetricCard(value: "\(progress.wins)", label: "acertos", color: DesignSystem.Palette.violet)
                            MetricCard(value: "\(progress.streak)", label: "dias", color: .orange)
                            MetricCard(value: "\(progress.points)", label: "pontos", color: .blue)
                        }

                        VStack(alignment: .leading, spacing: 4) {
                            Text("Descobertas").font(.title2.weight(.black))
                            Text("\(discovered.count) de \(people.count) personalidades").foregroundStyle(.secondary)
                        }

                        if discovered.isEmpty {
                            VStack(spacing: 14) {
                                Image(DesignSystem.Asset.achievementTrophy.rawValue).resizable().scaledToFit().frame(height: 120)
                                Text("Sua primeira descoberta aparecerá aqui.").font(.headline).multilineTextAlignment(.center)
                            }
                            .frame(maxWidth: .infinity).dsCard()
                        } else {
                            LazyVGrid(columns: [GridItem(.adaptive(minimum: 138))], spacing: 14) {
                                ForEach(discovered) { person in
                                    VStack(spacing: 9) {
                                        CharacterPortrait(person: person, size: 112)
                                        Text(person.name).font(.subheadline.weight(.bold)).multilineTextAlignment(.center).lineLimit(2)
                                        Text(person.profession).font(.caption).foregroundStyle(.secondary).lineLimit(1)
                                    }
                                    .frame(maxWidth: .infinity).dsCard(padding: 12)
                                }
                            }
                        }
                    }
                    .frame(maxWidth: DesignSystem.Metric.contentMaxWidth)
                    .padding(20).frame(maxWidth: .infinity)
                }
            }
            .toolbar(.hidden, for: .navigationBar)
        }
    }
}

private struct MetricCard: View {
    let value: String
    let label: String
    let color: Color
    var body: some View {
        VStack(spacing: 5) {
            Text(value).font(.title2.weight(.black)).foregroundStyle(color)
            Text(label).font(.caption).foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity).padding(.vertical, 15).dsCard(padding: 8)
        .accessibilityElement(children: .combine)
    }
}

struct ProfileView: View {
    let showOnboarding: () -> Void
    private var version: String { Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "—" }
    private var build: String { Bundle.main.object(forInfoDictionaryKey: "CFBundleVersion") as? String ?? "—" }

    var body: some View {
        NavigationStack {
            DSDecorativeBackground {
                ScrollView {
                    VStack(alignment: .leading, spacing: 18) {
                        Text("Perfil e ajustes").font(.system(.largeTitle, design: .rounded, weight: .black))
                        ProfileRow(icon: "questionmark.circle.fill", title: "Como jogar", subtitle: "Rever a missão da Princesa Detetive", action: showOnboarding)
                        NavigationLink { CreditsView() } label: {
                            ProfileRowLabel(icon: "photo.on.rectangle.angled", title: "Créditos das imagens", subtitle: "Autores, fontes e licenças")
                        }.buttonStyle(.plain)
                        NavigationLink { PrivacyView() } label: {
                            ProfileRowLabel(icon: "lock.shield.fill", title: "Privacidade", subtitle: "Seus dados ficam neste aparelho")
                        }.buttonStyle(.plain)

                        VStack(alignment: .leading, spacing: 8) {
                            Label("Jogue sem internet", systemImage: "wifi.slash").font(.headline)
                            Text("Sem cadastro, anúncios ou rastreamento. O progresso é salvo localmente.")
                                .foregroundStyle(.secondary)
                        }.dsCard()

                        Text("Versão \(version) (\(build))")
                            .font(.footnote).foregroundStyle(.secondary).frame(maxWidth: .infinity)
                    }
                    .frame(maxWidth: DesignSystem.Metric.contentMaxWidth)
                    .padding(20).frame(maxWidth: .infinity)
                }
            }
            .toolbar(.hidden, for: .navigationBar)
        }
    }
}

private struct ProfileRow: View {
    let icon: String
    let title: String
    let subtitle: String
    let action: () -> Void
    var body: some View { Button(action: action) { ProfileRowLabel(icon: icon, title: title, subtitle: subtitle) }.buttonStyle(.plain) }
}

private struct ProfileRowLabel: View {
    let icon: String
    let title: String
    let subtitle: String
    var body: some View {
        HStack(spacing: 14) {
            Image(systemName: icon).font(.title2.weight(.bold)).foregroundStyle(DesignSystem.Palette.violet).frame(width: 38)
            VStack(alignment: .leading, spacing: 3) {
                Text(title).font(.headline).foregroundStyle(DesignSystem.Palette.ink)
                Text(subtitle).font(.subheadline).foregroundStyle(.secondary)
            }
            Spacer()
            Image(systemName: "chevron.right").foregroundStyle(.secondary)
        }.dsCard()
    }
}

private struct PrivacyView: View {
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Text("Privacidade em primeiro lugar").font(.system(.title, design: .rounded, weight: .black))
                Text("Quem Sou Eu? Adivinha não exige conta e não coleta, transmite ou vende dados pessoais. Partidas, coleção e preferências ficam somente neste aparelho.")
                Text("O aplicativo funciona offline e não utiliza publicidade nem ferramentas de rastreamento.")
            }.padding(22)
        }.navigationTitle("Privacidade").navigationBarTitleDisplayMode(.inline)
    }
}

private struct CreditManifest: Decodable {
    let items: [CreditItem]
}
private struct CreditItem: Decodable, Identifiable {
    let id: String
    let name: String
    let author: String
    let license: String
    let url: URL
    let modifications: String
}

private struct CreditsView: View {
    private var credits: [CreditItem] {
        guard let url = Bundle.main.url(forResource: "image-credits", withExtension: "json"),
              let data = try? Data(contentsOf: url),
              let manifest = try? JSONDecoder().decode(CreditManifest.self, from: data) else { return [] }
        return manifest.items
    }
    var body: some View {
        List(credits) { credit in
            VStack(alignment: .leading, spacing: 5) {
                Text(credit.name).font(.headline)
                Text("Foto: \(credit.author)").font(.subheadline)
                Link("\(credit.license) • Ver fonte", destination: credit.url).font(.caption.weight(.semibold))
                Text("Modificações: \(credit.modifications)")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }.padding(.vertical, 5)
        }
        .navigationTitle("Créditos")
        .navigationBarTitleDisplayMode(.inline)
    }
}
