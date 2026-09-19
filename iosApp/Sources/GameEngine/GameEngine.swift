import Foundation

struct GameEngine {
    let people: [Person]
    let questions: [Question]
    private(set) var scores: [String: Double]
    private(set) var asked: Set<String> = []
    private(set) var askedAttributes: Set<String> = []
    private(set) var rejectedPersonIDs: Set<String> = []
    private(set) var recordedQuestionIDs: Set<String> = []
    private let chooseCandidateIndex: (Int) -> Int
    private let smoothing: Double

    init(
        people: [Person],
        questions: [Question],
        randomIndex: @escaping (Int) -> Int = { Int.random(in: 0..<$0) },
        smoothing: Double = 1e-9
    ) {
        self.people = people
        self.questions = questions
        self.chooseCandidateIndex = randomIndex
        self.smoothing = smoothing
        self.scores = Dictionary(uniqueKeysWithValues: people.map { ($0.id, 1.0 / Double(max(people.count, 1))) })
    }

    // MARK: - Ranking

    var ranked: [Person] {
        people.sorted { scores[$0.id, default: 0] > scores[$1.id, default: 0] }
    }

    var activePeople: [Person] {
        ranked.filter { scores[$0.id, default: 0] > 0 }
    }

    var bestGuess: Person? {
        activePeople.first
    }

    var confidence: Double {
        bestGuess.map { scores[$0.id, default: 0] } ?? 0
    }

    var secondBest: Person? {
        activePeople.count > 1 ? activePeople[1] : nil
    }

    var margin: Double {
        guard let first = bestGuess else { return 0 }
        guard let second = secondBest else { return scores[first.id, default: 0] }
        return scores[first.id, default: 0] - scores[second.id, default: 0]
    }

    var ratio: Double {
        guard let first = bestGuess, let second = secondBest else { return .greatestFiniteMagnitude }
        let secondScore = scores[second.id, default: 0]
        guard secondScore > 0 else { return .greatestFiniteMagnitude }
        return scores[first.id, default: 0] / secondScore
    }

    var entropyValue: Double {
        entropy(scores.values)
    }

    var effectiveCandidates: Double {
        pow(2.0, entropyValue)
    }

    // MARK: - Question selection

    mutating func nextQuestion() -> Question? {
        guard !people.isEmpty else { return nil }
        let scored = questions
            .filter { !asked.contains($0.id) && !askedAttributes.contains($0.attribute) }
            .map { (question: $0, gain: informationGain($0)) }
            .filter { $0.gain > 0.001 }
        guard !scored.isEmpty else { return nil }

        let bestGain = scored.map { $0.gain }.max() ?? 0
        let candidates = scored.filter { $0.gain >= bestGain - 0.01 }.map { $0.question }
        guard let selected = safePick(from: candidates) else { return nil }

        asked.insert(selected.id)
        askedAttributes.insert(selected.attribute)
        return selected
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
        for person in people {
            scores[person.id] = scores[person.id, default: 0] * likelihood(person.attributes[question.attribute], answer)
        }
        normalize()
    }

    mutating func reject(_ person: Person) {
        rejectedPersonIDs.insert(person.id)
        scores[person.id] = 0
        normalize()
    }

    mutating func restore(_ answers: [RecordedAnswer]) {
        for record in answers {
            guard let question = questions.first(where: { $0.id == record.questionID }) else { continue }
            asked.insert(question.id)
            askedAttributes.insert(question.attribute)
            apply(record.answer, to: question)
        }
    }

    // MARK: - Normalization

    private mutating func normalize() {
        for id in rejectedPersonIDs {
            scores[id] = 0
        }
        let activeIDs = scores.keys.filter { !rejectedPersonIDs.contains($0) }

        let total = scores.values.reduce(0, +)
        if total <= 0 {
            guard !activeIDs.isEmpty else { return }
            let share = 1.0 / Double(activeIDs.count)
            for id in scores.keys {
                scores[id] = rejectedPersonIDs.contains(id) ? 0 : share
            }
            return
        }

        for id in activeIDs {
            scores[id] = scores[id, default: 0] + smoothing
        }
        let smoothedTotal = scores.values.reduce(0, +)
        for id in scores.keys {
            let value = scores[id] ?? 0
            scores[id] = (value.isFinite && value >= 0) ? value / smoothedTotal : 0
        }
    }

    // MARK: - Information gain

    private func informationGain(_ question: Question) -> Double {
        let coverage = people.reduce(0.0) { partial, person in
            partial + (person.attributes[question.attribute] == nil ? 0 : scores[person.id, default: 0])
        }
        guard coverage >= 0.6 else { return 0 }

        let priorEntropy = entropy(scores.values)
        let expectedEntropy = Answer.allCases.filter { $0 != .unknown }.reduce(0.0) { total, answer in
            var weighted: [String: Double] = [:]
            for person in people {
                let answerWeight = likelihood(person.attributes[question.attribute], answer)
                weighted[person.id] = scores[person.id, default: 0] * answerWeight
            }
            let probability = weighted.values.reduce(0, +)
            guard probability > 0 else { return total }
            return total + probability * entropy(weighted.values.map { $0 / probability })
        }
        return max(0, priorEntropy - expectedEntropy) * coverage
    }

    private func likelihood(_ value: Double?, _ answer: Answer) -> Double {
        guard let value else { return 1.0 }
        let raw = max(0.05, 1.0 - abs(value - answer.evidence))
        let total = Answer.allCases
            .filter { $0 != .unknown }
            .reduce(0.0) { $0 + max(0.05, 1.0 - abs(value - $1.evidence)) }
        return total > 0 ? raw / total : 1.0
    }

    private func entropy<S: Sequence>(_ values: S) -> Double where S.Element == Double {
        values.reduce(0.0) { result, value in
            guard value > 0 else { return result }
            return result - value * log2(value)
        }
    }
}
