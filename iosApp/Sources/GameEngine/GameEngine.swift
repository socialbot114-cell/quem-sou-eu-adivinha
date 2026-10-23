import Foundation

enum GuessPolicy {
    static let questionLimit = 14
    static let minimumAnswersBeforeGuess = 4
    /// Confidence at which the game offers an early guess. Lowered from 0.68: fewer questions in every
    /// scenario with no loss of final accuracy (simulated; 0.50 saves more questions but lowers first guesses).
    static let confidenceThreshold = 0.55
    /// Abaixo deste nível, o jogo continua perguntando até o teto, em vez de parar no orçamento base.
    static let extensionConfidence = 0.50
    static let marginThreshold = 0.10
    /// Wrong guesses before the game gives up. Raised from 4: a character eliminated by mistaken answers
    /// is still recovered with more guesses (simulated: unsolved games 38 -> 6 with 10% wrong answers).
    static let maximumRejectedGuesses = 8
    static let likelihoodFloor = 0.18
    static let extraQuestionsPerRejectedGuess = 3
    static let freeUnknownAnswers = 2
    static let maximumQuestionLimit = 30

    /// Each rejected guess earns extra questions to recover from a mistaken answer,
    /// and the first "Não sei" answers do not consume the budget.
    static func questionBudget(availableAttributes: Int, rejectedGuesses: Int, unknownAnswers: Int) -> Int {
        let extended = questionLimit
            + extraQuestionsPerRejectedGuess * max(rejectedGuesses, 0)
            + min(max(unknownAnswers, 0), freeUnknownAnswers)
        return max(0, min(maximumQuestionLimit, extended, availableAttributes))
    }

    /// While the leading character is still uncertain, the game keeps asking (up to the maximum)
    /// instead of stopping at the base budget, so a long game can still reach a guess.
    static func effectiveQuestionLimit(availableAttributes: Int, rejectedGuesses: Int, unknownAnswers: Int, confidence: Double) -> Int {
        guard confidence < extensionConfidence else {
            return questionBudget(availableAttributes: availableAttributes, rejectedGuesses: rejectedGuesses, unknownAnswers: unknownAnswers)
        }
        return max(0, min(maximumQuestionLimit, availableAttributes))
    }
}

/// Lookup tables for one catalog. Every copy of an engine built from the same people shares it,
/// so undoing an answer does not rebuild them.
private final class CatalogIndex {
    let ids: [String]
    let positions: [String: Int]
    private let people: [Person]
    /// The value of every person for one attribute, aligned with `people`. Built on first use.
    private var columns: [String: [Double?]] = [:]

    init(people: [Person]) {
        self.people = people
        ids = people.map { $0.id }
        var positions: [String: Int] = [:]
        for (index, id) in ids.enumerated() {
            positions[id] = index
        }
        self.positions = positions
    }

    func column(for attribute: String) -> [Double?] {
        if let cached = columns[attribute] {
            return cached
        }
        let built = people.map { $0.attributes[attribute] }
        columns[attribute] = built
        return built
    }
}

struct GameEngine {
    private static let informativeAnswers = Answer.allCases.filter { $0 != .unknown }

    let people: [Person]
    let questions: [Question]
    /// How many distinct attributes the questions cover, which bounds the questions one round can ask.
    let availableAttributes: Int
    /// Scores by person id, kept in step with `weights` for callers that look people up by id.
    private(set) var scores: [String: Double]
    private(set) var asked: Set<String> = []
    private(set) var askedAttributes: Set<String> = []
    private(set) var rejectedPersonIDs: Set<String> = []
    private(set) var recordedQuestionIDs: Set<String> = []
    private let chooseCandidateIndex: (Int) -> Int
    private let smoothing: Double
    private let likelihoodFloor: Double
    private let catalog: CatalogIndex
    /// Scores aligned with `people`. The calculations read these, so they never hash a person id.
    private var weights: [Double]
    /// Rejected people, aligned with `people`.
    private var isRejected: [Bool]

    init(
        people: [Person],
        questions: [Question],
        randomIndex: @escaping (Int) -> Int = { Int.random(in: 0..<$0) },
        smoothing: Double = 1e-9,
        likelihoodFloor: Double = GuessPolicy.likelihoodFloor
    ) {
        self.init(
            people: people,
            questions: questions,
            catalog: CatalogIndex(people: people),
            randomIndex: randomIndex,
            smoothing: smoothing,
            likelihoodFloor: likelihoodFloor
        )
    }

    private init(
        people: [Person],
        questions: [Question],
        catalog: CatalogIndex,
        randomIndex: @escaping (Int) -> Int,
        smoothing: Double,
        likelihoodFloor: Double
    ) {
        self.people = people
        self.questions = questions
        self.availableAttributes = Set(questions.map(\.attribute)).count
        self.catalog = catalog
        self.chooseCandidateIndex = randomIndex
        self.smoothing = smoothing
        self.likelihoodFloor = likelihoodFloor
        let uniform = 1.0 / Double(max(people.count, 1))
        self.weights = Array(repeating: uniform, count: people.count)
        self.isRejected = Array(repeating: false, count: people.count)
        self.scores = [:]
        publishScores()
    }

    // MARK: - Ranking

    /// Indices of every person, highest score first. Equal scores keep the catalog order.
    private var rankedIndices: [Int] {
        weights.indices.sorted { lhs, rhs in
            weights[lhs] != weights[rhs] ? weights[lhs] > weights[rhs] : lhs < rhs
        }
    }

    var ranked: [Person] {
        rankedIndices.map { people[$0] }
    }

    var activePeople: [Person] {
        rankedIndices.filter { weights[$0] > 0 }.map { people[$0] }
    }

    /// The two leaders still in play, found in one pass. Equal scores go to the earlier person,
    /// the same order `activePeople` gives.
    private var leaders: (first: Int?, second: Int?) {
        var first: Int?
        var second: Int?
        for index in weights.indices where weights[index] > 0 {
            let value = weights[index]
            if let best = first, value <= weights[best] {
                if let runnerUp = second, value <= weights[runnerUp] { continue }
                second = index
            } else {
                second = first
                first = index
            }
        }
        return (first, second)
    }

    var bestGuess: Person? {
        leaders.first.map { people[$0] }
    }

    var confidence: Double {
        leaders.first.map { weights[$0] } ?? 0
    }

    var secondBest: Person? {
        leaders.second.map { people[$0] }
    }

    var margin: Double {
        let pair = leaders
        guard let first = pair.first else { return 0 }
        guard let second = pair.second else { return weights[first] }
        return weights[first] - weights[second]
    }

    var ratio: Double {
        let pair = leaders
        guard let first = pair.first, let second = pair.second else { return .greatestFiniteMagnitude }
        let secondScore = weights[second]
        guard secondScore > 0 else { return .greatestFiniteMagnitude }
        return weights[first] / secondScore
    }

    var entropyValue: Double {
        entropy(weights)
    }

    var effectiveCandidates: Double {
        pow(2.0, entropyValue)
    }

    // MARK: - Question selection

    mutating func nextQuestion() -> Question? {
        guard !people.isEmpty else { return nil }
        let priorEntropy = entropy(weights)
        let scored = questions
            .filter { !asked.contains($0.id) && !askedAttributes.contains($0.attribute) }
            .map { (question: $0, gain: informationGain($0, priorEntropy: priorEntropy)) }
            .filter { $0.gain > 0.001 }
        guard !scored.isEmpty else { return nil }

        let bestGain = scored.map { $0.gain }.max() ?? 0
        let candidates = scored.filter { $0.gain >= bestGain - 0.01 }.map { $0.question }
        guard let selected = safePick(from: candidates) else { return nil }

        markAsked(selected)
        return selected
    }

    /// Reserves a question so it is never selected again, e.g. when an undone question is shown again.
    mutating func markAsked(_ question: Question) {
        asked.insert(question.id)
        askedAttributes.insert(question.attribute)
    }

    private func safePick(from candidates: [Question]) -> Question? {
        guard !candidates.isEmpty else { return nil }
        let index = chooseCandidateIndex(candidates.count)
        let safeIndex = candidates.indices.contains(index) ? index : 0
        return candidates[safeIndex]
    }

    // MARK: - Evidence

    mutating func apply(_ answer: Answer, to question: Question) {
        guard answer != .unknown else { return }
        guard !recordedQuestionIDs.contains(question.id) else { return }
        recordedQuestionIDs.insert(question.id)
        let values = catalog.column(for: question.attribute)
        for index in weights.indices {
            let value = values[index] ?? 0.5
            weights[index] *= likelihood(value, answer, normalizer: normalizer(for: value))
        }
        normalize()
    }

    mutating func reject(_ person: Person) {
        rejectedPersonIDs.insert(person.id)
        if let index = catalog.positions[person.id] {
            isRejected[index] = true
            weights[index] = 0
        }
        normalize()
    }

    /// Rebuilds the engine from scratch, used to undo an answer without drifting from the saved round.
    func replaying(_ answers: [RecordedAnswer], rejectedPersonIDs rejected: [String]) -> GameEngine {
        var engine = GameEngine(
            people: people,
            questions: questions,
            catalog: catalog,
            randomIndex: chooseCandidateIndex,
            smoothing: smoothing,
            likelihoodFloor: likelihoodFloor
        )
        engine.restore(answers)
        for id in rejected {
            if let person = people.first(where: { $0.id == id }) { engine.reject(person) }
        }
        return engine
    }

    mutating func restore(_ answers: [RecordedAnswer]) {
        for record in answers {
            guard let question = questions.first(where: { $0.id == record.questionID }) else { continue }
            markAsked(question)
            apply(record.answer, to: question)
        }
    }

    // MARK: - Normalization

    private mutating func normalize() {
        defer { publishScores() }
        for index in weights.indices where isRejected[index] {
            weights[index] = 0
        }
        var activeCount = 0
        for rejected in isRejected where !rejected {
            activeCount += 1
        }

        let total = weights.reduce(0, +)
        if total <= 0 {
            guard activeCount > 0 else { return }
            let share = 1.0 / Double(activeCount)
            for index in weights.indices {
                weights[index] = isRejected[index] ? 0 : share
            }
            return
        }

        for index in weights.indices where !isRejected[index] {
            weights[index] += smoothing
        }
        let smoothedTotal = weights.reduce(0, +)
        for index in weights.indices {
            let value = weights[index]
            weights[index] = (value.isFinite && value >= 0) ? value / smoothedTotal : 0
        }
    }

    private mutating func publishScores() {
        scores = Dictionary(uniqueKeysWithValues: zip(catalog.ids, weights))
    }

    // MARK: - Information gain

    private func informationGain(_ question: Question, priorEntropy: Double) -> Double {
        let values = catalog.column(for: question.attribute)
        var coverage = 0.0
        for index in weights.indices where values[index] != nil {
            coverage += weights[index]
        }
        guard coverage >= 0.6 else { return 0 }

        let normalizers = values.map { normalizer(for: $0 ?? 0.5) }
        var expectedEntropy = 0.0
        for answer in GameEngine.informativeAnswers {
            var probability = 0.0
            for index in weights.indices {
                probability += weights[index] * likelihood(values[index] ?? 0.5, answer, normalizer: normalizers[index])
            }
            guard probability > 0 else { continue }

            var answerEntropy = 0.0
            for index in weights.indices {
                let share = weights[index] * likelihood(values[index] ?? 0.5, answer, normalizer: normalizers[index]) / probability
                guard share > 0 else { continue }
                answerEntropy -= share * log2(share)
            }
            expectedEntropy += probability * answerEntropy
        }
        return max(0, priorEntropy - expectedEntropy) * coverage
    }

    /// The likelihoods of the informative answers for one value add up to this normalizer.
    /// It does not depend on the answer, so it is computed once per person and question.
    private func normalizer(for value: Double) -> Double {
        GameEngine.informativeAnswers.reduce(0.0) { total, option in
            total + max(likelihoodFloor, 1.0 - abs(value - option.evidence))
        }
    }

    private func likelihood(_ value: Double, _ answer: Answer, normalizer: Double) -> Double {
        let raw = max(likelihoodFloor, 1.0 - abs(value - answer.evidence))
        return normalizer > 0 ? raw / normalizer : 1.0
    }

    private func entropy<S: Sequence>(_ values: S) -> Double where S.Element == Double {
        values.reduce(0.0) { result, value in
            guard value > 0 else { return result }
            return result - value * log2(value)
        }
    }
}
